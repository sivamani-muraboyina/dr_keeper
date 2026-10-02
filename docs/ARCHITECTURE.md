# Architecture

## Problem
A hospital EHR holds millions of rows (admissions, prescriptions, labs, doctor notes). Doctors want to ask
questions about ONE patient's history in plain English. The data is PHI (HIPAA), so it cannot be sent raw to an LLM.

## Design decisions
| Decision | Why |
|---|---|
| pgvector inside the client's Postgres | no new database, no data leaving the client stack |
| Select patient first, then search | filter-then-vector-search: 276 synthetic rows → ~12 per patient (25 M → ~100 at hospital scale ≈ 250,000× fewer comparisons) |
| Redact BEFORE the LLM (and after) | once PHI reaches a third-party model it is already disclosed |
| Guardrails before retrieval/LLM | blocked requests cost nothing and can't leak; deterministic rules are testable and free |
| Custom pipeline, no LangGraph | no tool calls / loops → conversation-history list is enough |
| Audit log | compliance needs "who asked what, what did the system decide" |

## Runtime flow
```
POST /api/v1/chat {patient_id, messages[]}
 ├─ redact(question) → q_red                      (never log/send raw question)
 ├─ guard(question): medical_advice | identity_request | prompt_injection | out_of_scope | empty
 │      └─ blocked → audit(blocked) → refusal text        (LLM not called, DB not touched)
 ├─ embed(q_red) → 768-d vector
 ├─ SELECT … WHERE subject_id=:pid AND clinical_embeddings IS NOT NULL
 │        ORDER BY clinical_embeddings <=> :q LIMIT top_k       (cosine distance, smaller = closer)
 ├─ no rows → audit(no_records) → "No historical record found"
 ├─ redact(each row text) → redacted_context
 ├─ [optional] NeMo rails
 ├─ LLM(system rules + redacted_context + redacted history + q_red)
 ├─ redact(answer)                                 (defense in depth)
 └─ audit(answered, rows, redaction_counts) → response + trace + disclaimer
```

## Components
| Module | Role |
|---|---|
| `ehr/embeddings.py` | `hash` (offline lexical) / `st` (sentence-transformers) backends, dim check |
| `ehr/retrieval.py` | row→text "super string", patient-scoped cosine search |
| `ehr/redaction.py` | Presidio analyzer+anonymizer; custom SSN/MRN/address/title recognizers; hospital deny-list (score 1.0); per-entity thresholds; clinical false-positive filter |
| `ehr/guardrails.py` | rule-based intent guard (+ `nemo/` optional Colang layer) |
| `ehr/llm.py` | OpenAI-compatible client or offline mock |
| `ehr/pipeline.py` | orchestration, timing trace, audit |
| `ehr/api.py` | FastAPI (`/health`, `/patients`, `/chat`, `/audit`), models loaded once at startup, optional `X-API-Key` |
| `ui/app.py` | Streamlit: patient select, chat memory, per-message pipeline trace, disclaimer |

## Data model
`patient_encounters(id, subject_id, hadm_id, …text columns…, clinical_embeddings vector(768))`,
`audit_log(id, ts, patient_id, question_redacted, decision, category, rows_retrieved, redaction_counts jsonb)`.

## Worked numbers
* cosine distance: a=(1,2), b=(2,1) → sim = 4/5 = 0.8 → distance 0.2.
* vector storage: 768 × 4 B = 3,072 B/row → 232,158 rows ≈ 713 MB.
* embedding time at ~11,000 rows/20 min on CPU: 232,158 rows ≈ 7 h (GPU / batching / smaller model fixes this).

## Ports
5432 Postgres (private) · 8000 FastAPI (private) · 8501 Streamlit (the only public port).
