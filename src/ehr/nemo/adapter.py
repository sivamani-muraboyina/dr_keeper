"""Optional second guardrail layer using NVIDIA NeMo Guardrails (Colang).

EXPERIMENTAL: not exercised in the sandbox this repo was generated in. The default,
tested guardrail is the deterministic rule layer in ehr/guardrails.py.
Note: LLM-backed rails cost extra API calls per question.
"""
from __future__ import annotations

import os
from pathlib import Path

from ..config import get_settings

REFUSAL_PREFIX = "I am an enterprise EHR retrieval system"


class NemoGuard:
    def __init__(self):
        from nemoguardrails import LLMRails, RailsConfig  # pip install nemoguardrails

        s = get_settings()
        os.environ.setdefault("OPENAI_API_KEY", s.llm_api_key)
        os.environ.setdefault("OPENAI_API_BASE", s.llm_base_url)
        self.rails = LLMRails(RailsConfig.from_path(str(Path(__file__).parent)))

    def check(self, question: str, context_lines: list[str]) -> str | None:
        """Return the refusal text if NeMo blocks the question, else None."""
        out = self.rails.generate(messages=[{"role": "user", "content": question}])
        content = out["content"] if isinstance(out, dict) else str(out)
        return content if content.startswith(REFUSAL_PREFIX) else None
