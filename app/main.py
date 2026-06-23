"""Minimal CLI-friendly entry point for Sprint 1."""

from app.orchestrator.order_orchestrator import route_user_question


def run_demo(question: str) -> dict:
    """Route a user question through the placeholder orchestrator."""
    return route_user_question(question).model_dump()


if __name__ == "__main__":
    demo_question = "Can we fulfill 25 Demo Widget A units for Demo Retail Alpha this week?"
    print(run_demo(demo_question))
