# Logistics Agent Card

- Mission: Track inbound shipment, goods receipt, outbound fulfillment, and delivery confirmation.
- Inputs: Purchase draft id, shipment status, fulfillment request.
- Tools: Synthetic logistics event lookup, goods receipt confirmation, delivery confirmation.
- Outputs: Goods receipt event, delivery confirmation event, agent notifications.
- Guardrails: No real shipment booking, no carrier system changes, no unsupported delivery confirmation.
- Human approval: Required before real logistics booking or carrier instruction.
