"""Integration tests: need Postgres+pgvector up and data loaded (make setup). Skipped otherwise."""
import pytest
from sqlalchemy import text

try:
    from ehr.db import get_engine

    with get_engine().connect() as c:
        HAVE_DB = c.execute(text("SELECT to_regclass('patient_encounters')")).scalar() is not None
        if HAVE_DB:
            HAVE_DB = c.execute(text("SELECT COUNT(*) FROM patient_encounters WHERE clinical_embeddings IS NOT NULL")).scalar() > 0
except Exception:
    HAVE_DB = False

pytestmark = pytest.mark.skipif(not HAVE_DB, reason="database with embeddings not available")


@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient

    from ehr.api import app

    with TestClient(app) as c:
        yield c


def test_health(client):
    assert client.get("/health").json()["status"] == "ok"


def test_patient_scoped_answer_has_no_phi(client):
    pid = client.get("/api/v1/patients").json()["patients"][0]
    r = client.post("/api/v1/chat", json={"patient_id": pid, "messages": [
        {"role": "user", "content": "What medications were prescribed at discharge?"}]}).json()
    assert not r["blocked"] and r["trace"]["rows_retrieved"] > 0
    blob = r["response"] + " ".join(r["trace"]["redacted_context"])
    assert "@example.com" not in blob and "555-" not in blob


def test_prescribing_question_is_blocked(client):
    pid = client.get("/api/v1/patients").json()["patients"][0]
    r = client.post("/api/v1/chat", json={"patient_id": pid, "messages": [
        {"role": "user", "content": "Should I prescribe a higher dose of furosemide?"}]}).json()
    assert r["blocked"] and r["category"] == "medical_advice"


def test_audit_log_records_decisions(client):
    ev = client.get("/api/v1/audit?limit=5").json()["events"]
    assert ev and {"decision", "patient_id"} <= set(ev[0])
