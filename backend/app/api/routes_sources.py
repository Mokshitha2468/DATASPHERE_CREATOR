"""API routes for source metadata ingestion and optional sample pattern learning."""

from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app.api.deps import get_current_state, set_current_state
from app.core.config import settings
from app.domain.source import SourceTable
from app.domain.state import SharedState
from app.observability.logger import logger
from app.services.dummy_data import generate_dummy_data
from app.services.sample_rows import parse_and_learn_patterns
from app.services.source_parser import DatasphereParser

router = APIRouter(prefix="", tags=["sources"])


@router.get("/samples")
async def list_samples() -> dict[str, Any]:
    """Lists pre-bundled sample Datasphere files for one-click testing."""
    samples = []
    sample_dir = settings.SAMPLE_DIR
    if sample_dir.exists():
        for file in sample_dir.glob("*.json"):
            samples.append({
                "id": file.stem,
                "filename": file.name,
                "label": file.stem.replace("_", " ").title(),
            })
    return {"samples": samples}


@router.get("/samples/{sample_id}")
async def load_sample(sample_id: str) -> dict[str, Any]:
    """Loads a specific sample Datasphere JSON content."""
    sample_dir = settings.SAMPLE_DIR
    target = sample_dir / f"{sample_id}.json"
    if not target.exists():
        raise HTTPException(status_code=404, detail=f"Sample '{sample_id}' not found.")
    try:
        content = json.loads(target.read_text(encoding="utf-8"))
        return {"filename": target.name, "content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read sample: {str(e)}")


@router.post("/sources")
async def ingest_sources(
    files: list[UploadFile] = File(default=[]),
    sample_files: list[UploadFile] = File(default=[]),
    raw_json: str | None = Form(default=None),
    intention: str | None = Form(default=None),
    requirement: str | None = Form(default=None),
    rows: int = Form(default=20),
) -> dict[str, Any]:
    """Ingests source metadata JSONs, optionally learns from sample rows, and generates synthetic data.
    
    PRIVACY GUARANTEE: Real sample data is NEVER stored in SharedState or logs.
    """
    state = get_current_state()
    state.intention = intention or state.intention
    state.requirement = requirement or state.requirement
    state.stage = "source"
    state.log("Starting source metadata ingestion...")

    source_json_list: list[Any] = []

    # 1. Read uploaded source metadata files
    for file in files:
        try:
            content = await file.read()
            if content:
                decoded = json.loads(content.decode("utf-8"))
                source_json_list.append(decoded)
        except Exception as e:
            err_msg = f"Invalid JSON in source file '{file.filename}': {str(e)}"
            logger.error(err_msg)
            return JSONResponse(status_code=400, content={"error": err_msg})

    # 2. Read raw JSON if provided
    if raw_json and raw_json.strip():
        try:
            parsed = json.loads(raw_json)
            if isinstance(parsed, list):
                source_json_list.extend(parsed)
            else:
                source_json_list.append(parsed)
        except Exception as e:
            err_msg = f"Invalid raw JSON text provided: {str(e)}"
            logger.error(err_msg)
            return JSONResponse(status_code=400, content={"error": err_msg})

    if not source_json_list:
        return JSONResponse(
            status_code=400, 
            content={"error": "No Datasphere JSON sources provided."}
        )

    # 3. Parse SourceTables
    parsed_tables: list[SourceTable] = []
    seen_names: set[str] = set()

    for item in source_json_list:
        try:
            tables = DatasphereParser.parse(item)
            for t in tables:
                orig_name = t.name
                c = 2
                while t.name in seen_names:
                    t.name = f"{orig_name}_{c}"
                    c += 1
                seen_names.add(t.name)
                parsed_tables.append(t)
                state.log(f"Parsed table '{t.name}' with {len(t.fields)} fields.")
        except Exception as e:
            err_msg = f"Failed to parse source JSON: {str(e)}"
            state.add_error(err_msg)
            logger.error(err_msg)

    state.source_tables = parsed_tables

    # 4. Process OPTIONAL sample data in temporary memory
    sample_patterns_map = {}
    if sample_files:
        state.log(f"Processing {len(sample_files)} optional sample data file(s) for pattern extraction...")
        for s_file in sample_files:
            try:
                s_content = await s_file.read()
                # Extract patterns and immediately discard raw rows
                patterns = parse_and_learn_patterns(s_content, max_rows=20)
                
                # Match to table by filename stem or fallback to first table
                matched_table_name = parsed_tables[0].name if parsed_tables else "DEFAULT"
                for t in parsed_tables:
                    if t.name.lower() in s_file.filename.lower():
                        matched_table_name = t.name
                        break
                sample_patterns_map[matched_table_name] = patterns
                state.log(f"Learned patterns for '{matched_table_name}' from sample '{s_file.filename}'. Real rows discarded.")
            except Exception as e:
                state.log(f"Warning: Could not extract patterns from sample file '{s_file.filename}': {e}")

    # 5. Generate deterministic synthetic dummy data (never real data)
    state.dummy_data = {}
    for table in parsed_tables:
        pat = sample_patterns_map.get(table.name)
        fake_rows = generate_dummy_data(table, row_count=rows, patterns=pat)
        state.dummy_data[table.name] = fake_rows
        state.log(f"Generated {len(fake_rows)} synthetic rows for '{table.name}'.")

    set_current_state(state)
    return state.model_dump()
