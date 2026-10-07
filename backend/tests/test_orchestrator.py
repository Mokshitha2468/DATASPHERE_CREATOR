"""Unit tests for LangGraph Orchestrator workflow, editing, and approval."""

import pytest
from app.domain.plan import ColumnDecision, PlanSpec
from app.domain.source import SourceField, SourceTable
from app.domain.state import SharedState
from app.orchestrator.graph import run_planner_workflow, run_approval_workflow


def test_orchestrator_planner_workflow():
    import asyncio
    table = SourceTable(
        name="SALES_FACT",
        fields=[
            SourceField(name="ID", data_type="cds.String", is_key=True),
            SourceField(name="REVENUE", data_type="cds.Decimal", precision=12, scale=2),
            SourceField(name="REGION", data_type="cds.String"),
        ]
    )
    state = SharedState(
        requirement="Model regional revenue",
        intention="Build Fact View",
        source_tables=[table],
        dummy_data={"SALES_FACT": [{"ID": "1", "REVENUE": 500.0, "REGION": "EMEA"}]}
    )

    updated = asyncio.run(run_planner_workflow(state))
    assert updated.plan is not None
    assert updated.plan_version == 1
    assert len(updated.plan_versions) == 1
    assert updated.plan_status == "draft"
    assert updated.stage == "plan"


def test_orchestrator_feedback_increases_version():
    import asyncio
    table = SourceTable(
        name="SALES_FACT",
        fields=[
            SourceField(name="ID", data_type="cds.String", is_key=True),
            SourceField(name="REVENUE", data_type="cds.Decimal", precision=12, scale=2),
            SourceField(name="REGION", data_type="cds.String"),
        ]
    )
    state = SharedState(
        requirement="Model regional revenue",
        source_tables=[table],
        dummy_data={"SALES_FACT": []}
    )

    # Initial plan v1
    v1_state = asyncio.run(run_planner_workflow(state))
    assert v1_state.plan_version == 1

    # Feedback re-plan v2
    v2_state = asyncio.run(run_planner_workflow(v1_state, feedback="Drop REGION column"))
    assert v2_state.plan_version == 2
    assert len(v2_state.plan_versions) == 2
    assert v2_state.plan_status == "draft"


def test_orchestrator_approval_calls_fact_agent_stub():
    import asyncio
    table = SourceTable(
        name="SALES_FACT",
        fields=[SourceField(name="ID", data_type="cds.String", is_key=True)]
    )
    plan = PlanSpec(
        fact_view_name="FV_SALES_FACT",
        source_table="SALES_FACT",
        selected_columns=[ColumnDecision(name="ID", reason="Key")],
        dropped_columns=[],
        filters=[],
        unsupported=[],
        summary="Plan approved"
    )
    state = SharedState(
        source_tables=[table],
        plan=plan,
        plan_version=1,
        plan_status="draft",
        fact_view_name="FV_SALES_FACT"
    )

    approved_state = asyncio.run(run_approval_workflow(state))
    assert approved_state.plan_status == "approved"
    assert approved_state.stage == "fact_view"
    assert any("Fact View generation" in log for log in approved_state.logs)
