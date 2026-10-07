"""Centralized SharedState domain model for Phase 2 pipeline."""

from __future__ import annotations
from typing import Any
from pydantic import BaseModel, Field

from app.domain.source import SourceTable
from app.domain.plan import PlanSpec, PlanVersion


class SharedState(BaseModel):
    """Central state communication layer across all pipeline phases."""
    
    # Input Intent & Requirements
    intention: str | None = Field(default=None, description="User intention or modeling goal")
    requirement: str | None = Field(default=None, description="Detailed business requirement")
    
    # Source Tables & Synthetic Data (strictly synthetic, never real rows)
    source_tables: list[SourceTable] = Field(default_factory=list, description="Parsed SourceTable objects")
    dummy_data: dict[str, list[dict[str, Any]]] = Field(
        default_factory=dict, 
        description="20 deterministic synthetic rows per source table"
    )
    
    # Plan & Versioning (Phase 2)
    plan: PlanSpec | None = Field(default=None, description="Active PlanSpec")
    plan_version: int = Field(default=0, description="Current plan version number")
    plan_versions: list[dict[str, Any]] = Field(default_factory=list, description="Historical snapshots of PlanSpec versions")
    plan_status: str = Field(default="draft", description="Plan status: draft, approved, stale")
    fact_view_name: str | None = Field(default=None, description="Active target Fact View name")
    
    # Pipeline Stage
    stage: str = Field(default="source", description="Pipeline stage: source, plan, fact_view, graphical_view, analytical_model")
    
    # Downstream artifacts (empty in Phase 2 - Fact View not implemented yet)
    fact_view_json: dict[str, Any] | None = Field(default=None, description="Future Fact View JSON artifact")
    graphical_view_json: dict[str, Any] | None = Field(default=None, description="Future Graphical View JSON artifact")
    analytical_model_json: dict[str, Any] | None = Field(default=None, description="Future Analytical Model JSON artifact")
    
    # Execution mode & Observability
    llm_mode: str = Field(default="MOCK", description="LLM execution mode: MOCK or REAL")
    errors: list[str] = Field(default_factory=list, description="Captured validation or processing errors")
    logs: list[str] = Field(default_factory=list, description="Human readable execution trace logs")

    def log(self, message: str) -> None:
        """Appends a trace log message."""
        self.logs.append(message)

    def add_error(self, error: str) -> None:
        """Appends an error message."""
        self.errors.append(error)
