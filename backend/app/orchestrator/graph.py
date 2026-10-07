"""LangGraph StateGraph workflow orchestrator."""

from __future__ import annotations
from typing import Any, Literal
from langgraph.graph import StateGraph, END
from app.domain.state import SharedState
from app.orchestrator.nodes import check_inputs_node, planner_node, fact_agent_stub_node


def should_retry_planner(state: dict[str, Any]) -> Literal["planner", "__end__"]:
    """Conditional routing: retry planner if validation error and retries remaining."""
    if state.get("validation_error") and state.get("retry_count", 0) <= 2:
        return "planner"
    return "__end__"


def create_planner_graph():
    """Creates the LangGraph workflow for Plan generation."""
    builder = StateGraph(dict)
    
    builder.add_node("check_inputs", check_inputs_node)
    builder.add_node("planner", planner_node)
    
    builder.set_entry_point("check_inputs")
    builder.add_edge("check_inputs", "planner")
    
    builder.add_conditional_edges(
        "planner",
        should_retry_planner,
        {
            "planner": "planner",
            "__end__": END,
        }
    )
    
    return builder.compile()


planner_graph = create_planner_graph()


async def run_planner_workflow(
    shared_state: SharedState,
    feedback: str | None = None
) -> SharedState:
    """Executes the planner LangGraph workflow and updates the SharedState."""
    state_dict = shared_state.model_dump()
    state_dict["feedback"] = feedback
    state_dict["retry_count"] = 0
    state_dict["validation_error"] = None
    
    # Run graph
    result = await planner_graph.ainvoke(state_dict)
    return SharedState.model_validate(result)


async def run_approval_workflow(shared_state: SharedState) -> SharedState:
    """Executes plan approval workflow invoking Fact Agent stub."""
    state_dict = shared_state.model_dump()
    result = await fact_agent_stub_node(state_dict)
    return SharedState.model_validate(result)
