"""Load a CSV into Postgres (the 'client system' baseline).

  python scripts/02_ingest.py --csv data/sample_encounters.csv --reset
For the Kaggle MIMIC-style EHR CSV: drop it in data/ and pass --csv. Headers are normalised to
snake_case; subject_id / hadm_id become BIGINT, everything else TEXT.
"""
import argparse
import re

import pandas as pd
from _common import ROOT
from sqlalchemy import text

from ehr.config import get_settings
from ehr.db import get_engine


def norm(c: str) -> str:
    return re.sub(r"[^0-9a-z]+", "_", c.strip().lower()).strip("_")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=str(ROOT / "data" / "sample_encounters.csv"))
    ap.add_argument("--reset", action="store_true", help="drop and recreate the table")
    ap.add_argument("--chunk", type=int, default=2000)
    a = ap.parse_args()

    s, eng = get_settings(), get_engine()
    df = pd.read_csv(a.csv, dtype=str, keep_default_na=False)
    df.columns = [norm(c) for c in df.columns]
    df = df.replace({"": None, "nan": None, "NaT": None})
    if "subject_id" not in df.columns:
        raise SystemExit("CSV must contain a subject_id column (patient identifier)")
    for c in ("subject_id", "hadm_id"):
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").astype("Int64")

    cols = ", ".join(
        f'"{c}" {"BIGINT" if c in ("subject_id", "hadm_id") else "TEXT"}' for c in df.columns
    )
    with eng.begin() as c:
        if a.reset:
            c.execute(text(f"DROP TABLE IF EXISTS {s.table} CASCADE"))
        c.execute(text(f"CREATE TABLE IF NOT EXISTS {s.table} (id BIGSERIAL PRIMARY KEY, {cols})"))
        c.execute(text(f"CREATE INDEX IF NOT EXISTS idx_{s.table}_subject ON {s.table}(subject_id)"))
    df.to_sql(s.table, eng, if_exists="append", index=False, method="multi", chunksize=a.chunk)
    with eng.connect() as c:
        n = c.execute(text(f"SELECT COUNT(*) FROM {s.table}")).scalar()
    print(f"ingested {len(df)} rows; table now has {n} rows")


if __name__ == "__main__":
    main()
