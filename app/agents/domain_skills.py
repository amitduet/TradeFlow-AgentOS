"""Deterministic helpers for Sprint 006 domain skill metadata and trigger evals."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SKILLS_ROOT = REPO_ROOT / "skills"
REQUIRED_METADATA_FIELDS = {
    "name",
    "description",
    "version",
    "owner",
    "allowed_actions",
    "disallowed_actions",
}
SALES_ORDER_PATTERN = re.compile(r"\bSO-\d+\b", re.IGNORECASE)


@dataclass(frozen=True)
class DomainSkill:
    name: str
    description: str
    version: str
    owner: str
    allowed_actions: list[str]
    disallowed_actions: list[str]
    related_runbooks: list[str]
    trigger_phrases: list[str]
    non_trigger_phrases: list[str]
    path: Path


@dataclass(frozen=True)
class SkillCatalog:
    skills: list[DomainSkill]

    def get(self, name: str) -> DomainSkill:
        for skill in self.skills:
            if skill.name == name:
                return skill
        raise KeyError(f"Unknown skill: {name}")

    @property
    def names(self) -> list[str]:
        return [skill.name for skill in self.skills]


@dataclass(frozen=True)
class SkillTriggerCase:
    case_id: str
    user_request: str
    expected_skill: str | None
    focus_skill: str | None = None


@dataclass(frozen=True)
class SkillEvaluationResult:
    case_id: str
    user_request: str
    expected_skill: str | None
    matched_skill: str | None
    passed: bool
    score_by_skill: dict[str, int]


def load_skill_metadata(skill_md_path: str | Path) -> DomainSkill:
    """Load and validate one SKILL.md file."""
    path = Path(skill_md_path)
    frontmatter = _parse_frontmatter(path.read_text(encoding="utf-8"))
    missing = sorted(field for field in REQUIRED_METADATA_FIELDS if field not in frontmatter)
    if missing:
        raise ValueError(f"{path} is missing required metadata fields: {missing}")

    return DomainSkill(
        name=_as_str(frontmatter["name"], "name", path),
        description=_as_str(frontmatter["description"], "description", path),
        version=_as_str(frontmatter["version"], "version", path),
        owner=_as_str(frontmatter["owner"], "owner", path),
        allowed_actions=_as_list(frontmatter["allowed_actions"], "allowed_actions", path),
        disallowed_actions=_as_list(frontmatter["disallowed_actions"], "disallowed_actions", path),
        related_runbooks=_as_list(frontmatter.get("related_runbooks", []), "related_runbooks", path),
        trigger_phrases=_as_list(frontmatter.get("trigger_phrases", []), "trigger_phrases", path),
        non_trigger_phrases=_as_list(frontmatter.get("non_trigger_phrases", []), "non_trigger_phrases", path),
        path=path,
    )


def list_available_skills(skills_root: str | Path = DEFAULT_SKILLS_ROOT) -> SkillCatalog:
    """Load all skill folders under the skills root."""
    root = Path(skills_root)
    skill_paths = sorted(path for path in root.glob("*/SKILL.md") if path.is_file())
    return SkillCatalog(skills=[load_skill_metadata(path) for path in skill_paths])


def match_skill_for_request(
    user_request: str,
    catalog: SkillCatalog | None = None,
) -> SkillEvaluationResult:
    """Return the best deterministic skill match for a user request."""
    resolved_catalog = catalog or list_available_skills()
    scores = {skill.name: _score_skill(user_request, skill) for skill in resolved_catalog.skills}
    matched_skill = _best_match(scores)
    return SkillEvaluationResult(
        case_id="ad_hoc",
        user_request=user_request,
        expected_skill=None,
        matched_skill=matched_skill,
        passed=True,
        score_by_skill=scores,
    )


def evaluate_trigger_case(
    trigger_case: SkillTriggerCase,
    catalog: SkillCatalog | None = None,
) -> SkillEvaluationResult:
    """Evaluate one versioned trigger case."""
    resolved_catalog = catalog or list_available_skills()
    scores = {skill.name: _score_skill(trigger_case.user_request, skill) for skill in resolved_catalog.skills}
    matched_skill = _best_match(scores)
    if trigger_case.expected_skill is None:
        if trigger_case.focus_skill is not None:
            passed = matched_skill != trigger_case.focus_skill
        else:
            passed = matched_skill is None
    else:
        passed = matched_skill == trigger_case.expected_skill
    return SkillEvaluationResult(
        case_id=trigger_case.case_id,
        user_request=trigger_case.user_request,
        expected_skill=trigger_case.expected_skill,
        matched_skill=matched_skill,
        passed=passed,
        score_by_skill=scores,
    )


def load_trigger_cases(cases_path: str | Path) -> list[SkillTriggerCase]:
    """Load trigger cases from the Sprint 006 JSON dataset."""
    import json

    payload = json.loads(Path(cases_path).read_text(encoding="utf-8"))
    return [
        SkillTriggerCase(
            case_id=case["case_id"],
            user_request=case["user_request"],
            expected_skill=case.get("expected_skill"),
            focus_skill=case.get("focus_skill"),
        )
        for case in payload["cases"]
    ]


def _score_skill(user_request: str, skill: DomainSkill) -> int:
    lowered = user_request.lower()
    score = 0
    for phrase in skill.trigger_phrases:
        if phrase.lower() in lowered:
            score += 10
    for phrase in skill.non_trigger_phrases:
        if phrase.lower() in lowered:
            score -= 20

    score += _business_signal_score(lowered, skill.name)
    return score


def _business_signal_score(lowered_request: str, skill_name: str) -> int:
    has_order_id = SALES_ORDER_PATTERN.search(lowered_request) is not None
    if skill_name == "approval-gate-handling":
        if any(term in lowered_request for term in ("bypass", "skip approval", "without approval", "auto approve")):
            return 40
        if "approval" in lowered_request or "approve" in lowered_request:
            return 15
    if skill_name == "purchase-order-recommendation":
        if "approval" in lowered_request or "approve" in lowered_request:
            return -8
        if "purchase order" in lowered_request or re.search(r"\bpo\b", lowered_request):
            return 14
    if skill_name == "order-risk-analysis":
        if has_order_id and any(term in lowered_request for term in ("analyze", "risk", "safe", "proceed")):
            return 12
        if "customer order" in lowered_request and "risk" in lowered_request:
            return 10
    return 0


def _best_match(scores: dict[str, int]) -> str | None:
    positive_scores = [(name, score) for name, score in scores.items() if score > 0]
    if not positive_scores:
        return None
    positive_scores.sort(key=lambda item: (-item[1], item[0]))
    if len(positive_scores) > 1 and positive_scores[0][1] == positive_scores[1][1]:
        return None
    return positive_scores[0][0]


def _parse_frontmatter(text: str) -> dict[str, str | list[str]]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("SKILL.md must start with YAML frontmatter")

    metadata: dict[str, str | list[str]] = {}
    current_list_key: str | None = None
    for line in lines[1:]:
        stripped = line.strip()
        if stripped == "---":
            return metadata
        if not stripped:
            continue
        if stripped.startswith("- "):
            if current_list_key is None:
                raise ValueError(f"List item without a key: {line}")
            value = stripped[2:].strip()
            existing = metadata.setdefault(current_list_key, [])
            if not isinstance(existing, list):
                raise ValueError(f"Metadata field {current_list_key} mixes scalar and list values")
            existing.append(value)
            continue
        if ":" not in line:
            raise ValueError(f"Invalid frontmatter line: {line}")
        key, raw_value = line.split(":", 1)
        key = key.strip()
        value = raw_value.strip()
        if value:
            metadata[key] = value.strip('"').strip("'")
            current_list_key = None
        else:
            metadata[key] = []
            current_list_key = key
    raise ValueError("SKILL.md frontmatter is not closed")


def _as_str(value: str | list[str], field_name: str, path: Path) -> str:
    if isinstance(value, str) and value:
        return value
    raise ValueError(f"{path} metadata field {field_name} must be a non-empty string")


def _as_list(value: str | list[str], field_name: str, path: Path) -> list[str]:
    if isinstance(value, list) and all(isinstance(item, str) and item for item in value):
        return value
    raise ValueError(f"{path} metadata field {field_name} must be a non-empty list")
