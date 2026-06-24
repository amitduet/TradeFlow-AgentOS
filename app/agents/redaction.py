"""Helpers for redacting local provider secrets from logs and reports."""

from __future__ import annotations

import os
import re
from typing import Any


REDACTION = "[REDACTED]"
SECRET_ENV_NAMES = (
    "TRADEFLOW_LLM_API_KEY",
)
SENSITIVE_KEY_TERMS = ("api_key", "apikey", "authorization", "bearer", "token", "secret")
SECRET_PATTERNS = (
    re.compile(r"Bearer\s+[A-Za-z0-9._~+/=-]+", re.IGNORECASE),
    re.compile(r"(key=)[A-Za-z0-9._~+/=-]+", re.IGNORECASE),
    re.compile(r"(api[_-]?key['\"]?\s*[:=]\s*['\"]?)[^,'\"\s}]+", re.IGNORECASE),
)


def collect_configured_secrets(extra_values: list[str] | None = None) -> list[str]:
    """Return non-empty local secret values that should never be emitted."""
    values = [os.getenv(name, "") for name in SECRET_ENV_NAMES]
    values.extend(extra_values or [])
    return sorted({value for value in values if value}, key=len, reverse=True)


def redact_text(value: str | None, secrets: list[str] | None = None) -> str | None:
    """Redact known secret values and common credential patterns from text."""
    if value is None:
        return None
    redacted = value
    for secret in collect_configured_secrets(secrets):
        redacted = redacted.replace(secret, REDACTION)
    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub(_redact_match, redacted)
    return redacted


def redact_data(value: Any, secrets: list[str] | None = None) -> Any:
    """Recursively redact secrets from JSON-serializable data."""
    if isinstance(value, str):
        return redact_text(value, secrets)
    if isinstance(value, list):
        return [redact_data(item, secrets) for item in value]
    if isinstance(value, tuple):
        return tuple(redact_data(item, secrets) for item in value)
    if isinstance(value, dict):
        redacted: dict[Any, Any] = {}
        for key, item in value.items():
            if _sensitive_key(str(key)):
                redacted[key] = REDACTION if item else item
            else:
                redacted[key] = redact_data(item, secrets)
        return redacted
    return value


def _redact_match(match: re.Match[str]) -> str:
    if match.lastindex:
        return match.group(1) + REDACTION
    text = match.group(0)
    if text.lower().startswith("bearer "):
        return "Bearer " + REDACTION
    return REDACTION


def _sensitive_key(key: str) -> bool:
    normalized = key.replace("-", "_").lower()
    return any(term in normalized for term in SENSITIVE_KEY_TERMS)
