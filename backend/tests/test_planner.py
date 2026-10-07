"""Unit tests for PlannerAgent, retry loop, and safety."""

import asyncio
from app.agents.planner import PlannerAgent
from app.domain.source import SourceField, SourceTable
from app.llm.mock import generate_mock_plan


def test_planner_agent_mock_output():
    table = SourceTable(
        name="ORDERS",
        fields=[
            SourceField(name="ORDER_ID", data_type="cds.String", is_key=True),
            SourceField(name="NET_AMOUNT", data_type="cds.Decimal", precision=10, scale=2),
            SourceField(name="ORDER_STATUS", data_type="cds.String"),
        ]
    )
    dummy_data = {
        "ORDERS": [
            {"ORDER_ID": "KEY_1001", "NET_AMOUNT": 100.0, "ORDER_STATUS": "ACTIVE"}
        ]
    }

    planner = PlannerAgent()
    plan = asyncio.run(planner.generate_plan(
        requirement="Calculate net revenue and exclude cancelled",
        intention="Revenue Fact View",
        source_tables=[table],
        dummy_data=dummy_data,
    ))

    assert plan.fact_view_name.startswith("FV_")
    assert plan.source_table == "ORDERS"
    assert len(plan.selected_columns) >= 2
    # Ensure all columns decided
    decided_cols = {c.name for c in plan.selected_columns} | {c.name for c in plan.dropped_columns}
    assert decided_cols == {"ORDER_ID", "NET_AMOUNT", "ORDER_STATUS"}


def test_mock_plan_failure_mode_for_retry():
    table = SourceTable(name="T1", fields=[SourceField(name="C1")])
    fail_plan = generate_mock_plan(
        requirement="Test",
        intention="Test",
        source_tables=[table],
        should_fail=True
    )
    assert fail_plan.selected_columns[0].name == "NON_EXISTENT_COL_XYZ"
