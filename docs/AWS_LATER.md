# AWS deployment (do this after the local demo works)

Goal: same Docker Compose stack on one EC2 instance. Order matters: **Security Group → EC2 → Elastic IP**.

1. Security group: SSH 22 from *your IP only*; 8501 from anywhere (or your IP for private demos). **Do not open 5432 or 8000.**
2. EC2: Ubuntu 24.04, t3.large / 8 GB if using `WITH_ML=true` (semantic embeddings), 4 GB is fine for `hash` + `mock`; 30 GB disk (image with torch is large).
3. Elastic IP → associate.
4. Install Docker (official docs) → `git clone` → `cp .env.example .env` (set `LLM_*`, `API_KEY`, strong `DB_PASSWORD`) → `docker compose up -d --build`.
5. Data: `data/sample_encounters.csv` loads automatically. For the Kaggle MIMIC-style CSV: copy it to `data/`, then
   `docker compose exec api python scripts/02_ingest.py --csv data/<file>.csv --reset && docker compose exec api python scripts/03_apply_vector_schema.py && docker compose exec api python scripts/04_generate_embeddings.py --limit 10000`.
6. Cost hygiene: stop the instance when idle; release the Elastic IP and delete volumes when done.

Upgrades to consider afterwards: HTTPS (Caddy/ALB), Secrets Manager, RDS Postgres (pgvector supported), CloudWatch logs, CI/CD deploy, semantic embeddings, date-shifting.
