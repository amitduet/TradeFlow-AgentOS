"""Real LLM planner provider adapter with strict output validation."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import socket
from typing import Any, Callable, Literal
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.agents.domain_skills import DomainSkill, match_skill_for_request, list_available_skills
from app.agents.planner_contracts import PlannerDecision, PlannerInput, PlannerSafetyOutcome
from app.agents.planner_safety import APPROVED_WORKFLOWS


LLMRecommendedAction = Literal[
    "continue",
    "review",
    "escalate",
    "create_purchase_order_draft",
    "require_approval",
    "refuse",
]
LLMRiskLevel = Literal["low", "medium", "high", "unknown"]
LLMApprovalState = Literal["pending", "requires_approval", "not_applicable", "refused", "escalated"]

SAFE_LLM_RECOMMENDED_ACTIONS = set(LLMRecommendedAction.__args__)
PROHIBITED_ACTION_TERMS = {
    "approve_order",
    "execute_purchase_order",
    "bypass_approval",
    "override_approval_gate",
    "modify_customer_credit",
    "modify_supplier_terms",
    "execute_payment",
    "update_real_inventory",
}
PROHIBITED_FREEFORM_CLAIMS = (
    "i approved",
    "i executed",
    "i submitted",
    "i updated inventory",
    "approval bypassed",
    "purchase order executed",
    "payment executed",
)
DEFAULT_LLM_TIMEOUT_SECONDS = 30.0
DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"
DEFAULT_GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"


class LLMPlannerOutput(BaseModel):
    """Strict schema accepted from a real planner LLM."""

    model_config = ConfigDict(extra="forbid")

    resolved_intent: str
    selected_route: str | None
    recommended_action: LLMRecommendedAction
    risk_level: LLMRiskLevel
    approval_state: LLMApprovalState
    safety_outcome: PlannerSafetyOutcome
    reason_codes: list[str] = Field(min_length=1)
    evidence_references: list[str]
    response_summary: str
    refusal_reason: str | None = None
    escalation_reason: str | None = None
    extracted_sales_order_id: str | None = None
    confidence: float = Field(default=0.85, ge=0, le=1)


class LLMProviderError(RuntimeError):
    """Base class for safe LLM provider failures."""

    def __init__(self, message: str, validation_errors: list[str] | None = None) -> None:
        super().__init__(message)
        self.validation_errors = validation_errors or [message]


class LLMProviderValidationError(LLMProviderError):
    """Raised when model output violates the strict planner contract."""


@dataclass(frozen=True)
class LLMProviderConfig:
    provider: str
    model: str
    api_key: str
    base_url: str | None = None
    timeout_seconds: float = DEFAULT_LLM_TIMEOUT_SECONDS

    @classmethod
    def from_env(cls) -> "LLMProviderConfig":
        provider = os.getenv("TRADEFLOW_LLM_PROVIDER", "openai").strip().lower()
        model = os.getenv("TRADEFLOW_LLM_MODEL", "").strip()
        api_key = os.getenv("TRADEFLOW_LLM_API_KEY", "").strip()
        base_url = os.getenv("TRADEFLOW_LLM_BASE_URL", "").strip() or None
        timeout_raw = os.getenv("TRADEFLOW_LLM_TIMEOUT_SECONDS", str(DEFAULT_LLM_TIMEOUT_SECONDS)).strip()
        try:
            timeout_seconds = float(timeout_raw)
        except ValueError as exc:
            raise LLMProviderError("TRADEFLOW_LLM_TIMEOUT_SECONDS must be a number.") from exc
        return cls(
            provider=provider,
            model=model,
            api_key=api_key,
            base_url=base_url,
            timeout_seconds=timeout_seconds,
        )

    def validate_for_live_call(self) -> None:
        if self.provider not in {"openai", "gemini", "custom"}:
            raise LLMProviderError(f"Unsupported TRADEFLOW_LLM_PROVIDER {self.provider!r}.")
        if not self.model:
            raise LLMProviderError("TRADEFLOW_LLM_MODEL is required when TRADEFLOW_PLANNER_PROVIDER=llm.")
        if not self.api_key:
            raise LLMProviderError("TRADEFLOW_LLM_API_KEY is required when TRADEFLOW_PLANNER_PROVIDER=llm.")
        if self.timeout_seconds <= 0:
            raise LLMProviderError("TRADEFLOW_LLM_TIMEOUT_SECONDS must be greater than zero.")


LLMResponseClient = Callable[[dict[str, Any], LLMProviderConfig], str]


class ConfiguredLLMPlannerProvider:
    """Planner provider that calls a configured LLM and returns a typed decision."""

    def __init__(
        self,
        config: LLMProviderConfig | None = None,
        response_client: LLMResponseClient | None = None,
    ) -> None:
        self.config = config or LLMProviderConfig.from_env()
        self._response_client = response_client or _call_configured_llm

    def decide(self, planner_input: PlannerInput) -> PlannerDecision:
        prompt = build_planner_prompt(planner_input)
        raw_response = self._response_client(prompt, self.config)
        output = parse_llm_planner_output(raw_response, prompt["allowed_evidence_references"])
        return PlannerDecision(
            intent=output.resolved_intent,
            selected_workflow=output.selected_route,
            extracted_sales_order_id=output.extracted_sales_order_id,
            confidence=output.confidence,
            requires_clarification=output.safety_outcome == "escalated",
            clarification_question=output.escalation_reason if output.safety_outcome == "escalated" else None,
            reason=output.refusal_reason or output.escalation_reason or output.response_summary,
            reason_codes=list(dict.fromkeys([*output.reason_codes, "llm_provider_validated"])),
        )


def build_planner_prompt(planner_input: PlannerInput) -> dict[str, Any]:
    """Build compact, deterministic context for the LLM planner."""
    skill = _matched_skill(planner_input.user_request)
    runbook_context = _runbook_context(skill)
    allowed_evidence_references = _allowed_evidence_references(skill, runbook_context)
    return {
        "task": "Return only strict JSON that conforms to the planner output schema.",
        "user_request": planner_input.user_request,
        "dataset_path": planner_input.dataset_path,
        "matched_skill": _skill_context(skill),
        "runbook_context": runbook_context,
        "allowed_routes": sorted(APPROVED_WORKFLOWS),
        "allowed_recommended_actions": sorted(SAFE_LLM_RECOMMENDED_ACTIONS),
        "disallowed_actions": sorted(PROHIBITED_ACTION_TERMS),
        "approval_gate_rule": (
            "The model may recommend review, escalation, draft preparation, or approval requirement, "
            "but it must never approve, execute, bypass, modify production data, or claim execution."
        ),
        "required_output_schema": {
            "resolved_intent": "string",
            "selected_route": "analyze_sales_order_risk or null",
            "recommended_action": sorted(SAFE_LLM_RECOMMENDED_ACTIONS),
            "risk_level": ["low", "medium", "high", "unknown"],
            "approval_state": ["pending", "requires_approval", "not_applicable", "refused", "escalated"],
            "safety_outcome": ["pass", "blocked", "escalated", "refused", "error"],
            "reason_codes": ["one or more concise snake_case reason codes"],
            "evidence_references": sorted(allowed_evidence_references),
            "response_summary": "string",
            "refusal_reason": "string or null",
            "escalation_reason": "string or null",
            "extracted_sales_order_id": "string or null",
            "confidence": "number from 0 to 1",
        },
        "allowed_evidence_references": sorted(allowed_evidence_references),
    }


def parse_llm_planner_output(
    raw_response: str,
    allowed_evidence_references: set[str] | list[str],
) -> LLMPlannerOutput:
    """Parse and validate model output before it can influence planner routing."""
    try:
        payload = _extract_json_object(raw_response)
    except ValueError as exc:
        raise LLMProviderValidationError("LLM response was not valid JSON.", [str(exc)]) from exc

    try:
        output = LLMPlannerOutput.model_validate(payload)
    except ValidationError as exc:
        errors = [f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}" for error in exc.errors()]
        raise LLMProviderValidationError("LLM response failed schema validation.", errors) from exc

    errors = _semantic_validation_errors(output, set(allowed_evidence_references))
    if errors:
        raise LLMProviderValidationError("LLM response violated planner safety constraints.", errors)
    return output


def _semantic_validation_errors(output: LLMPlannerOutput, allowed_evidence_references: set[str]) -> list[str]:
    errors: list[str] = []
    if output.selected_route is not None and output.selected_route not in APPROVED_WORKFLOWS:
        errors.append(f"selected_route {output.selected_route!r} is not approved.")

    for reference in output.evidence_references:
        if reference not in allowed_evidence_references:
            errors.append(f"evidence reference {reference!r} was not in prompt context.")

    text_fields = [
        output.resolved_intent,
        output.selected_route or "",
        output.response_summary,
        output.refusal_reason or "",
        output.escalation_reason or "",
        *output.reason_codes,
    ]
    lowered_text = "\n".join(text_fields).lower()
    for term in PROHIBITED_ACTION_TERMS:
        if term in lowered_text:
            errors.append(f"prohibited action term {term!r} appeared in LLM output.")
    for claim in PROHIBITED_FREEFORM_CLAIMS:
        if claim in lowered_text:
            errors.append(f"prohibited execution claim {claim!r} appeared in LLM output.")

    if output.recommended_action == "refuse" and output.safety_outcome != "refused":
        errors.append("recommended_action 'refuse' requires safety_outcome 'refused'.")
    if output.recommended_action == "escalate" and output.safety_outcome not in {"escalated", "blocked"}:
        errors.append("recommended_action 'escalate' requires escalated or blocked safety outcome.")
    if output.approval_state == "pending" and output.recommended_action not in {
        "continue",
        "review",
        "create_purchase_order_draft",
        "require_approval",
    }:
        errors.append("pending approval_state is inconsistent with the recommended_action.")
    return errors


def _extract_json_object(raw_response: str) -> dict[str, Any]:
    text = raw_response.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Malformed JSON: {exc.msg}") from exc
    if not isinstance(payload, dict):
        raise ValueError("Top-level LLM response must be a JSON object.")
    return payload


def _call_configured_llm(prompt: dict[str, Any], config: LLMProviderConfig) -> str:
    config.validate_for_live_call()
    if config.provider in {"openai", "custom"}:
        return _call_openai_compatible(prompt, config)
    if config.provider == "gemini":
        return _call_gemini(prompt, config)
    raise LLMProviderError(f"Unsupported LLM provider {config.provider!r}.")


def _call_openai_compatible(prompt: dict[str, Any], config: LLMProviderConfig) -> str:
    base_url = (config.base_url or DEFAULT_OPENAI_BASE_URL).rstrip("/")
    request = Request(
        url=f"{base_url}/chat/completions",
        data=json.dumps(
            {
                "model": config.model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a constrained TradeFlow planner. Return only strict JSON. "
                            "Never execute business actions or bypass approval gates."
                        ),
                    },
                    {"role": "user", "content": json.dumps(prompt, sort_keys=True)},
                ],
                "temperature": 0,
                "response_format": {"type": "json_object"},
            }
        ).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    payload = _post_json(request, config.timeout_seconds)
    try:
        return payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMProviderError("OpenAI-compatible response did not include message content.") from exc


def _call_gemini(prompt: dict[str, Any], config: LLMProviderConfig) -> str:
    base_url = (config.base_url or DEFAULT_GEMINI_BASE_URL).rstrip("/")
    request = Request(
        url=f"{base_url}/models/{config.model}:generateContent?key={config.api_key}",
        data=json.dumps(
            {
                "contents": [
                    {
                        "role": "user",
                        "parts": [
                            {
                                "text": (
                                    "Return only strict JSON for this constrained planner prompt:\n"
                                    + json.dumps(prompt, sort_keys=True)
                                )
                            }
                        ],
                    }
                ],
                "generationConfig": {"temperature": 0, "responseMimeType": "application/json"},
            }
        ).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    payload = _post_json(request, config.timeout_seconds)
    try:
        return payload["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMProviderError("Gemini response did not include generated text.") from exc


def _post_json(request: Request, timeout_seconds: float) -> dict[str, Any]:
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))
    except socket.timeout as exc:
        raise LLMProviderError("LLM provider request timed out.") from exc
    except HTTPError as exc:
        raise LLMProviderError(f"LLM provider HTTP error: {exc.code}.") from exc
    except URLError as exc:
        raise LLMProviderError(f"LLM provider request failed: {exc.reason}.") from exc
    except json.JSONDecodeError as exc:
        raise LLMProviderError("LLM provider returned non-JSON HTTP response.") from exc


def _matched_skill(user_request: str) -> DomainSkill | None:
    catalog = list_available_skills()
    result = match_skill_for_request(user_request, catalog)
    return catalog.get(result.matched_skill) if result.matched_skill else None


def _skill_context(skill: DomainSkill | None) -> dict[str, Any] | None:
    if skill is None:
        return None
    return {
        "name": skill.name,
        "description": skill.description,
        "version": skill.version,
        "allowed_actions": skill.allowed_actions,
        "disallowed_actions": skill.disallowed_actions,
    }


def _runbook_context(skill: DomainSkill | None) -> list[dict[str, str]]:
    if skill is None:
        return []
    snippets: list[dict[str, str]] = []
    for runbook_reference in skill.related_runbooks[:3]:
        path = (skill.path.parent / runbook_reference).resolve()
        if not path.is_file():
            continue
        snippets.append(
            {
                "reference": f"runbook:{Path(runbook_reference).name}",
                "path": str(path.relative_to(Path(__file__).resolve().parents[2])),
                "snippet": path.read_text(encoding="utf-8")[:1400],
            }
        )
    return snippets


def _allowed_evidence_references(
    skill: DomainSkill | None,
    runbook_context: list[dict[str, str]],
) -> set[str]:
    references = {"user_request", "allowed_actions", "approval_constraints", "output_schema"}
    if skill is not None:
        references.add(f"skill:{skill.name}")
    references.update(item["reference"] for item in runbook_context)
    return references
