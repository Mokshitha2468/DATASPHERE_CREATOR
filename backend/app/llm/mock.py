"""Offline Mock Planner generating realistic, valid PlanSpec structures."""

from __future__ import annotations
import re
from typing import Sequence
from app.domain.plan import ColumnDecision, FilterSpec, PlanSpec
from app.domain.source import InferredClassification, SourceTable


def generate_mock_plan(
    requirement: str | None,
    intention: str | None,
    source_tables: Sequence[SourceTable],
    feedback: str | None = None,
    should_fail: bool = False
) -> PlanSpec:
    """Generates a realistic PlanSpec based on source tables, intention, and requirements.
    
    Args:
        requirement: Business requirement text.
        intention: User intention.
        source_tables: Ingested source tables.
        feedback: Optional user feedback for re-planning.
        should_fail: If True, produces an intentionally invalid plan to test retry loops.
    """
    if not source_tables:
        return PlanSpec(
            fact_view_name="FV_EMPTY",
            source_table="NONE",
            selected_columns=[],
            dropped_columns=[],
            filters=[],
            unsupported=["No source tables available"],
            summary="Cannot generate plan without source tables."
        )

    # Pick the most suitable primary fact table (e.g. table with measures or matching keywords)
    table = source_tables[0]
    for t in source_tables:
        t_name = t.name.lower()
        req_str = f"{requirement or ''} {intention or ''}".lower()
        if t_name in req_str or (t.label and t.label.lower() in req_str):
            table = t
            break
        # Prefer tables that contain numeric measures as primary Fact View candidates
        if len(t.get_measures()) > len(table.get_measures()):
            table = t

    # Determine Fact View Name (e.g. FV_SALES_ORDERS_REVENUE)
    clean_name = re.sub(r"[^A-Za-z0-9_]", "", table.name).upper()
    if not clean_name.startswith("FV_"):
        fact_view_name = f"FV_{clean_name}"
    else:
        fact_view_name = clean_name

    intent_lower = (intention or "").lower()
    req_lower = (requirement or "").lower()
    feedback_lower = (feedback or "").lower()
    combined_intent = f"{intent_lower} {req_lower} {feedback_lower}"

    if "revenue" in combined_intent:
        fact_view_name = f"{fact_view_name}_REVENUE"
    elif "sales" in combined_intent:
        fact_view_name = f"{fact_view_name}_SALES"

    # Handle intentional test failure mode
    if should_fail:
        return PlanSpec(
            fact_view_name=fact_view_name,
            source_table=table.name,
            selected_columns=[ColumnDecision(name="NON_EXISTENT_COL_XYZ", reason="Invalid test column")],
            dropped_columns=[],
            filters=[FilterSpec(column="INVALID_COL", operator="INVALID_OP", values=["X"], reason="Test filter")],
            unsupported=[],
            summary="Intentionally invalid plan for retry testing."
        )

    selected: list[ColumnDecision] = []
    dropped: list[ColumnDecision] = []
    filters: list[FilterSpec] = []
    unsupported: list[str] = []

    # Technical noise keywords to exclude from clean analytical models
    tech_patterns = (
        "CREATED_BY", "CHANGED_BY", "DUMMY", "TEMP", "FLAG", "SYS_", "_SYS",
        "CDC", "OPERATION", "SEQUENCE", "HASH", "PAYLOAD", "ROW_ID", "TIMESTAMP", "DELETED"
    )

    for field in table.fields:
        col_name = field.name
        norm_name = col_name.upper()

        # Check explicit user feedback first
        if "drop" in feedback_lower and col_name.lower() in feedback_lower:
            dropped.append(ColumnDecision(name=col_name, reason="Dropped per user feedback."))
            continue
        if "keep" in feedback_lower and col_name.lower() in feedback_lower:
            selected.append(ColumnDecision(name=col_name, reason="Kept per user feedback."))
            continue

        # Retain Keys
        if field.is_key:
            selected.append(ColumnDecision(name=col_name, reason="Retained primary entity key for granularity."))
        # Retain Measures
        elif field.inferred_classification == InferredClassification.MEASURE_CANDIDATE:
            selected.append(ColumnDecision(name=col_name, reason="Selected numeric measure candidate for aggregation."))
        # Retain Core Analytical Dimensions
        elif any(dim_word in norm_name for dim_word in ("DATE", "STATUS", "CATEGORY", "COUNTRY", "CITY", "TYPE", "CUSTOMER", "PRODUCT", "REGION", "CODE", "YEAR", "MONTH")):
            selected.append(ColumnDecision(name=col_name, reason="Retained core analytical dimension."))
        # Drop BLOBs / binary
        elif field.inferred_classification == InferredClassification.BINARY_OR_BLOB:
            dropped.append(ColumnDecision(name=col_name, reason="Excluded binary/blob payload from analytical fact view."))
        # Drop technical/CDC noise fields
        elif any(tp in norm_name for tp in tech_patterns):
            dropped.append(ColumnDecision(name=col_name, reason="Excluded technical/CDC operational column from reporting model."))
        else:
            # Default to keep business columns
            selected.append(ColumnDecision(name=col_name, reason="Included for dimensional context."))

    # Generate filters based on user intention/requirements
    for field in table.fields:
        col_u = field.name.upper()
        if "STATUS" in col_u:
            if "cancel" in combined_intent or "exclude" in combined_intent:
                filters.append(FilterSpec(
                    column=field.name,
                    operator="!=",
                    values=["CANCELLED"],
                    reason="Exclude cancelled records per user intention."
                ))
            elif "active" in combined_intent or "completed" in combined_intent or "open" in combined_intent:
                target_val = "COMPLETED" if "completed" in combined_intent else "ACTIVE"
                filters.append(FilterSpec(
                    column=field.name,
                    operator="=",
                    values=[target_val],
                    reason=f"Filter for {target_val.lower()} records per requirement."
                ))

        if "COUNTRY" in col_u and "usa" in combined_intent:
            filters.append(FilterSpec(
                column=field.name,
                operator="=",
                values=["US"],
                reason="Filter for US region per intention."
            ))

    # Multi-table explanation in Phase 2
    if len(source_tables) > 1:
        other_tables = [t.name for t in source_tables if t.name != table.name]
        unsupported.append(
            f"Multi-table Join with [{', '.join(other_tables)}] will be synthesized in Phase 3 Graphical Views."
        )

    summary = (
        f"Fact View '{fact_view_name}' modeled on primary source '{table.name}'. "
        f"Selected {len(selected)} columns ({len(table.get_measures())} measures) and pruned {len(dropped)} technical/unneeded columns."
    )
    if filters:
        summary += f" Applied {len(filters)} filter constraint(s)."

    return PlanSpec(
        fact_view_name=fact_view_name,
        source_table=table.name,
        selected_columns=selected,
        dropped_columns=dropped,
        filters=filters,
        unsupported=unsupported,
        summary=summary
    )
