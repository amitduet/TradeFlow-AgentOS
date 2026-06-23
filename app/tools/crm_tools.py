"""CRM tool placeholders."""

from app.data.db import SYNTHETIC_CUSTOMERS


def get_customer_profile(customer_id: str) -> dict:
    customer = SYNTHETIC_CUSTOMERS.get(customer_id)
    if customer is None:
        return {"customer_id": customer_id, "status": "unknown", "synthetic": True}
    return {"customer_id": customer_id, **customer, "synthetic": True}


def summarize_payment_behavior(customer_id: str) -> dict:
    risk_by_customer = {
        "cust_demo_001": "low",
        "cust_demo_002": "medium",
        "cust_demo_003": "high",
    }
    return {
        "customer_id": customer_id,
        "payment_behavior_risk": risk_by_customer.get(customer_id, "needs_human_review"),
        "synthetic": True,
    }
