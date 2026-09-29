# Phase 4 - PHI redaction (`src/ehr/redaction.py`)

**Goal:** Analyzer finds entities → filters → anonymizer replaces with `[ENTITY]`.

## Steps
1. Presidio + spaCy (`SPACY_MODEL`, default `en_core_web_lg`).
2. Custom recognizers: SSN regex (0.9), MRN, street address, clinician titles (`Dr. Patel`); hospital-name deny-list forced to ORGANIZATION (1.0).
3. Per-entity threshold: generic ORG hits need ≥0.95 (spaCy tags 'WBC', 'SSN' as ORG). Clinical filter: PERSON followed by number/unit, ≤2 chars, or DATE_TIME that is only 'daily/BID/q8h' is not redacted.
4. `python scripts/07_evaluate.py` measures leak rate and clinical-term retention.

## Done when
`pytest tests/test_redaction.py` passes; leak rate printed by `make eval`.
