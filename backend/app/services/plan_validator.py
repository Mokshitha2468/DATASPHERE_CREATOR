"""Plan validation service for Phase 2 Planner specifications."""

from __future__ import annotations
from typing import Sequence
from app.domain.plan import PlanSpec, PlanValidationResult
from app.domain.source import SourceTable

ALLOWED_OPERATORS = {
    "=", "!=", "<>", ">", ">=", "<", "<=", 
    "BETWEEN", "IN", "NOT IN", "LIKE", "NOT LIKE", 
    "IS NULL", "IS NOT NULL"
}


def validate_plan(plan: PlanSpec, source_tables: Sequence[SourceTable]) -> PlanValidationResult:
    """Validates a PlanSpec against available SourceTable metadata.
    
    Checks:
    1. Source table exists.
    2. Fact View name is valid.
    3. Every selected column exists in source table.
    4. Every dropped column exists in source table.
    5. Every source column is either selected or dropped (partition check).
    6. No column is missing from decision.
    7. No column appears in both selected and dropped.
    8. Every filter column exists.
    9. Every filter operator is allowed.
    10. Warns (non-fatal) if a primary key column is dropped.
    """
    errors: list[str] = []
    warnings: list[str] = []

    # 1. Check Fact View Name
    if not plan.fact_view_name or not plan.fact_view_name.strip():
        errors.append("Fact view name cannot be empty.")

    # 2. Check Source Table
    table_map = {t.name: t for t in source_tables}
    table = table_map.get(plan.source_table)
    if not table:
        # Check case-insensitive
        for t in source_tables:
            if t.name.lower() == plan.source_table.lower():
                table = t
                break

    if not table:
        errors.append(f"Source table '{plan.source_table}' not found in ingested sources: {list(table_map.keys())}")
        return PlanValidationResult(valid=False, errors=errors, warnings=warnings)

    source_cols = set(table.get_columns())
    selected_names = [c.name for c in plan.selected_columns]
    dropped_names = [c.name for c in plan.dropped_columns]

    selected_set = set(selected_names)
    dropped_set = set(dropped_names)

    # 3. Check selected columns exist
    invalid_selected = selected_set - source_cols
    if invalid_selected:
        errors.append(f"Selected column(s) do not exist in '{table.name}': {sorted(invalid_selected)}")

    # 4. Check dropped columns exist
    invalid_dropped = dropped_set - source_cols
    if invalid_dropped:
        errors.append(f"Dropped column(s) do not exist in '{table.name}': {sorted(invalid_dropped)}")

    # 5 & 6. Check complete partition (every column decided)
    all_decided = selected_set | dropped_set
    missing_cols = source_cols - all_decided
    if missing_cols:
        errors.append(f"Missing column decision for columns in '{table.name}': {sorted(missing_cols)}. Every column must be either selected or dropped.")

    # 7. Check overlap
    overlap = selected_set & dropped_set
    if overlap:
        errors.append(f"Column(s) cannot be both selected and dropped: {sorted(overlap)}")

    # 8 & 9. Check filters
    for f in plan.filters:
        if f.column not in source_cols:
            errors.append(f"Filter column '{f.column}' does not exist in table '{table.name}'.")
        
        op_norm = f.operator.upper().strip()
        if op_norm not in ALLOWED_OPERATORS:
            errors.append(f"Invalid filter operator '{f.operator}' on column '{f.column}'. Allowed operators: {sorted(ALLOWED_OPERATORS)}")

    # 10. Key drop warning (warning only, not fatal)
    key_cols = set(table.get_key_columns())
    dropped_keys = key_cols & dropped_set
    if dropped_keys:
        warnings.append(f"Primary key column(s) dropped: {sorted(dropped_keys)}. This may affect downstream entity granularity.")

    is_valid = len(errors) == 0
    return PlanValidationResult(valid=is_valid, errors=errors, warnings=warnings)
