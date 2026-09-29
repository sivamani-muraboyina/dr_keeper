"""Enable pgvector and add the embedding column (dimension must equal the embedder's output)."""
import argparse

from _common import ROOT  # noqa: F401
from sqlalchemy import text

from ehr.config import get_settings
from ehr.db import ensure_audit_table, get_engine


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hnsw", action="store_true", help="also build an HNSW cosine index (useful at scale)")
    a = ap.parse_args()
    s, eng = get_settings(), get_engine()
    with eng.begin() as c:
        c.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        c.execute(text(f"ALTER TABLE {s.table} ADD COLUMN IF NOT EXISTS clinical_embeddings vector({int(s.embed_dim)})"))
        if a.hnsw:
            c.execute(text(f"CREATE INDEX IF NOT EXISTS idx_{s.table}_emb ON {s.table} USING hnsw (clinical_embeddings vector_cosine_ops)"))
    ensure_audit_table(eng)
    with eng.connect() as c:
        row = c.execute(text(
            "SELECT column_name, udt_name FROM information_schema.columns "
            "WHERE table_name=:t AND column_name='clinical_embeddings'"), {"t": s.table}).first()
    print("column present:" , row)


if __name__ == "__main__":
    main()
