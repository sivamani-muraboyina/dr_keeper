"""Generate a SYNTHETIC EHR-style CSV (no real patients) with PHI planted in free-text notes,
so the redaction layer has something real to catch.  Deterministic (seeded).

  python scripts/01_generate_sample_data.py [--patients 24] [--out data/sample_encounters.csv]
"""
import argparse
import json
import random
from datetime import date, timedelta

import pandas as pd
from _common import ROOT

FIRST = ["Maria", "James", "Aisha", "Wei", "Carlos", "Priya", "Olivia", "Ahmed", "Sofia", "Daniel",
         "Fatima", "Lucas", "Ananya", "Grace", "Ivan", "Nora", "Tariq", "Elena", "Kofi", "Mei"]
LAST = ["Gonzalez", "Carter", "Khan", "Zhang", "Ramirez", "Sharma", "Brown", "Hassan", "Rossi", "Kim",
        "Ali", "Silva", "Reddy", "Taylor", "Petrov", "Novak", "Rahman", "Costa", "Mensah", "Tan"]
DOCS = ["Dr. Patel", "Dr. Nguyen", "Dr. Alvarez", "Dr. Okafor", "Dr. Fischer"]
HOSP = ["St. Mary's General Hospital", "Riverside Medical Center"]
STREETS = ["Oak Street", "Maple Avenue", "Cedar Road", "Elm Drive"]

# condition -> (diagnoses, drugs[(name, dose)], tests[(name, template)], severity)
CONDS = {
    "liver": (["Cirrhosis with ascites", "Other disorders of liver", "Hepatic encephalopathy"],
              [("Furosemide", "40 mg IV BID"), ("Spironolactone", "100 mg PO daily"), ("Lactulose", "20 g PO TID")],
              [("Albumin", "2.4 g/dL"), ("INR", "1.9"), ("Bilirubin", "3.8 mg/dL")], "severe"),
    "cardiac": (["Congestive heart failure", "Atrial fibrillation", "Hypertensive heart disease"],
                [("Furosemide", "20 mg IV daily"), ("Metoprolol", "50 mg PO BID"), ("Lisinopril", "10 mg PO daily")],
                [("BNP", "980 pg/mL"), ("Troponin", "0.02 ng/mL"), ("Potassium", "3.4 mmol/L")], "moderate"),
    "infection": (["Community acquired pneumonia", "Urinary tract infection", "Sepsis"],
                  [("Ceftriaxone", "1 g IV daily"), ("Vancomycin", "1.25 g IV q12h"), ("Azithromycin", "500 mg PO daily")],
                  [("WBC", "14.2 x10^9/L"), ("Urine culture", "10,000 CFU/mL E. coli"), ("Lactate", "2.8 mmol/L")], "severe"),
    "diabetes": (["Type 2 diabetes mellitus", "Diabetic ketoacidosis", "Diabetic neuropathy"],
                 [("Metformin", "1000 mg PO BID"), ("Insulin glargine", "20 units SC nightly"), ("Gabapentin", "300 mg PO TID")],
                 [("HbA1c", "9.1 %"), ("Glucose", "312 mg/dL"), ("Creatinine", "1.4 mg/dL")], "moderate"),
    "renal": (["Chronic kidney disease stage 4", "Acute kidney injury", "Hyperkalemia"],
              [("Sevelamer", "800 mg PO TID"), ("Calcitriol", "0.25 mcg PO daily"), ("Sodium bicarbonate", "650 mg PO BID")],
              [("Creatinine", "3.1 mg/dL"), ("eGFR", "22 mL/min"), ("Potassium", "5.9 mmol/L")], "severe"),
    "respiratory": (["COPD exacerbation", "Asthma exacerbation", "Acute respiratory failure"],
                    [("Prednisone", "40 mg PO daily"), ("Albuterol", "2.5 mg nebulized q4h"), ("Ipratropium", "0.5 mg nebulized q6h")],
                    [("SpO2", "88 % on room air"), ("pCO2", "58 mmHg"), ("Respiratory culture", "no growth at 48 h")], "moderate"),
}
ADM = ["URGENT", "EMERGENCY", "ELECTIVE"]


def note(rng, name, mrn, ssn, phone, email, street, stnum, doc, hosp, when, cond_dx, drug, dose, test, val):
    templates = [
        f"Patient {name} (MRN {mrn}) admitted to {hosp} on {when:%m/%d/%Y} with {cond_dx}. {doc} reviewed labs: {test} {val}. Started {drug} {dose}.",
        f"Follow-up by {doc}. {name} reports improvement. {test} {val}. Continue {drug} {dose}. Family contact number {phone}.",
        f"Discharge summary for {name}, SSN {ssn}, residing at {stnum} {street}. Discharged from {hosp}. Medications on discharge: {drug} {dose}. Email {email} for follow-up.",
        f"{cond_dx} stable. {test} {val}. {drug} {dose} continued. Discussed plan with {doc} on {when:%B %d, %Y}.",
    ]
    return rng.choice(templates)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--patients", type=int, default=24)
    ap.add_argument("--out", default=str(ROOT / "data" / "sample_encounters.csv"))
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    rng = random.Random(a.seed)
    rows, truth, hadm = [], {}, 200000
    for i in range(a.patients):
        sid = 10000000 + i * 137 + rng.randint(0, 99)
        name = f"{rng.choice(FIRST)} {rng.choice(LAST)}"
        mrn, ssn = rng.randint(1000000, 9999999), f"{rng.randint(100,899)}-{rng.randint(10,99)}-{rng.randint(1000,9999)}"
        phone, email = f"555-{rng.randint(200,999)}-{rng.randint(1000,9999)}", f"{name.split()[0].lower()}.{rng.randint(1,99)}@example.com"
        street, hosp, stnum = rng.choice(STREETS), rng.choice(HOSP), rng.randint(10, 99)
        conds = rng.sample(list(CONDS), k=rng.choice([1, 2, 2]))
        d0 = date(2024, 1, 1) + timedelta(days=rng.randint(0, 200))
        for _ in range(rng.randint(8, 14)):
            c = rng.choice(conds)
            dxs, drugs, tests, sev = CONDS[c]
            dx, (drug, dose), (test, val) = rng.choice(dxs), rng.choice(drugs), rng.choice(tests)
            d0 += timedelta(days=rng.randint(1, 20))
            hadm += 1
            doc = rng.choice(DOCS)
            text_ = note(rng, name, mrn, ssn, phone, email, street, stnum, doc, hosp, d0, dx, drug, dose, test, val)
            cands = [name, name.split()[-1], str(mrn), ssn, phone, email, f"{stnum} {street}", doc.split()[-1],
                     hosp, f"{d0:%m/%d/%Y}", f"{d0:%B %d, %Y}"]
            truth[str(hadm)] = {"phi": [c_ for c_ in cands if c_ in text_], "keep": [k_ for k_ in (drug, dose, val) if k_ in text_]}
            rows.append({
                "subject_id": sid, "hadm_id": hadm, "admission_type": rng.choice(ADM),
                "admit_date": d0.isoformat(), "diagnosis": dx, "drug": drug, "drug_dose": dose,
                "test_name": test, "test_result": val, "severity": sev,
                "doctor_comments": text_,
            })
    pd.DataFrame(rows).to_csv(a.out, index=False)
    # ground truth for scripts/07_evaluate.py (planted PHI strings per row) - NOT loaded into the DB
    (ROOT / "data" / "sample_phi_truth.json").write_text(json.dumps(truth))
    print(f"wrote {len(rows)} rows for {a.patients} synthetic patients -> {a.out}")


if __name__ == "__main__":
    main()
