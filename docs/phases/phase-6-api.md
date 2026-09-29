# Phase 6 - FastAPI (`src/ehr/api.py`, `pipeline.py`)

**Goal:** Orchestrate the flow; load heavy models once at startup.

## Steps
1. `GET /health`, `GET /api/v1/patients`, `POST /api/v1/chat {patient_id, messages[]}`, `GET /api/v1/audit`.
2. `chat` returns `response, blocked, category, trace{rows, distances, redaction_counts, redacted_context, latency_ms}`.
3. Optional `API_KEY` → header `X-API-Key`. Endpoints are sync `def` so blocking DB/LLM calls run in FastAPI's threadpool.
4. Run: `PYTHONPATH=src uvicorn ehr.api:app --port 8000`.

## Done when
`pytest tests/test_api_pipeline.py` passes (needs DB).
