#!/usr/bin/env sh
# Single-container mode: bootstrap data (idempotent) -> FastAPI (8000) + Streamlit (8501)
set -e
[ "${AUTO_BOOTSTRAP:-true}" = "true" ] && python scripts/bootstrap.py
uvicorn ehr.api:app --host 0.0.0.0 --port 8000 &
for i in $(seq 1 60); do curl -sf http://localhost:8000/health >/dev/null && break; sleep 2; done
exec streamlit run ui/app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true
