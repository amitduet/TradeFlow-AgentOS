"""File-backed approval gate for deterministic workflow recommendations."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from app.agents.workflow_contracts import ApprovalRequest, ApprovalStatus, RecommendedAction


DEFAULT_APPROVAL_STORE_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "runtime" / "approval_requests.json"
)


def create_approval_request(
    *,
    sales_order_id: str,
    proposed_action: RecommendedAction,
    reason: str,
    risk_level: str,
    storage_path: str | Path = DEFAULT_APPROVAL_STORE_PATH,
) -> ApprovalRequest:
    """Create a pending approval request without mutating business data."""
    request = ApprovalRequest(
        approval_id=f"APR-{uuid4().hex[:12].upper()}",
        sales_order_id=sales_order_id,
        proposed_action=proposed_action,
        reason=reason,
        risk_level=risk_level,  # type: ignore[arg-type]
        status="pending",
        created_at=datetime.now(UTC),
    )
    requests = _load_requests(storage_path)
    requests.append(request)
    _write_requests(storage_path, requests)
    return request


def approve_request(
    approval_id: str,
    storage_path: str | Path = DEFAULT_APPROVAL_STORE_PATH,
) -> ApprovalRequest:
    """Mark an existing approval request as approved by explicit call."""
    return _update_request_status(approval_id, "approved", storage_path)


def reject_request(
    approval_id: str,
    storage_path: str | Path = DEFAULT_APPROVAL_STORE_PATH,
) -> ApprovalRequest:
    """Mark an existing approval request as rejected by explicit call."""
    return _update_request_status(approval_id, "rejected", storage_path)


def _update_request_status(
    approval_id: str,
    status: ApprovalStatus,
    storage_path: str | Path,
) -> ApprovalRequest:
    requests = _load_requests(storage_path)
    for index, request in enumerate(requests):
        if request.approval_id == approval_id:
            updated = request.model_copy(update={"status": status})
            requests[index] = updated
            _write_requests(storage_path, requests)
            return updated
    raise KeyError(f"Unknown approval_id: {approval_id}")


def _load_requests(storage_path: str | Path) -> list[ApprovalRequest]:
    path = Path(storage_path)
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [ApprovalRequest.model_validate(item) for item in payload]


def _write_requests(storage_path: str | Path, requests: list[ApprovalRequest]) -> None:
    path = Path(storage_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [request.model_dump(mode="json") for request in requests]
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
