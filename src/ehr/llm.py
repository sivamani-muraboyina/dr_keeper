"""LLM access. The LLM only ever sees REDACTED context.

mock   : extractive, deterministic answer built from the redacted context (no API key, offline demo).
openai : any OpenAI-compatible endpoint via base_url (OpenAI, DeepSeek, Groq, Ollama, vLLM...).
"""
from __future__ import annotations

from .config import Settings, get_settings

SYSTEM_PROMPT = (
    "You are a clinical records retrieval assistant for licensed healthcare staff.\n"
    "Rules:\n"
    "1. Answer ONLY from the CONTEXT (the selected patient's redacted historical records).\n"
    "2. If the context does not contain the answer, say so plainly. Never guess or invent.\n"
    "3. Never give treatment, prescribing or diagnostic recommendations.\n"
    "4. Placeholders like [PERSON] or [DATE_TIME] are redactions; do not try to infer the hidden values.\n"
    "5. Be concise. Quote drug names, doses and lab values exactly as written."
)


class LLM:
    def __init__(self, settings: Settings | None = None):
        self.s = settings or get_settings()
        self._client = None
        if self.s.llm_provider == "openai":
            if not self.s.llm_api_key:
                raise SystemExit("LLM_PROVIDER=openai requires LLM_API_KEY")
            from openai import OpenAI

            self._client = OpenAI(api_key=self.s.llm_api_key, base_url=self.s.llm_base_url)
        elif self.s.llm_provider != "mock":
            raise ValueError("LLM_PROVIDER must be 'mock' or 'openai'")

    def answer(self, question: str, context_lines: list[str], history: list[dict]) -> str:
        if self._client is None:
            return self._mock(question, context_lines)
        context = "\n".join(f"- {c}" for c in context_lines)
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages += [m for m in history[-6:] if m["role"] in ("user", "assistant")]
        messages.append({"role": "user", "content": f"CONTEXT:\n{context}\n\nQUESTION: {question}"})
        resp = self._client.chat.completions.create(
            model=self.s.llm_model, messages=messages, temperature=0.1, max_tokens=500
        )
        return (resp.choices[0].message.content or "").strip()

    @staticmethod
    def _mock(question: str, context_lines: list[str]) -> str:
        head = "Most relevant records for this patient (redacted; offline demo mode, no LLM):"
        return head + "\n" + "\n".join(f"{i}. {c}" for i, c in enumerate(context_lines[:5], 1))
