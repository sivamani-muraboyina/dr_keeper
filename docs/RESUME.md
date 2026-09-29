# Resume material

**Project title:** Secure EHR Insight & Clinical Validator - HIPAA-aware clinical RAG (Python, Postgres/pgvector, Presidio, FastAPI, Streamlit, Docker)

**Bullets (edit numbers only if you re-run `make eval` and they change):**
* Built a privacy-first clinical Q&A system: patient-scoped pgvector retrieval in the client's existing Postgres, Presidio PHI redaction before/after the LLM, and rule-based guardrails blocking treatment, identity-disclosure and prompt-injection requests.
* Built an evaluation harness on synthetic EHR notes with planted PHI: **99.7 % identifier recall (4/1,242 leaks)** and **94 % clinical-term retention**; guardrail regression suite 44/44; 55 automated tests + GitHub Actions CI.
* Added per-query audit logging, API-key auth, output redaction and a Docker Compose stack (Postgres+pgvector, FastAPI, Streamlit); ~175 ms p50 pipeline latency excluding LLM generation.
* (After AWS step) Deployed on AWS EC2 with Docker, locked-down security groups and Elastic IP.

**Attribution line for the README/interviews:** "Architecture based on a public FDE live-coding session; guardrail layer, audit log, evaluation harness, tests and CI are my additions."

**Do not claim:** HIPAA compliant/certified · real patient data · a benchmark result · production use.
