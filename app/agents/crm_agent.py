"""CRM Agent placeholder."""

from app.tools.crm_tools import get_customer_profile, summarize_payment_behavior


def review_customer(customer_id: str) -> dict:
    return {
        "profile": get_customer_profile(customer_id),
        "payment_behavior": summarize_payment_behavior(customer_id),
    }
