# Phase 7 - Streamlit UI (`ui/app.py`)

**Goal:** Patient selector, chat, and an inspectable processing trace.

## Steps
1. Sidebar patient select (cached 300 s), sample-question buttons (including ones that get blocked).
2. `st.session_state.messages` is the chat memory; `patient_id` is sent on every request so the model never 'forgets' the patient.
3. Per-message expander shows the pipeline trace and the redacted context; disclaimer on every answer.
4. Run: `streamlit run ui/app.py` (API must be up).

## Done when
Selecting a patient and asking a question shows an answer + trace; a prescribing question shows 🛑.
