"""Embed each encounter's text and store it in clinical_embeddings.

Safe to re-run: only rows WHERE clinical_embeddings IS NULL are processed (use --force to redo all).
  python scripts/04_generate_embeddings.py [--batch 250] [--limit 1000] [--force]
"""
import argparse
import time

from _common import ROOT  # noqa: F401
from sqlalchemy import text

from ehr.config import get_settings
from ehr.db import get_engine, vec_literal
from ehr.embeddings import Embedder
from ehr.retrieval import row_to_text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", type=int, default=250)
    ap.add_argument("--limit", type=int, default=0, help="0 = all pending rows")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    s, eng = get_settings(), get_engine()
    emb = Embedder(s.embed_backend, s.embed_model, s.embed_dim)
    where = "" if a.force else "WHERE clinical_embeddings IS NULL"
    lim = f"LIMIT {int(a.limit)}" if a.limit else ""
    with eng.connect() as c:
        pending = c.execute(text(f"SELECT COUNT(*) FROM {s.table} {where}")).scalar()
    print(f"backend={s.embed_backend} model={s.embed_model if s.embed_backend=='st' else 'feature-hash'} dim={s.embed_dim}; pending={pending}")

    done, t0 = 0, time.time()
    while True:
        with eng.connect() as c:
            rows = [dict(r._mapping) for r in c.execute(text(
                f"SELECT * FROM {s.table} WHERE clinical_embeddings IS NULL ORDER BY id LIMIT :b"
                if not a.force else
                f"SELECT * FROM {s.table} ORDER BY id OFFSET :off LIMIT :b"),
                {"b": a.batch, "off": done})]
        if not rows or (a.limit and done >= a.limit):
            break
        vecs = emb.encode([row_to_text({k: v for k, v in r.items() if k != "clinical_embeddings"}) for r in rows])
        with eng.begin() as c:
            c.execute(text(f"UPDATE {s.table} SET clinical_embeddings = CAST(:v AS vector) WHERE id = :id"),
                      [{"v": vec_literal(v), "id": r["id"]} for r, v in zip(rows, vecs)])
        done += len(rows)
        print(f"  embedded {done}/{pending}  ({done/(time.time()-t0):.0f} rows/s)")
    print("done.")


if __name__ == "__main__":
    main()
