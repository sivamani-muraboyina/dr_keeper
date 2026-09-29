# Interview cheat sheet

**30-second pitch:** "I built a HIPAA-aware clinical Q&A system: Postgres+pgvector inside the client's stack, patient-scoped
retrieval, Presidio redaction before the LLM, deterministic guardrails that block treatment/identity/injection requests, an audit log, and an
evaluation harness that measures PHI leakage - all containerised."

| Question | Answer |
|---|---|
| Why pgvector, not Pinecone? | Client already runs Postgres: no new dependency, no data movement, one security perimeter. |
| Why select patient first? | Hybrid filter-then-search: 276 demo rows → ~12 per patient; 25 M → ~100 at scale (≈250,000× fewer comparisons). |
| Cosine distance: small or large = similar? | Small. a=(1,2), b=(2,1): sim 0.8, distance 0.2. |
| Why redact before the LLM? | After disclosure it's too late. Also redact the answer (defense in depth) and the user question. |
| Why not redact every number? | Lab values/counts carry the clinical meaning. Clinical-heuristics filter keeps drug/dose/lab tokens (94 % retained). |
| How do you know redaction works? | Planted PHI ground truth in synthetic notes; leak rate 0.3 % (lg) / 1.8 % (sm); reproducible with `make eval`; caveat: synthetic. |
| Why regex guardrails? | Deterministic, free, testable, 4 ms. NeMo/LLM layer optional for paraphrase robustness. |
| Why no LangGraph? | No tool use or loops; a history list is the memory. Avoid overkill. |
| Biggest weaknesses? | Synthetic-only metrics, NER misses, redacted dates, hash embeddings lexical, shared-key auth, external LLM BAA. |
| Scale to 25 M rows? | Keep patient filter + btree on subject_id; HNSW index if cross-patient search is needed; batch/GPU embeddings; read replica. |
| What's beyond an AI engineer here (FDE)? | Asking who the client is, what they run, which law binds them, where it deploys and who operates it. |
