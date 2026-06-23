"""Synthetic seed accessors."""

from app.data.db import SYNTHETIC_CUSTOMERS, SYNTHETIC_INVENTORY


def load_seed_data() -> dict:
    """Return the Sprint 1 in-memory synthetic seed data."""
    return {
        "customers": SYNTHETIC_CUSTOMERS,
        "inventory": SYNTHETIC_INVENTORY,
    }
