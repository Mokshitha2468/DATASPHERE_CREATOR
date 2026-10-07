"""Unit tests for Phase 2 SharedState model."""

from app.domain.plan import ColumnDecision, PlanSpec
from app.domain.source import SourceField, SourceTable
from app.domain.state import SharedState


def test_shared_state_defaults():
    state = SharedState()
    assert state.requirement is None
    assert state.intention is None
    assert state.source_tables == []
    assert state.dummy_data == {}
    assert state.plan is None
    assert state.plan_version == 0
    assert state.plan_versions == []
    assert state.plan_status == "draft"
    assert state.stage == "source"
    assert state.fact_view_json is None
    assert state.llm_mode in ("MOCK", "REAL")
    assert state.errors == []
    assert state.logs == []


def test_shared_state_pydantic_serialization():
    table = SourceTable(
        name="TEST_ENTITY",
        label="Test Entity Label",
        fields=[
            SourceField(name="ID", data_type="cds.String", is_key=True),
            SourceField(name="VAL", data_type="cds.Decimal", precision=10, scale=2),
        ]
    )
    plan = PlanSpec(
        fact_view_name="FV_TEST",
        source_table="TEST_ENTITY",
        selected_columns=[ColumnDecision(name="ID", reason="Key"), ColumnDecision(name="VAL", reason="Measure")],
        dropped_columns=[],
        filters=[],
        unsupported=[],
        summary="Test summary"
    )
    
    state = SharedState(
        intention="Revenue Fact View",
        requirement="Build revenue fact model",
        source_tables=[table],
        dummy_data={"TEST_ENTITY": [{"ID": "K1", "VAL": 12.34}]},
        plan=plan,
        plan_version=1,
        plan_status="draft",
        errors=["Minor warning"],
        logs=["Step 1 complete"]
    )

    json_str = state.model_dump_json()
    reconstructed = SharedState.model_validate_json(json_str)

    assert reconstructed.intention == "Revenue Fact View"
    assert reconstructed.plan is not None
    assert reconstructed.plan.fact_view_name == "FV_TEST"
    assert reconstructed.plan_version == 1
    assert len(reconstructed.source_tables) == 1
