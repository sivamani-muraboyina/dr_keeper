# Phase 2 - embeddings

**Goal:** Turn each encounter into one 'super string' (all non-null columns) and embed it.

## Steps
1. `python scripts/04_generate_embeddings.py [--batch 250] [--limit N] [--force]` - re-runnable: only `clinical_embeddings IS NULL` rows are processed.
2. `EMBED_BACKEND=hash` offline lexical mode; `EMBED_BACKEND=st` + `requirements-ml.txt` for a biomedical sentence-transformer (768-d). General models fragment drug/disease terms; domain models don't.
3. Scale math: ~11k rows/20 min on CPU → 232k rows ≈ 7 h. GPU / batching / smaller model.

## Done when
`COUNT(*) WHERE clinical_embeddings IS NOT NULL` grows.
