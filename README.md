# SAP Datasphere Creator

Automated modeling pipeline and planner for SAP Datasphere source metadata and analytical views.

## Architecture

```text
Frontend (React 18 + Vite + Tailwind + @xyflow/react)
   ↓
FastAPI Backend (`/api/sources`, `/api/plan`, `/api/state`, `/api/logs`)
   ↓
LangGraph Orchestrator (`check_inputs` → `planner` → `validation` → `fact_agent_stub`)
   ↓
Planner Agent (Mock or Real LLM)
   ↓
Plan Validator (Column partitions, allowed operators, key warnings)
   ↓
Pydantic v2 SharedState
```

## Real Data Privacy & Safety

Sample rows are strictly optional. When provided:

```text
Real sample data (CSV or JSON, max 20 rows)
      ↓
Temporary pattern extraction in memory (prefixes, lengths, dates, flags)
      ↓
Immediate discard of raw rows
      ↓
Synthetic dummy data generation (guaranteed unique keys, valid dates, collision safety)
      ↓
Planner Agent / LLM
```

> [!IMPORTANT]
> **Privacy Guarantee:** Real sample rows never reach the LLM, logs, SharedState, LangSmith traces, or the frontend UI. Only generated synthetic rows are visible or transmitted.

---

## Getting Started

### 1. Run Backend

```bash
cd backend
pip install -r requirements.txt
python run.py
```

Backend API server runs at:
👉 **[http://localhost:8000](http://localhost:8000)** (Swagger docs at `/docs`)

### 2. Run Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend application runs at:
👉 **[http://localhost:5173](http://localhost:5173)**

---

## Running Tests

```bash
cd backend
python -m pytest -v
```
