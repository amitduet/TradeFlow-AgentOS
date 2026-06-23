"""Placeholder order orchestrator for Sprint 1."""

from pydantic import BaseModel, Field


class WorkflowRoute(BaseModel):
    workflow: str
    started_by: str = "orchestrator"
    next_agents: list[str] = Field(default_factory=list)
    rationale: str
    draft_only: bool = True


def route_user_question(question: str) -> WorkflowRoute:
    """Classify a user question into a simple synthetic workflow route."""
    normalized = question.lower()
    lifecycle_terms = {"delivered", "delivery", "goods receipt", "received", "inbound"}
    procurement_terms = {"procure", "procurement", "supplier", "shortfall", "purchase"}

    if any(term in normalized for term in lifecycle_terms):
        return WorkflowRoute(
            workflow="order_lifecycle",
            next_agents=["logistics", "sales", "inventory", "finance"],
            rationale="Question references lifecycle activity such as receipt or delivery.",
        )

    agents = ["sales", "crm", "inventory", "finance"]
    if any(term in normalized for term in procurement_terms):
        agents.append("purchase")

    return WorkflowRoute(
        workflow="order_feasibility",
        next_agents=agents,
        rationale="Question appears to ask whether a customer order can be accepted or fulfilled.",
    )
