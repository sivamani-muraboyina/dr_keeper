"""Measured quality numbers you can quote (and reproduce) - on SYNTHETIC data.

  python scripts/07_evaluate.py
1. Redaction  : PHI leak rate + clinical-term retention on the synthetic notes (planted ground truth).
2. Guardrails : accuracy on data/eval_guardrail.json (regression suite authored by the repo owner).
3. Latency    : per-stage p50 / p95 through the full pipeline (needs the DB up + embeddings loaded).
Small, author-written sets: treat as regression tests, not as an independent benchmark.
"""
import json
import statistics as st
import sys

import pandas as pd
from _common import ROOT

from ehr.guardrails import check_input
from ehr.redaction import ClinicalPIIRedactor


def redaction_eval():
    truth = json.loads((ROOT / "data" / "sample_phi_truth.json").read_text())
    df = pd.read_csv(ROOT / "data" / "sample_encounters.csv", dtype=str)
    r = ClinicalPIIRedactor()
    from ehr.config import get_settings
    print(f"(spaCy model: {get_settings().spacy_model})")
    phi_total = phi_leaked = keep_total = keep_ok = 0
    by_kind: dict[str, list[int]] = {}
    for _, row in df.iterrows():
        t = truth[str(row["hadm_id"])]
        red = r.redact(row["doctor_comments"]).text
        for p in t["phi"]:
            phi_total += 1
            leaked = p in red
            phi_leaked += leaked
            kind = ("phone" if p.startswith("555-") else
                    "ssn" if p.count("-") == 2 and p.replace("-", "").isdigit() else
                    "email" if "@" in p else
                    "date" if any(ch.isdigit() for ch in p) and ("/" in p or "," in p) else
                    "mrn" if p.isdigit() else "address" if any(w in p for w in ("Street","Avenue","Road","Drive")) else
                    "organization" if any(w in p for w in ("Hospital","Center")) else "person")
            by_kind.setdefault(kind, [0, 0])
            by_kind[kind][0] += 1
            by_kind[kind][1] += leaked
        for k in t["keep"]:
            keep_total += 1
            keep_ok += k in red
    print("== Redaction (synthetic notes, planted PHI) ==")
    print(f"notes={len(df)}  planted PHI strings={phi_total}")
    print(f"PHI leak rate      : {phi_leaked}/{phi_total} = {100*phi_leaked/phi_total:.1f}%   (recall {100-100*phi_leaked/phi_total:.1f}%)")
    print(f"clinical retention : {keep_ok}/{keep_total} = {100*keep_ok/keep_total:.1f}%  (drug/dose/lab value survive redaction)")
    for k, (n, l) in sorted(by_kind.items()):
        print(f"   {k:<13} leaked {l}/{n}")
    return phi_leaked, phi_total


def guard_eval():
    ev = json.loads((ROOT / "data" / "eval_guardrail.json").read_text())
    fa = [q for q in ev["allowed"] if not check_input(q).allowed]      # false refusals
    fb = [q for q in ev["blocked"] if check_input(q).allowed]          # missed blocks
    n = len(ev["allowed"]) + len(ev["blocked"])
    print("\n== Guardrails (rule layer) ==")
    print(f"accuracy {n-len(fa)-len(fb)}/{n} = {100*(n-len(fa)-len(fb))/n:.1f}%  | false refusals {len(fa)}/{len(ev['allowed'])} | missed blocks {len(fb)}/{len(ev['blocked'])}")
    for q in fa: print("   FALSE REFUSAL:", q)
    for q in fb: print("   MISSED BLOCK :", q)


def latency_eval(n=30):
    try:
        from ehr.pipeline import SecurePipeline
        from ehr.retrieval import list_patients
        pipe, pats = SecurePipeline(), list_patients()
    except Exception as e:  # DB not up
        print("\n== Latency == skipped:", type(e).__name__, str(e)[:80]); return
    qs = ["What medications were prescribed at discharge?", "Show the last lab results",
          "What diagnoses appear in the records?", "Summarize the admission history"]
    lat = {"guard": [], "embed_search": [], "redact": [], "llm": [], "total": []}
    for i in range(n):
        res = pipe.chat(pats[i % len(pats)], [{"role": "user", "content": qs[i % len(qs)]}])
        for k, v in res.trace.get("latency_ms", {}).items():
            lat[k].append(v)
    print(f"\n== Latency ({n} queries, patient-scoped, LLM_PROVIDER={pipe.s.llm_provider}) ==")
    for k, v in lat.items():
        v = sorted(v)
        print(f"{k:<13} p50 {st.median(v):7.1f} ms   p95 {v[int(0.95*(len(v)-1))]:7.1f} ms")


if __name__ == "__main__":
    redaction_eval(); guard_eval(); latency_eval()
