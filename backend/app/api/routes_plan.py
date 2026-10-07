"""API routes for PlanSpec generation, editing, versioning, and approval."""

from __future__ import annotations
import datetime
from typing import Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.api.deps import get_current_state, set_current_state
from app.domain.plan import PlanSpec, PlanValidationResult
from app.orchestrator.graph import run_planner_workflow, run_approval_workflow
from app.services.plan_validator import validate_plan

router = APIRouter(prefix="/plan", tags=["plan"])


class PlanGenerateRequest(BaseModel):
    requirement: str | None = None
    intention: str | None = None


class PlanEditRequest(BaseModel):
    plan: dict[str, Any] | None = None
    feedback: str | None = None


@router.post("")
async def generate_plan(req: PlanGenerateRequest) -> dict[str, Any]:
    """Triggers the Planner orchestrator workflow to generate a PlanSpec."""
    state = get_current_state()
    if not state.source_tables:
        raise HTTPException(
            status_code=400, 
            detail="No source tables available in state. Please ingest sources first."
        )

    if req.requirement:
        state.requirement = req.requirement
    if req.intention:
        state.intention = req.intention

    updated_state = await run_planner_workflow(state)
    set_current_state(updated_state)
    return updated_state.model_dump()


@router.post("/edit")
async def edit_plan(req: PlanEditRequest) -> dict[str, Any]:
    """Edits active plan directly or submits feedback for re-planning."""
    state = get_current_state()
    if not state.plan:
        raise HTTPException(status_code=400, detail="No active plan to edit.")

    # Option A: Feedback-driven re-planning
    if req.feedback and req.feedback.strip():
        state.log(f"Re-planning with user feedback: '{req.feedback}'...")
        updated_state = await run_planner_workflow(state, feedback=req.feedback)
        set_current_state(updated_state)
        return updated_state.model_dump()

    # Option B: Direct JSON modification
    if req.plan:
        try:
            new_plan = PlanSpec.model_validate(req.plan)
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"Invalid PlanSpec structure: {str(e)}")

        # Validate against source tables
        val_result: PlanValidationResult = validate_plan(new_plan, state.source_tables)
        if not val_result.valid:
            raise HTTPException(
                status_code=422, 
                detail=f"Plan validation failed: {'; '.join(val_result.errors)}"
            )

        # Snapshot old version into history
        new_version_num = state.plan_version + 1
        version_snapshot = {
            "version": new_version_num,
            "plan": new_plan.model_dump(),
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "source": "user_edit",
        }
        state.plan_versions.append(version_snapshot)

        # Update state
        state.plan = new_plan
        state.plan_version = new_version_num
        state.plan_status = "draft"
        state.fact_view_name = new_plan.fact_view_name
        # Mark downstream as stale
        state.fact_view_json = None
        state.graphical_view_json = None
        state.analytical_model_json = None
        
        state.log(f"Plan updated directly by user to v{new_version_num}. Downstream artifacts marked stale.")
        set_current_state(state)
        return state.model_dump()

    raise HTTPException(status_code=400, detail="Either 'plan' JSON or 'feedback' text must be provided.")


@router.post("/approve")
async def approve_plan() -> dict[str, Any]:
    """Approves the active PlanSpec and triggers Fact Agent stub."""
    state = get_current_state()
    if not state.plan:
        raise HTTPException(status_code=400, detail="No active plan to approve.")

    # Validate before approval
    val_result: PlanValidationResult = validate_plan(state.plan, state.source_tables)
    if not val_result.valid:
        raise HTTPException(
            status_code=422, 
            detail=f"Cannot approve invalid plan: {'; '.join(val_result.errors)}"
        )

    updated_state = await run_approval_workflow(state)
    set_current_state(updated_state)
    return updated_state.model_dump()


@router.get("/versions")
async def get_plan_versions() -> dict[str, Any]:
    """Returns historical versions of the plan."""
    state = get_current_state()
    return {
        "current_version": state.plan_version,
        "plan_status": state.plan_status,
        "versions": state.plan_versions,
    }
