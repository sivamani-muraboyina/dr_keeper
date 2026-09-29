# 5-minute recruiter demo

**Setup:** `docker compose up --build` (or local quickstart). Open http://localhost:8501. Keep "Show pipeline trace" ON.

1. **Frame (20 s):** "Hospital EHR + LLM = HIPAA problem. My system lets clinicians query one patient's history without PHI ever reaching the model."
2. **Happy path (60 s):** pick a patient → click *"What medications were prescribed to this patient?"*. Open the trace: rows retrieved, distances, redaction counts, **redacted context** (`[PERSON]`, `[MRN]`, `[DATE_TIME]`) while `Furosemide 40 mg IV BID` and lab values stay intact.
3. **Why patient-first (30 s):** "Filter to one patient, then vector-search ~10 rows, not the whole table. At 25 M rows that's ~250,000× fewer comparisons."
4. **Guardrails (60 s):** click *"Should I increase the diuretic dose?"* → 🛑 blocked `medical_advice`; then *"What is the patient's name and phone number?"* → blocked `identity_request`; then the injection prompt → blocked. "LLM was never called; zero API cost."
5. **Audit (30 s):** open http://localhost:8000/api/v1/audit (add `X-API-Key` if set) → each decision logged, no raw PHI.
6. **Numbers (45 s):** `make eval` → 99.7 % PHI recall, 94 % clinical-term retention, p50 latency. "Synthetic data, so treat as regression metrics."
7. **Honest close (45 s):** limitations slide: external-LLM BAA, NER misses, date redaction, regex brittleness; next steps: semantic embeddings, date-shifting, RBAC/TLS, AWS deploy.

**Likely questions:** why pgvector not Pinecone? why redact before *and* after? why not LangGraph? how would you scale to 25 M rows? how do you know redaction works? → answers in `docs/INTERVIEW_CHEATSHEET.md`.
