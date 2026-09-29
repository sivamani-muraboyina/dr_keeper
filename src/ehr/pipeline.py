"""End-to-end secure query pipeline.

question -> input guard -> embed -> patient-scoped vector search -> REDACT context
         -> (optional NeMo) -> LLM (sees redacted text only) -> redact answer -> audit log
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field

from sqlalchemy import text

from .config import Settings, get_settings
from .db import ensure_audit_table, get_engine
from .embeddings import Embedder
from .guardrails import check_input
from .llm import LLM
from .redaction import ClinicalPIIRedactor
from .retrieval import row_to_text, search_patient

NO_RECORDS = "No historical record found for this patient."


@dataclass
class ChatResult:
    answer: str
    blocked: bool = False
    category: str = "ok"
    trace: dict = field(default_factory=dict)


class SecurePipeline:
    def __init__(self, settings: Settings | None = None):
        self.s = settings or get_settings()
        self.embedder = Embedder(self.s.embed_backend, self.s.embed_model, self.s.embed_dim)
        self.redactor = ClinicalPIIRedactor(self.s)
        self.llm = LLM(self.s)
        self.nemo = None
        if self.s.use_nemo:
            from .nemo.adapter import NemoGuard  # optional, experimental

            self.nemo = NemoGuard()
        ensure_audit_table()

    # ---- audit -----------------------------------------------------------------
    def _audit(self, pid, q_red, decision, category, rows, counts):
        with get_engine().begin() as c:
            c.execute(
                text(
                    """INSERT INTO audit_log
                       (patient_id, question_redacted, decision, category, rows_retrieved, redaction_counts)
                       VALUES (:p, :q, :d, :c, :r, CAST(:j AS jsonb))"""
                ),
                {"p": pid, "q": q_red, "d": decision, "c": category, "r": rows, "j": json.dumps(counts)},
            )

    # ---- main ------------------------------------------------------------------
    def chat(self, patient_id: int, messages: list[dict]) -> ChatResult:
        t0 = time.perf_counter()
        history = [m for m in messages[:-1]]
        question = messages[-1]["content"] if messages else ""
        q_red = self.redactor.redact(question)  # doctors may paste identifiers; never log/send raw

        g = check_input(question)
        if not g.allowed:
            self._audit(patient_id, q_red.text, "blocked", g.category, 0, {})
            return ChatResult(g.message, True, g.category, {"guard_layer": g.layer})

        t1 = time.perf_counter()
        qvec = self.embedder.encode([q_red.text])[0]
        rows = search_patient(patient_id, qvec, self.s.top_k)
        t2 = time.perf_counter()

        if not rows:
            self._audit(patient_id, q_red.text, "no_records", None, 0, {})
            return ChatResult(NO_RECORDS, False, "no_records", {"rows_retrieved": 0})

        raw_lines = [row_to_text(r) for r in rows]
        red = [self.redactor.redact(x) for x in raw_lines]
        context_lines = [r.text for r in red]
        counts: dict[str, int] = {}
        for r in red:
            for k, v in r.counts.items():
                counts[k] = counts.get(k, 0) + v
        t3 = time.perf_counter()

        if self.nemo is not None:
            nres = self.nemo.check(q_red.text, context_lines)
            if nres is not None:  # NeMo refused
                self._audit(patient_id, q_red.text, "blocked", "nemo", len(rows), counts)
                return ChatResult(nres, True, "nemo", {"guard_layer": "nemo"})

        hist_red = [{"role": m["role"], "content": self.redactor.redact(m["content"]).text} for m in history]
        answer = self.llm.answer(q_red.text, context_lines, hist_red)
        answer = self.redactor.redact(answer).text  # defense in depth on the output
        t4 = time.perf_counter()

        self._audit(patient_id, q_red.text, "answered", None, len(rows), counts)
        return ChatResult(
            answer,
            False,
            "ok",
            {
                "rows_retrieved": len(rows),
                "redaction_counts": counts,
                "redacted_context": context_lines,
                "distances": [round(float(r["distance"]), 4) for r in rows],
                "latency_ms": {
                    "guard": round((t1 - t0) * 1000, 1),
                    "embed_search": round((t2 - t1) * 1000, 1),
                    "redact": round((t3 - t2) * 1000, 1),
                    "llm": round((t4 - t3) * 1000, 1),
                    "total": round((t4 - t0) * 1000, 1),
                },
            },
        )
