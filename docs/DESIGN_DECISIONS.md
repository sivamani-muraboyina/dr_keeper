# Secure EHR Insight: Problem, Solution, and Design Decisions

## 1. Problem Statement

Clinical records contain useful history, but they are difficult to query quickly. A clinician may need to find a medication, lab result, diagnosis, or encounter detail across many records for one patient. A natural-language interface can make that history easier to inspect, but it introduces serious risks:

- Patient identifiers and other protected health information (PHI) must not be sent to an external LLM.
- A retrieval system must not mix records from different patients.
- The assistant must answer historical-record questions, not diagnose or prescribe.
- Every request needs an auditable decision and outcome.
- The system should run locally and remain useful without a paid model API during development.

This repository is a reference implementation using synthetic data. It is not a HIPAA certification, a production clinical system, or a substitute for clinical judgment.

## 2. Solution Summary

The application provides a Streamlit chat interface backed by a FastAPI service. The backend uses the existing relational EHR database as the source of truth and adds vector embeddings to the encounter table with pgvector.

For each request, the system:

1. Lets the clinician select one patient.
2. Redacts identifiers from the question before logging or downstream processing.
3. Applies deterministic guardrails before retrieval or an LLM call.
4. Embeds the question and searches only that patient's encounters.
5. Redacts retrieved records before they become LLM context.
6. Generates either an extractive offline response or an answer through an OpenAI-compatible provider.
7. Redacts the answer again and writes a PHI-safe audit event.

The complete request path is shown in [secure-query-flow.svg](diagrams/secure-query-flow.svg).

## 3. Decisions and Trade-offs

### 3.1 Keep Postgres as the system of record

**Decision:** Keep encounter data in Postgres and add a vector column rather than moving records into a separate retrieval database.

**Why:** The EHR is already stored in a relational database. Migrating clinical records to a separate vector database would add data movement, synchronization, access-control, backup, and operational costs. It could also create two sources of truth for the same patient.

**Trade-off:** A dedicated vector database can offer specialized scaling, filtering, and indexing features. For this system, keeping retrieval beside the source rows makes patient scoping and transactional ownership simpler. A separate vector service can be reconsidered at hospital scale after measuring database load.

### 3.2 Use pgvector instead of a separate vector database

**Decision:** Store embeddings in a `vector(768)` column and use pgvector cosine distance in SQL.

**Why:** pgvector works inside the existing Postgres deployment, supports patient filters in the same query, and avoids another service to operate. The query can apply `WHERE subject_id = :pid` before ranking, which is essential for tenant and patient isolation.

**Trade-off:** A specialized vector database may provide better approximate-nearest-neighbor throughput for very large corpora. pgvector couples vector workload to the relational database, so indexing, connection pooling, and query latency must be monitored as data grows.

### 3.3 Filter by patient before vector search

**Decision:** Require a patient selection and search only that patient's embedded encounters.

**Why:** This is a safety boundary, not only an optimization. It prevents the retriever from choosing a semantically similar record belonging to another patient. It also reduces the number of vector comparisons by searching a small patient-specific subset instead of the entire table.

**Trade-off:** Users must select the correct patient before asking a question. Cross-patient population analysis is intentionally outside this interface and would need a separate authorization and query design.

### 3.4 Use hybrid embedding modes: hash by default, semantic model optionally

**Decision:** Provide a deterministic feature-hashing embedder for offline use and an optional biomedical sentence-transformer backend for semantic retrieval.

**Why:** The hash backend has no model download, API cost, or GPU requirement. It makes local setup, CI, and tests reliable. The semantic backend improves meaning-based matching for real retrieval experiments.

**Trade-off:** Hash embeddings are lexical and are not true semantic embeddings. The semantic model is heavier, slower to download, and requires the database vector dimension to match the model exactly. Changing the backend requires regenerating stored embeddings.

### 3.5 Redact before the LLM, and redact the output again

**Decision:** Use Presidio, spaCy, and custom recognizers to replace identifiers with typed placeholders before context reaches the LLM. Run the same protection on the generated answer.

**Why:** Sending raw PHI to a third-party model is already a disclosure. Output redaction provides defense in depth if a model repeats an identifier or if a hidden value appears in generated text. Clinical false-positive rules preserve useful drugs, doses, lab values, and units.

