from __future__ import annotations

from functools import lru_cache

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from .config import get_settings


@lru_cache
def get_engine() -> Engine:
    return create_engine(get_settings().database_url, pool_pre_ping=True)


def vec_literal(vec) -> str:
    """pgvector text literal: '[0.1,0.2,...]' (use with CAST(:v AS vector))."""
    return "[" + ",".join(f"{float(x):.6f}" for x in vec) + "]"


def ensure_audit_table(engine: Engine | None = None) -> None:
    engine = engine or get_engine()
    with engine.begin() as c:
        c.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS audit_log (
                id BIGSERIAL PRIMARY KEY,
                ts TIMESTAMPTZ NOT NULL DEFAULT now(),
                patient_id BIGINT,
                question_redacted TEXT,
                decision TEXT NOT NULL,           -- answered | blocked | no_records
                category TEXT,                    -- guardrail category if blocked
                rows_retrieved INT,
                redaction_counts JSONB
            )"""
            )
        )
