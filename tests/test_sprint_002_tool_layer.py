import json
import subprocess
import sys
from pathlib import Path

from app.schemas.tradeflow_dataset import TradeFlowDataset
from app.tools.tradeflow_tools import (
    calculate_order_margin,
    detect_order_risk,
    get_customer_profile,
    get_drop_shipping_chain,
    get_supplier_profile,
    list_logistics_events,
    load_synthetic_dataset,
)
from scripts.generate_synthetic_data import generate_synthetic_dataset, write_dataset


DATASET_PATH = Path("data/synthetic/tradeflow_seed.json")


def test_synthetic_generation_is_deterministic_for_same_seed() -> None:
    first = generate_synthetic_dataset(seed=1234).model_dump(mode="json")
    second = generate_synthetic_dataset(seed=1234).model_dump(mode="json")

    assert first == second


def test_generated_dataset_passes_referential_integrity_validation() -> None:
    dataset = load_synthetic_dataset(DATASET_PATH)

    assert isinstance(dataset, TradeFlowDataset)
    assert len(dataset.customers) >= 12
    assert len(dataset.suppliers) >= 8
    assert len(dataset.products) >= 25
    assert len(dataset.sales_orders) >= 20
    assert len(dataset.purchase_order_drafts) >= 12
    assert len(dataset.logistics_events) >= 30
    assert len(dataset.invoice_summaries) >= 15
    assert len(dataset.payment_summaries) >= 15


def test_customer_contact_person_fields_exist() -> None:
    customer = get_customer_profile("CUST-001")

    assert customer["rating"] == 5
    assert customer["billing_address"]
    assert customer["shipping_address"]
    assert customer["phone_number"]
    assert customer["contact_person"]["name"]
    assert customer["contact_person"]["email"]
    assert customer["contact_person"]["phone"]
    assert customer["contact_person"]["designation"]


def test_supplier_contact_person_fields_exist() -> None:
    supplier = get_supplier_profile("SUP-002")

    assert supplier["country"] == "Vietnam"
    assert supplier["phone_number"]
    assert supplier["contact_person"]["name"]
    assert supplier["contact_person"]["email"]
    assert supplier["contact_person"]["phone"]
    assert supplier["contact_person"]["designation"]


def test_purchase_order_drafts_can_link_to_sales_orders() -> None:
    dataset = load_synthetic_dataset(DATASET_PATH)

    linked_drafts = [draft for draft in dataset.purchase_order_drafts if draft.related_sales_order_id]

    assert linked_drafts
    assert any(draft.related_sales_order_id == "SO-1002" for draft in linked_drafts)
    assert all(draft.created_from_sales_order for draft in linked_drafts)


def test_logistics_events_link_to_sales_orders() -> None:
    events = list_logistics_events("SO-1002")

    assert len(events) == 3
    assert {event["related_sales_order_id"] for event in events} == {"SO-1002"}


def test_get_drop_shipping_chain_returns_order_customer_pos_suppliers_and_events() -> None:
    chain = get_drop_shipping_chain("SO-1002")

    assert chain["sales_order"]["id"] == "SO-1002"
    assert chain["customer"]["id"] == "CUST-002"
    assert chain["purchase_order_drafts"][0]["related_sales_order_id"] == "SO-1002"
    assert chain["suppliers"][0]["id"] == "SUP-002"
    assert chain["logistics_events"]


def test_calculate_order_margin_returns_stable_expected_values() -> None:
    margin = calculate_order_margin("SO-1001")

    assert margin == {
        "order_id": "SO-1001",
        "revenue": 2880.0,
        "estimated_cost": 1920.0,
        "gross_margin": 960.0,
        "gross_margin_percent": 33.33,
    }


def test_detect_order_risk_returns_known_flags() -> None:
    assert detect_order_risk("SO-1003")["risk_flags"] == ["low_customer_rating"]
    assert detect_order_risk("SO-1005")["risk_flags"] == ["missing_linked_po_for_drop_shipping"]
    assert detect_order_risk("SO-1006")["risk_flags"] == ["delayed_logistics_event"]


def test_eval_runner_passes() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/run_tool_evals.py"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "10/10 passed" in result.stdout


def test_generator_writes_pretty_json_to_requested_output(tmp_path: Path) -> None:
    output = tmp_path / "nested" / "tradeflow_seed.json"

    write_dataset(generate_synthetic_dataset(seed=999), output)
    parsed = json.loads(output.read_text(encoding="utf-8"))

    assert parsed["customers"][0]["id"] == "CUST-001"
    assert output.read_text(encoding="utf-8").startswith("{\n  ")
