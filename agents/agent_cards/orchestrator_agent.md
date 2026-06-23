# Orchestrator Agent Card

- Mission: Route user questions into the correct synthetic TradeFlow workflow.
- Inputs: User question, optional order context, synthetic event history.
- Tools: Workflow classifier, event router.
- Outputs: Workflow route, selected agents, next action summary.
- Guardrails: No transaction posting, no production API calls, no Finance override.
- Human approval: Required before any real-world action triggered by routed workflow.
