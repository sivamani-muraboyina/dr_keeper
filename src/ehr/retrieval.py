"""Row -> text formatting and patient-scoped cosine search in Postgres (pgvector)."""
from __future__ import annotations

from sqlalchemy import text

from .config import get_settings
from .db import get_engine, vec_literal

# columns never used as embedding/context text
SKIP_COLS = {"id", "subject_id", "hadm_id", "clinical_embeddings", "distance"}


def row_to_text(row: dict) -> str:
    """One 'super string' per encounter: 'col: value | col: value ...' (non-null values only)."""
    parts = [
        f"{k.replace('_', ' ')}: {str(v).strip()}"
        for k, v in row.items()
        if k not in SKIP_COLS and v is not None and str(v).strip() not in ("", "nan", "None")
    ]
    return " | ".join(parts)


def list_patients(limit: int = 500) -> list[int]:
    s = get_settings()
    with get_engine().connect() as c:
        rows = c.execute(
            text(
                f"SELECT DISTINCT subject_id FROM {s.table} "
                f"WHERE clinical_embeddings IS NOT NULL ORDER BY subject_id LIMIT :n"
            ),
            {"n": limit},
        ).all()
    return [r[0] for r in rows]


def search_patient(patient_id: int, query_vec, k: int | None = None) -> list[dict]:
    """Top-k cosine-nearest encounters for ONE patient. `<=>` = cosine distance (smaller = closer)."""
    s = get_settings()
    k = k or s.top_k
    with get_engine().connect() as c:
        res = c.execute(
            text(
                f"""SELECT *, clinical_embeddings <=> CAST(:q AS vector) AS distance
                    FROM {s.table}
                    WHERE subject_id = :pid AND clinical_embeddings IS NOT NULL
                    ORDER BY distance ASC LIMIT :k"""
            ),
            {"q": vec_literal(query_vec), "pid": patient_id, "k": k},
        )
        return [dict(r._mapping) for r in res]
