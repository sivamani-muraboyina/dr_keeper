"""One-shot, idempotent setup used by docker compose: wait for DB -> load data if empty -> pgvector schema -> embeddings."""
import subprocess
import sys
import time

from _common import ROOT
from sqlalchemy import text

from ehr.config import get_settings
from ehr.db import get_engine

PY = sys.executable


def run(*args):
    subprocess.run([PY, str(ROOT / "scripts" / args[0]), *args[1:]], check=True)


def main():
    s = get_settings()
    for i in range(60):
        try:
            with get_engine().connect() as c:
                c.execute(text("SELECT 1"))
            break
        except Exception:
            print(f"waiting for database... ({i+1})")
            time.sleep(2)
    else:
        raise SystemExit("database never became reachable")

    with get_engine().connect() as c:
        exists = c.execute(text("SELECT to_regclass(:t)"), {"t": s.table}).scalar()
        n = c.execute(text(f"SELECT COUNT(*) FROM {s.table}")).scalar() if exists else 0
    if n == 0:
        csv = ROOT / "data" / "sample_encounters.csv"
        if not csv.exists():
            run("01_generate_sample_data.py")
        run("02_ingest.py", "--reset")
    else:
        print(f"table {s.table} already has {n} rows - skipping ingest")
    run("03_apply_vector_schema.py")
    run("04_generate_embeddings.py")
    print("bootstrap complete")


if __name__ == "__main__":
    main()
