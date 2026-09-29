import pytest

from ehr.redaction import ClinicalPIIRedactor


@pytest.fixture(scope="module")
def red():
    return ClinicalPIIRedactor()


def test_direct_identifiers_removed(red):
    t = ("Patient Maria Gonzalez (MRN 4471920) seen at St. Mary's General Hospital. "
         "Call 555-201-7788 or maria.g@example.com. SSN 123-45-6789.")
    out = red.redact(t).text
    for leaked in ("Maria", "Gonzalez", "4471920", "555-201-7788", "maria.g@example.com", "123-45-6789", "St. Mary"):
        assert leaked not in out


def test_clinical_values_survive(red):
    t = "Urine culture grew 10,000 CFU/mL E. coli; creatinine 1.8 mg/dL. Furosemide 40 mg IV BID."
    out = red.redact(t).text
    for keep in ("10,000 CFU/mL", "1.8 mg/dL", "Furosemide 40 mg IV BID"):
        assert keep in out


def test_lab_and_drug_names_not_treated_as_people(red):
    out = red.redact("Bilirubin 3.8 mg/dL. Started Sevelamer 800 mg PO TID.").text
    assert "Bilirubin" in out and "Sevelamer" in out


def test_counts_reported(red):
    r = red.redact("Email a.b@example.com or call 555-201-7788")
    assert r.counts.get("EMAIL_ADDRESS") == 1 and r.total >= 2
