# Phase 1 - add vectors inside the client's Postgres

**Goal:** No new database: enable the extension and add an embedding column.

## Steps
1. `python scripts/03_apply_vector_schema.py` → `CREATE EXTENSION vector`; `ALTER TABLE … ADD COLUMN clinical_embeddings vector(768)`; creates `audit_log`.
2. Dimension must equal the embedder output (768) - the embedder asserts it and exits on mismatch.
3. `--hnsw` optionally builds a cosine HNSW index (only useful for cross-patient search at scale).

## Done when
`information_schema` shows the `clinical_embeddings` column.