**Trade-off:** NER and regex redaction are imperfect. Aggressive thresholds can remove clinically useful text; permissive thresholds can miss identifiers. The system therefore includes custom patterns, a hospital deny-list, evaluation data, and explicit limitations rather than claiming perfect detection.

### 3.6 Put deterministic guardrails before retrieval and generation

**Decision:** Run regex-based intent rules before embedding, database retrieval, or any LLM call. Optionally add NeMo Guardrails as a second layer.

**Why:** Medical advice, identity requests, prompt injection, and unrelated questions can be rejected deterministically with zero model cost. Blocking early also reduces the chance that unsafe requests reach patient data or the model.

**Trade-off:** Rules can miss paraphrases and can occasionally over-block legitimate questions. The project keeps them narrow enough to allow historical questions such as a previously recorded dose. NeMo is optional because it adds dependencies and operational complexity.

### 3.7 Support an offline mock LLM

**Decision:** Use an extractive mock response by default and support any OpenAI-compatible provider through configuration.

**Why:** Developers can run the full retrieval, redaction, guardrail, and audit path without an API key or network dependency. Production-like experiments can use Groq, OpenAI, DeepSeek, Ollama, or another compatible endpoint without changing the pipeline.

**Trade-off:** Mock responses do not demonstrate open-ended generation quality. External providers introduce cost, latency, availability, and data-governance concerns. Only redacted context is sent by this application, but provider terms and organizational policy still need review.

### 3.8 Use FastAPI and Streamlit as separate processes

**Decision:** Keep Streamlit responsible for presentation and FastAPI responsible for the protected application pipeline.

**Why:** The separation makes the API testable, supports a future non-Streamlit client, keeps database and model work out of the UI layer, and gives the backend one place to enforce guardrails and audit behavior.

**Trade-off:** Local and cloud deployments need service discovery, environment variables, and at least two processes. Streamlit Community Cloud cannot run the current Docker Compose stack by itself. The documented deployment target is Docker, with AWS used for a prior validated deployment.

### 3.9 Use Docker Compose for reproducible local operation

**Decision:** Package Postgres/pgvector, FastAPI, and Streamlit as three Compose services.

**Why:** The database extension, API dependencies, bootstrap process, and UI can be started consistently with one command. This reduces machine-specific setup problems.

**Trade-off:** Docker consumes more resources than a single Python process and is not directly equivalent to a managed cloud deployment. The Compose configuration is intended for reproducible development and validation, not as a complete production hardening guide.

### 3.10 Audit decisions, not raw PHI

**Decision:** Store timestamp, patient ID, redacted question, decision, category, row count, and redaction counts in `audit_log`.

**Why:** Compliance and debugging require evidence of what the system decided. Storing redacted content and counts gives useful traceability without deliberately copying raw questions or raw context into the audit table.

**Trade-off:** A useful audit trail still needs access control, retention rules, monitoring, and a defined operator identity in a real deployment. This implementation records the application event but does not implement a complete enterprise identity system.

## 4. Deployment Position

The application was deployed and tested on AWS during development. The instance was terminated after validation to avoid ongoing infrastructure costs. There is no maintained public deployment at present.

The current Docker Compose architecture can be deployed again on a VM or split into separate managed services. Streamlit Community Cloud can host the UI process, but it cannot host the current FastAPI, Postgres, and pgvector stack as one application. A Streamlit-only deployment would require a separate architecture using local or in-memory data, which is intentionally not part of this project.

## 5. Known Limitations

- The data is synthetic and must not be replaced with real PHI without a full security and compliance review.
- The default hash embedding backend is lexical, not semantic.
- Redaction has measured false positives and false negatives.
- The application uses an optional API key header, not enterprise authentication or authorization.
- Audit events do not yet include a real authenticated clinician identity.
- In-memory application state and local deployment choices are not designed for high availability.
- NeMo Guardrails is experimental and disabled by default.

## 6. Validation

Run the main checks with:

```bash
make test
make eval
```

Start the complete local stack with:

```bash
docker compose up --build
```

The Streamlit UI is available at `http://localhost:8501`, the FastAPI service at `http://localhost:8000`, and the API documentation at `http://localhost:8000/docs`.
