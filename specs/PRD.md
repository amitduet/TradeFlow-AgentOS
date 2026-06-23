# Product Requirements Document

## Problem Statement

Trading teams need a fast, auditable way to evaluate whether a customer order can be accepted, fulfilled from stock, procured from suppliers, financed safely, delivered, invoiced, and followed up for receivables. Today these checks often span sales notes, CRM records, inventory files, finance judgment, purchase options, and logistics updates.

## Users

- Sales managers evaluating customer requests.
- Finance managers reviewing margin, credit exposure, and payment risk.
- Inventory planners checking stock availability and reservation risk.
- Purchase coordinators preparing supplier and PO recommendations.
- Logistics coordinators tracking inbound and outbound movement.
- Portfolio reviewers assessing agentic workflow design.

## Scope

- Synthetic customer order feasibility workflow.
- Synthetic CRM, inventory, finance, supplier, logistics, and invoice draft data.
- Agent contracts for Orchestrator, Sales, CRM, Inventory, Finance, Purchase, and Logistics.
- A2A-style event contracts between agents.
- Draft-only purchase order and invoice workflows.
- Human approval checkpoints for real-world actions.
- Basic tests for schema, finance decision, and order workflow rules.

## Non-Scope

- Full ERP implementation.
- Production Odoo integration.
- Real customer data.
- Real TAM data or private business details.
- Real purchase order creation, stock posting, invoicing, or customer email sending.
- Autonomous financial, procurement, logistics, or customer-facing commitments.
- Real LLM calls in Sprint 1.

## MVP Features

- Classify a user order question into a workflow.
- Represent order, event, and finance decision schemas with Pydantic.
- Define placeholder tools for each business function.
- Define source-of-truth specs, agent cards, guardrails, and evaluation plan.
- Enforce that invoice drafts cannot be created before delivery confirmation.

## Success Criteria

- Public repository files explain the business problem, architecture, and guardrails.
- All seven agents have clear responsibilities, allowed tools, prohibited actions, inputs, and outputs.
- Event contracts include JSON examples.
- Synthetic data model covers the core trading workflow tables.
- Initial golden cases cover stock fulfillment, procurement, credit rejection, goods receipt, and invoice follow-up.
- Tests pass locally with `pytest`.

## Timeline

- Sprint 1: Foundation specs, contracts, minimal schemas, placeholder tools, and tests.
- Sprint 2: Implement first deterministic order feasibility workflow using synthetic seed data.
- Sprint 3: Add richer workflow state, approval gates, and expanded evaluation cases.
- Sprint 4: Polish demo interface, portfolio narrative, and Kaggle submission materials.
