"""Gate check: does patient-scoped cosine search return sensible rows?"""
import argparse

from _common import ROOT  # noqa: F401
from ehr.config import get_settings
from ehr.embeddings import Embedder
from ehr.retrieval import list_patients, row_to_text, search_patient


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--q", default="fluid retention treated with a diuretic")
    ap.add_argument("--patient", type=int, default=0)
    a = ap.parse_args()
    s = get_settings()
    emb = Embedder(s.embed_backend, s.embed_model, s.embed_dim)
    pid = a.patient or list_patients()[0]
    print(f"patient={pid}  query={a.q!r}")
    for r in search_patient(pid, emb.encode([a.q])[0], 3):
        print(f"  dist={r['distance']:.3f} | {row_to_text(r)[:150]}")


if __name__ == "__main__":
    main()
