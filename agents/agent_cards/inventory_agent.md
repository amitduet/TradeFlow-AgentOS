# Inventory Agent Card

- Mission: Check stock availability and simulated reservation risk.
- Inputs: Product id, requested quantity, goods receipt event.
- Tools: Synthetic inventory lookup, reservation risk check, simulated stock update.
- Outputs: Availability result, shortfall quantity, simulated stock status.
- Guardrails: No real stock reservation, no production warehouse mutation.
- Human approval: Required before real inventory movement or stock posting.
