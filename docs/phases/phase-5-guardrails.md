# Phase 5 - guardrails (`src/ehr/guardrails.py`, `src/ehr/nemo/`)

**Goal:** Decide what may be asked BEFORE retrieval or the LLM.

## Steps
1. Rule layer categories: `medical_advice`, `identity_request`, `prompt_injection`, `out_of_scope`. History questions ('last recorded dose of furosemide') must pass.
2. Optional NeMo/Colang layer (`USE_NEMO=true`, `pip install nemoguardrails`) mirrors the live session's `rails.co`; experimental.
3. `python scripts/06_test_guardrails.py`; regression set in `data/eval_guardrail.json` (44 prompts).

## Done when
`pytest tests/test_guardrails.py` passes.
