# Compliance & Limitations

## Regulatory frame
* **HIPAA** covers providers, clearinghouses, insurers and their business associates. **PHI** = any data that can
  identify a patient: names, addresses, phone, SSN, MRN, email, dates, photos, financial and medical-record data.
* This repo is a **compliance-aware design**, not a certified system. Real HIPAA use needs risk analysis, BAAs with every
  vendor touching PHI, access control, audit retention, encryption, and (often) certification.
* Redaction patterns are region-specific (US SSN here; India would need Aadhaar, etc.).
* Not every number is PII - lab values / counts must survive redaction.

## Current Implementation Boundaries
| Gap | Current implementation |
|---|---|
| External LLM API sees data (BAA problem) | Data is synthetic, so no real PHI leaves. Default `mock` LLM sends nothing anywhere. Real use: BAA-covered or self-hosted model (Ollama/vLLM). |
| Only ~11k of 232k rows embedded (7 h on CPU) | The included dataset has 276 rows and embeds in seconds. Scaling requires GPU, batching, HNSW indexing, or a smaller model. |
| Guardrails cost extra LLM calls per question | The default guardrail is deterministic regex: 0 API calls, ~4 ms. NeMo is optional. |
| No audit trail | `audit_log` table + `/api/v1/audit`. |
| Open API | optional `X-API-Key`; only the UI port is public in compose. |
| No tests / metrics | 55 tests, `make eval` produces reproducible numbers, and a CI workflow is included. |

## Limitations that remain (state these honestly)
* **Metrics are on synthetic data authored by the repo owner.** PHI-leak 0.3 % / retention 94 % will be worse on real,
  messy clinical notes. The guardrail suite is a regression set (rules were fixed after seeing 1 miss), not a benchmark.
* NER-based person detection can miss names (4/617 leaked with `lg`, 22/617 with `sm`) and can over-redact clinical words;
  a clinical-heuristics filter reduces (not removes) false positives.
* **Structured dates are redacted too** (`admit_date` → `[DATE_TIME]`), which removes timeline reasoning. Upgrade: date-shifting per patient.
* `hash` embeddings are lexical, so "fluid retention" won't find "ascites". Use `EMBED_BACKEND=st` for semantic retrieval.
* Regex guardrails are brittle to paraphrase; add an LLM/classifier layer (NeMo, Llama Guard) for depth.
* No user authentication / RBAC beyond a shared API key; no HTTPS in the compose file (terminate TLS at a proxy/ALB).
* Postgres `pg_hba` / security groups must be locked down when deployed; secrets belong in a secrets manager, not `.env`.
* The LLM can still hallucinate; grounding prompt + "answer only from context" reduces it but is not a guarantee.
* NeMo layer is experimental and was not exercised in the build environment. Docker/compose files were written but not run there either (Postgres/pgvector, API, UI, tests and eval were run directly).
