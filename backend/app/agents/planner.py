"""Planner Agent generating PlanSpec from requirements, metadata, and synthetic dummy data."""

from __future__ import annotations
import json
from typing import Any, Sequence
from app.agents.base import BaseAgent
from app.domain.plan import PlanSpec
from app.domain.source import SourceTable
from app.llm.client import get_llm, get_llm_mode
from app.llm.mock import generate_mock_plan
from app.observability.logger import logger


class PlannerAgent(BaseAgent):
    """Generates structured modeling PlanSpec specifications."""

    def __init__(self):
        super().__init__(name="Planner")

    async def generate_plan(
        self,
        requirement: str | None,
        intention: str | None,
        source_tables: Sequence[SourceTable],
        dummy_data: dict[str, list[dict[str, Any]]],
        validation_error: str | None = None,
        feedback: str | None = None,
        retry_count: int = 0,
    ) -> PlanSpec:
        """Runs the planner logic with safe inputs only."""
        safe_input = {
            "requirement": requirement,
            "intention": intention,
            "tables": [t.name for t in source_tables],
            "retry_count": retry_count,
            "validation_error": validation_error,
            "feedback": feedback,
            # Synthetic data row count only
            "dummy_data_counts": {k: len(v) for k, v in dummy_data.items()},
        }

        step_name = f"GeneratePlan (Attempt {retry_count + 1})" if retry_count > 0 else "GeneratePlan"

        async def _execute_plan() -> PlanSpec:
            mode = get_llm_mode()
            if mode == "MOCK":
                return generate_mock_plan(
                    requirement=requirement,
                    intention=intention,
                    source_tables=source_tables,
                    feedback=feedback or validation_error,
                )

            llm = get_llm()
            if not llm:
                return generate_mock_plan(
                    requirement=requirement,
                    intention=intention,
                    source_tables=source_tables,
                    feedback=feedback or validation_error,
                )

            # Real LLM call with structured prompt
            prompt = self._build_prompt(
                requirement=requirement,
                intention=intention,
                source_tables=source_tables,
                dummy_data=dummy_data,
                validation_error=validation_error,
                feedback=feedback,
            )

            try:
                response = await llm.ainvoke(prompt)
                content = response.content if hasattr(response, "content") else str(response)
                # Parse JSON from response
                json_str = self._extract_json(content)
                parsed = json.loads(json_str)
                return PlanSpec.model_validate(parsed)
            except Exception as e:
                logger.warning(f"Real LLM plan parsing failed ({e}). Falling back to deterministic Mock planner.")
                return generate_mock_plan(
                    requirement=requirement,
                    intention=intention,
                    source_tables=source_tables,
                    feedback=feedback or validation_error,
                )

        return await self.execute(step_name, _execute_plan, safe_input)

    def _build_prompt(
        self,
        requirement: str | None,
        intention: str | None,
        source_tables: Sequence[SourceTable],
        dummy_data: dict[str, list[dict[str, Any]]],
        validation_error: str | None,
        feedback: str | None,
    ) -> str:
        tables_summary = [t.to_llm_summary() for t in source_tables]
        prompt = (
            f"You are the SAP Datasphere Modeling Planner.\n"
            f"User Intention: {intention or 'Create Fact View'}\n"
            f"Business Requirement: {requirement or 'Standard Analytical Fact Model'}\n\n"
            f"Available Source Tables Metadata:\n{json.dumps(tables_summary, indent=2)}\n\n"
            f"Synthetic Data Samples (First 3 synthetic rows only):\n"
            f"{json.dumps({k: v[:3] for k, v in dummy_data.items()}, indent=2)}\n\n"
        )
        if validation_error:
            prompt += f"PREVIOUS VALIDATION ERROR (Fix these issues):\n{validation_error}\n\n"
        if feedback:
            prompt += f"USER FEEDBACK TO INCORPORATE:\n{feedback}\n\n"

        prompt += "Return strict JSON conforming to PlanSpec schema with fact_view_name, source_table, selected_columns, dropped_columns, filters, unsupported, summary."
        return prompt

    def _extract_json(self, text: str) -> str:
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            return "\n".join(lines).strip()
        return text
