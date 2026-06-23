"""A2A-style event schemas for synthetic agent handoffs."""

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class AgentEvent(BaseModel):
    event_id: str
    event_type: str
    source_agent: str
    target_agent: str
    correlation_id: str
    payload: dict[str, Any] = Field(default_factory=dict)
    requires_human_approval: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
