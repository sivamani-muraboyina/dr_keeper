# Phase 8 - Docker & deployment

**Goal:** Reproducible everywhere; only the UI port is public.

## Steps
1. `docker compose up --build` → services `db` (pgvector), `api` (bootstrap then uvicorn), `ui` (Streamlit 8501).
2. `Dockerfile` args: `WITH_ML=true` (torch + sentence-transformers), `SPACY_MODEL`.
3. AWS steps (security group → EC2 → Elastic IP → Docker → Compose): `docs/AWS_DEPLOYMENT.md`.
4. Redeploy after changes: `git pull && docker compose up -d --build`.

## Done when
http://localhost:8501 (or `http://<EC2_IP>:8501`) answers questions.
