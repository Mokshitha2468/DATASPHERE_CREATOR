"""Plan domain models for Phase 2 Planner specifications and versions."""

from __future__ import annotations
from typing import Any
from pydantic import BaseModel, Field


class ColumnDecision(BaseModel):
    """Decision details for keeping or dropping a source column."""
    name: str = Field(description="Column technical name")
    reason: str = Field(description="Human readable explanation for why this column is kept or dropped")


class FilterSpec(BaseModel):
    """Specification of an explicit filter applied on a source column."""
    column: str = Field(description="Column technical name to filter on")
    operator: str = Field(description="Filter operator e.g. =, !=, IN, NOT IN, >, >=, <, <=, BETWEEN, LIKE, IS NULL, IS NOT NULL")
    values: list[Any] = Field(default_factory=list, description="Filter operand values")
    reason: str = Field(description="Explanation for why this filter is applied")


class PlanSpec(BaseModel):
    """Structured modeling plan specification produced by Planner."""
    fact_view_name: str = Field(description="Target technical name of the Fact View e.g. FV_SALES_ORDER")
    source_table: str = Field(description="Source table/entity name being modeled")
    selected_columns: list[ColumnDecision] = Field(default_factory=list, description="Columns to project/keep")
    dropped_columns: list[ColumnDecision] = Field(default_factory=list, description="Columns to exclude/drop")
    filters: list[FilterSpec] = Field(default_factory=list, description="Filters to apply")
    unsupported: list[str] = Field(default_factory=list, description="Unsupported requirements (e.g. joins, unions, custom script)")
    summary: str = Field(description="Plain English summary of the plan logic")


class PlanVersion(BaseModel):
    """Historical version snapshot of a plan."""
    version: int = Field(description="Version number (e.g. 1, 2, 3)")
    plan: PlanSpec = Field(description="PlanSpec snapshot")
    created_at: str = Field(description="ISO timestamp of creation")
    source: str = Field(default="planner", description="Origin: planner, user_edit, feedback")


class PlanValidationResult(BaseModel):
    """Result of plan structural and semantic validation."""
    valid: bool = Field(description="Whether the plan is valid")
    errors: list[str] = Field(default_factory=list, description="Validation errors preventing approval")
    warnings: list[str] = Field(default_factory=list, description="Non-fatal warnings (e.g. dropped primary key)")
