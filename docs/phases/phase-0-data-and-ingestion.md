# Phase 0 - the 'client system' (baseline data)

**Goal:** Stand up Postgres and load the EHR table - this is what the hospital already has.

## Steps
1. Docker: `docker compose up` creates `db` (pgvector image). Local: any Postgres 14+ with pgvector.
2. `python scripts/01_generate_sample_data.py` → synthetic CSV with planted PHI + `sample_phi_truth.json` (ground truth for eval).
3. `python scripts/02_ingest.py --csv data/sample_encounters.csv --reset` → headers normalised, `subject_id/hadm_id` BIGINT, rest TEXT, index on `subject_id`.
4. Kaggle MIMIC-style CSV (232,158 rows, already anonymised): drop in `data/`, pass `--csv`.

## Done when
`SELECT COUNT(*)` equals the CSV row count.
