"""Orchestrator nodes for LangGraph workflow execution."""

from __future__ import annotations
import datetime
from typing import Any
from app.agents.fact_agent import FactAgentStub
from app.agents.planner import PlannerAgent
from app.domain.plan import PlanSpec, PlanValidationResult
from app.domain.source import SourceTable
from app.domain.state import SharedState
from app.observability.events import event_bus
from app.observability.logger import logger
from app.services.plan_validator import validate_plan

planner_agent = PlannerAgent()
fact_agent_stub = FactAgentStub()


async def check_inputs_node(state: dict[str, Any]) -> dict[str, Any]:
    """Validates that source tables and synthetic data are present."""
    logger.info("[Orchestrator] Checking input state...")
    event_bus.publish("orchestrator_step", {"step": "check_inputs", "status": "running"})
    
    source_tables = state.get("source_tables", [])
    if not source_tables:
        err = "No source tables provided to orchestrator."
        logger.error(f"[Orchestrator] {err}")
        return {
            **state,
            "errors": state.get("errors", []) + [err],
            "logs": state.get("logs", []) + [f"Error: {err}"],
        }

    return {
        **state,
        "logs": state.get("logs", []) + [f"Input verified with {len(source_tables)} source table(s)."]
    }


async def planner_node(state: dict[str, Any]) -> dict[str, Any]:
    """Executes Planner agent to produce PlanSpec with retry support."""
    requirement = state.get("requirement")
    intention = state.get("intention")
    raw_tables = state.get("source_tables", [])
    
    # Ensure source_tables are SourceTable instances
    source_tables: list[SourceTable] = []
    for t in raw_tables:
        if isinstance(t, SourceTable):
            source_tables.append(t)
        elif isinstance(t, dict):
            source_tables.append(SourceTable.model_validate(t))

    dummy_data = state.get("dummy_data", {})
    feedback = state.get("feedback")
    validation_error = state.get("validation_error")
    retry_count = state.get("retry_count", 0)

    logger.info(f"[Orchestrator] Running Planner (Attempt {retry_count + 1})...")

    try:
        plan: PlanSpec = await planner_agent.generate_plan(
            requirement=requirement,
            intention=intention,
            source_tables=source_tables,
            dummy_data=dummy_data,
            validation_error=validation_error,
            feedback=feedback,
            retry_count=retry_count,
        )

        # Run validation
        val_result: PlanValidationResult = validate_plan(plan, source_tables)
        
        if not val_result.valid:
            logger.warning(f"[Orchestrator] Plan validation failed: {val_result.errors}")
            if retry_count < 2:
                logger.info(f"[Orchestrator] Triggering retry {retry_count + 1}/2...")
                return {
                    **state,
                    "plan": plan.model_dump(),
                    "validation_error": "; ".join(val_result.errors),
                    "retry_count": retry_count + 1,
                    "plan_status": "draft",
                    "logs": state.get("logs", []) + [f"Validation failure: {val_result.errors}. Retrying..."],
                }
            else:
                # Retries exhausted
                err_msg = f"Plan validation failed after 2 retries: {val_result.errors}"
                return {
                    **state,
                    "plan": plan.model_dump(),
                    "errors": state.get("errors", []) + [err_msg],
                    "plan_status": "draft",
                    "logs": state.get("logs", []) + [f"Validation error: {err_msg}"],
                }

        # Plan is valid
        current_version = state.get("plan_version", 0) + 1
        versions = list(state.get("plan_versions", []))
        
        version_snapshot = {
            "version": current_version,
            "plan": plan.model_dump(),
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "source": "feedback" if feedback else "planner",
        }
        versions.append(version_snapshot)

        return {
            **state,
            "plan": plan.model_dump(),
            "plan_version": current_version,
            "plan_versions": versions,
            "plan_status": "draft",
            "fact_view_name": plan.fact_view_name,
            "validation_error": None,
            "stage": "plan",
            "logs": state.get("logs", []) + [f"Generated valid Plan v{current_version} for '{plan.fact_view_name}'."],
        }
    except Exception as e:
        err_msg = f"Planner failed: {str(e)}"
        logger.error(f"[Orchestrator] {err_msg}", exc_info=True)
        return {
            **state,
            "errors": state.get("errors", []) + [err_msg],
            "logs": state.get("logs", []) + [f"Error: {err_msg}"],
        }


async def fact_agent_stub_node(state: dict[str, Any]) -> dict[str, Any]:
    """Calls Fact Agent stub upon plan approval."""
    fact_view_name = state.get("fact_view_name") or "FV_DEFAULT"
    logger.info(f"[Orchestrator] Plan approved. Calling Fact Agent Stub for '{fact_view_name}'...")
    
    stub_res = await fact_agent_stub.execute_stub(fact_view_name)
    
    return {
        **state,
        "plan_status": "approved",
        "stage": "fact_view",
        "logs": state.get("logs", []) + [f"Plan approved. {stub_res.get('message')}"],
    }
