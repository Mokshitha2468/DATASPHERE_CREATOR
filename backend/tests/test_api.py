"""Integration tests for all FastAPI endpoints."""

from pathlib import Path
from starlette.testclient import TestClient
from app.main import app

client = TestClient(app)
SAMPLE_DIR = Path(__file__).parent / "sample_data"


def test_api_samples_route():
    response = client.get("/api/samples")
    assert response.status_code == 200
    data = response.json()
    assert "samples" in data


def test_api_sources_ingestion_and_pipeline():
    sample_path = SAMPLE_DIR / "sales_order_csn.json"
    with open(sample_path, "rb") as f:
        response = client.post(
            "/api/sources",
            files={"files": ("sales_order_csn.json", f, "application/json")},
            data={"intention": "Sales Modeling", "requirement": "Calculate Net Revenue", "rows": 20},
        )
    assert response.status_code == 200
    data = response.json()
    assert len(data["source_tables"]) == 1
    assert data["source_tables"][0]["name"] == "SALES_ORDERS"
    assert "SALES_ORDERS" in data["dummy_data"]
    assert len(data["dummy_data"]["SALES_ORDERS"]) == 20

    # Test Plan Generation
    plan_res = client.post("/api/plan", json={"requirement": "Model Revenue", "intention": "Fact View"})
    assert plan_res.status_code == 200
    plan_data = plan_res.json()
    assert plan_data["plan_version"] >= 1
    assert plan_data["plan"] is not None
    assert plan_data["plan_status"] == "draft"

    # Test Plan Edit via feedback
    edit_res = client.post("/api/plan/edit", json={"feedback": "Drop TAX_AMOUNT column"})
    assert edit_res.status_code == 200
    edit_data = edit_res.json()
    assert edit_data["plan_version"] >= 2

    # Test Plan Versions
    versions_res = client.get("/api/plan/versions")
    assert versions_res.status_code == 200
    versions_data = versions_res.json()
    assert len(versions_data["versions"]) >= 2

    # Test Plan Approval
    approve_res = client.post("/api/plan/approve")
    assert approve_res.status_code == 200
    approved_data = approve_res.json()
    assert approved_data["plan_status"] == "approved"
    assert approved_data["stage"] == "fact_view"

    # Test State route
    state_res = client.get("/api/state")
    assert state_res.status_code == 200
    assert state_res.json()["plan_status"] == "approved"

    # Test Logs route
    logs_res = client.get("/api/logs")
    assert logs_res.status_code == 200
    assert len(logs_res.json()["logs"]) > 0


def test_api_logs_stream():
    from app.observability.events import event_bus
    import asyncio
    
    event_bus.publish("test_event", {"info": "unit test event"})
    
    async def _test():
        gen = event_bus.stream()
        # Read the initial 'connected' event
        first = await gen.__anext__()
        assert "data:" in first
        assert "connected" in first
        await gen.aclose()

    asyncio.run(_test())
