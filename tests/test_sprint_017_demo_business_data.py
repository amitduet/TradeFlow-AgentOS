import json
from pathlib import Path

from app.agents.demo_agent import load_demo_input, run_tradeflow_agent_demo
from app.agents.demo_data import DEFAULT_DEMO_DATA_DIR, load_demo_business_data


EXAMPLES_DIR = Path("examples/demo")
DEMO_DATA_FILES = [
    "demo_products.json",
    "demo_customers.json",
    "demo_inventory.json",
    "demo_finance_opening_balance.json",
]


def test_demo_business_data_files_exist() -> None:
    for filename in DEMO_DATA_FILES:
        assert (DEFAULT_DEMO_DATA_DIR / filename).exists()


def test_demo_business_data_counts_and_finance_balance() -> None:
    data = load_demo_business_data()

    assert len(data["products"]) == 10
    assert len(data["customers"]) == 10
    assert data["finance_opening_balance"]["currency"] == "USD"
    assert data["finance_opening_balance"]["opening_cash_balance"] == 100000


def test_inventory_product_codes_exist_in_demo_products() -> None:
    data = load_demo_business_data()
    product_codes = {product["product_code"] for product in data["products"]}

    assert product_codes
    assert all(record["product_code"] in product_codes for record in data["inventory"])


def test_demo_order_examples_reference_valid_demo_products_and_customers() -> None:
    data = load_demo_business_data()
    product_codes = {product["product_code"] for product in data["products"]}
    customer_ids = {customer["customer_id"] for customer in data["customers"]}

    for path in sorted(EXAMPLES_DIR.glob("*_risk_order.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        context = payload["business_context"]

        assert context["product_code"] in product_codes
        assert context["customer_id"] in customer_ids


def test_demo_business_context_is_included_in_deterministic_response(tmp_path: Path) -> None:
    scenario = load_demo_input(EXAMPLES_DIR / "low_risk_order.json")
    response = run_tradeflow_agent_demo(
        scenario,
        approval_storage_path=tmp_path / "approval_requests.json",
        audit_log_path=tmp_path / "planner_audit.jsonl",
    )

    assert response.success is True
    assert response.risk_level == "low"
    assert response.demo_business_context["product"]["product_code"] == "PRD-SODA-ASH-DENSE"
    assert response.demo_business_context["customer"]["customer_id"] == "CUST-001"
    assert response.demo_business_context["inventory"]["available_quantity"] == 220


def test_low_stock_inventory_is_surfaced_as_demo_context_signal(tmp_path: Path) -> None:
    scenario = load_demo_input(EXAMPLES_DIR / "medium_risk_order.json")
    response = run_tradeflow_agent_demo(
        scenario,
        approval_storage_path=tmp_path / "approval_requests.json",
        audit_log_path=tmp_path / "planner_audit.jsonl",
    )

    assert response.success is True
    assert response.risk_level == "medium"
    assert response.demo_business_context["inventory"]["inventory_status"] == "low_stock"
    assert "inventory_status:low_stock" in response.demo_business_context["demo_context_signals"]
    assert "available_inventory_at_or_below_reorder_level" in response.demo_business_context["demo_context_signals"]


def test_low_medium_high_risk_scenarios_still_pass(tmp_path: Path) -> None:
    cases = {
        "low_risk_order.json": "low",
        "medium_risk_order.json": "medium",
        "high_risk_order.json": "high",
    }

    for filename, expected_risk in cases.items():
        scenario = load_demo_input(EXAMPLES_DIR / filename)
        response = run_tradeflow_agent_demo(
            scenario,
            approval_storage_path=tmp_path / f"{scenario.case_id}_approvals.json",
            audit_log_path=tmp_path / f"{scenario.case_id}_audit.jsonl",
        )

        assert response.success is True
        assert response.risk_level == expected_risk
        assert response.demo_business_context["product"]
        assert response.demo_business_context["customer"]
