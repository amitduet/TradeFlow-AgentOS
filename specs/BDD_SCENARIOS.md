# BDD Scenarios

```gherkin
Feature: TradeFlow AgentOS order lifecycle

  Scenario: Customer order can be fulfilled from stock
    Given a synthetic customer with acceptable credit exposure
    And the requested product has enough available inventory
    When the Sales Agent starts an order feasibility workflow
    Then the Inventory Agent reports stock is available
    And the Finance Agent returns approved or approved_with_conditions
    And no purchase order draft is required

  Scenario: Customer order requires procurement
    Given a synthetic customer requests more units than available stock
    And at least one approved synthetic supplier option exists
    When the Sales Agent starts an order feasibility workflow
    Then the Inventory Agent reports procurement is needed
    And the Purchase Agent prepares a supplier recommendation
    And a purchase order draft is created only after finance consent

  Scenario: Finance rejects order due to credit exposure
    Given a synthetic customer exceeds the configured credit exposure threshold
    When the Finance Agent reviews the order
    Then the Finance Agent returns rejected
    And the Purchase Agent must not create a purchase order draft
    And the Sales Agent must not create a customer commitment

  Scenario: Logistics confirms goods receipt and notifies inventory and sales
    Given a purchase order draft has been approved by a human
    And an inbound shipment is marked received in the synthetic workflow
    When the Logistics Agent confirms goods receipt
    Then the Logistics Agent emits a goods_received event
    And the Inventory Agent updates simulated stock status
    And the Sales Agent is notified that fulfillment can continue

  Scenario: Delivery confirmation triggers invoice draft and finance receivable follow-up
    Given a synthetic customer order has been fulfilled
    And Logistics has confirmed customer delivery
    When the Sales Agent prepares post-delivery actions
    Then the Sales Agent creates an invoice draft
    And the Sales Agent creates a customer email draft
    And the Finance Agent starts receivable follow-up tracking
```
