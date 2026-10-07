"""Unit tests for PlanValidator service."""

from app.domain.plan import ColumnDecision, FilterSpec, PlanSpec
from app.domain.source import SourceField, SourceTable
from app.services.plan_validator import validate_plan


def get_test_table() -> SourceTable:
    return SourceTable(
        name="SALES",
        fields=[
            SourceField(name="ORDER_ID", data_type="cds.String", is_key=True),
            SourceField(name="CUSTOMER", data_type="cds.String"),
            SourceField(name="AMOUNT", data_type="cds.Decimal", precision=10, scale=2),
            SourceField(name="STATUS", data_type="cds.String"),
        ]
    )


def test_valid_plan():
    table = get_test_table()
    plan = PlanSpec(
        fact_view_name="FV_SALES",
        source_table="SALES",
        selected_columns=[
            ColumnDecision(name="ORDER_ID", reason="Key"),
            ColumnDecision(name="CUSTOMER", reason="Dimension"),
            ColumnDecision(name="AMOUNT", reason="Measure"),
        ],
        dropped_columns=[
            ColumnDecision(name="STATUS", reason="Not needed"),
        ],
        filters=[
            FilterSpec(column="AMOUNT", operator=">", values=[100], reason="High value only")
        ],
        unsupported=[],
        summary="Valid plan"
    )

    res = validate_plan(plan, [table])
    assert res.valid is True
    assert len(res.errors) == 0


def test_invalid_column_error():
    table = get_test_table()
    plan = PlanSpec(
        fact_view_name="FV_SALES",
        source_table="SALES",
        selected_columns=[
            ColumnDecision(name="NON_EXISTING_COL", reason="Invalid"),
            ColumnDecision(name="ORDER_ID", reason="Key"),
        ],
        dropped_columns=[
            ColumnDecision(name="CUSTOMER", reason="Drop"),
            ColumnDecision(name="AMOUNT", reason="Drop"),
            ColumnDecision(name="STATUS", reason="Drop"),
        ],
        filters=[],
        unsupported=[],
        summary="Invalid column test"
    )

    res = validate_plan(plan, [table])
    assert res.valid is False
    assert any("NON_EXISTING_COL" in e for e in res.errors)


def test_missing_column_decision_error():
    table = get_test_table()
    # Missing decision for 'STATUS'
    plan = PlanSpec(
        fact_view_name="FV_SALES",
        source_table="SALES",
        selected_columns=[
            ColumnDecision(name="ORDER_ID", reason="Key"),
            ColumnDecision(name="AMOUNT", reason="Measure"),
        ],
        dropped_columns=[
            ColumnDecision(name="CUSTOMER", reason="Drop"),
        ],
        filters=[],
        unsupported=[],
        summary="Missing status column"
    )

    res = validate_plan(plan, [table])
    assert res.valid is False
    assert any("Missing column decision" in e for e in res.errors)


def test_invalid_filter_operator_error():
    table = get_test_table()
    plan = PlanSpec(
        fact_view_name="FV_SALES",
        source_table="SALES",
        selected_columns=[
            ColumnDecision(name="ORDER_ID", reason="Key"),
            ColumnDecision(name="CUSTOMER", reason="Dim"),
            ColumnDecision(name="AMOUNT", reason="Measure"),
            ColumnDecision(name="STATUS", reason="Dim"),
        ],
        dropped_columns=[],
        filters=[
            FilterSpec(column="STATUS", operator="INVALID_CUSTOM_OP", values=["X"], reason="Test")
        ],
        unsupported=[],
        summary="Invalid filter operator test"
    )

    res = validate_plan(plan, [table])
    assert res.valid is False
    assert any("Invalid filter operator" in e for e in res.errors)


def test_dropped_key_warning():
    table = get_test_table()
    # Key 'ORDER_ID' is dropped
    plan = PlanSpec(
        fact_view_name="FV_SALES",
        source_table="SALES",
        selected_columns=[
            ColumnDecision(name="CUSTOMER", reason="Dim"),
            ColumnDecision(name="AMOUNT", reason="Measure"),
            ColumnDecision(name="STATUS", reason="Dim"),
        ],
        dropped_columns=[
            ColumnDecision(name="ORDER_ID", reason="Drop key"),
        ],
        filters=[],
        unsupported=[],
        summary="Dropped key warning test"
    )

    res = validate_plan(plan, [table])
    # Should be valid (warnings don't fail validation)
    assert res.valid is True
    assert len(res.warnings) >= 1
    assert any("Primary key column" in w for w in res.warnings)
