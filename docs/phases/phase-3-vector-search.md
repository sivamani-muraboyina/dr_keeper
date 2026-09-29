# Phase 3 - prove semantic search (gate)

**Goal:** Nothing later works if cosine search doesn't.

## Steps
1. `python scripts/05_test_vector_search.py --q "…" --patient <id>`.
2. SQL: `… WHERE subject_id=:pid AND clinical_embeddings IS NOT NULL ORDER BY clinical_embeddings <=> :q LIMIT k` (`<=>` = cosine distance, smaller = closer).
3. Caveat: `hash` backend matches words, not meaning.

## Done when
Top rows are relevant to the query and belong to the patient.
