"""Central configuration. Everything is driven by environment variables (.env)."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


def _list(name: str, default: str) -> list[str]:
    return [x.strip() for x in os.getenv(name, default).split(",") if x.strip()]


@dataclass(frozen=True)
class Settings:
    # --- database ---
    database_url: str = os.getenv(
        "DATABASE_URL", "postgresql+psycopg2://fde:fde_pass@localhost:5432/ehrdb"
    )
    table: str = os.getenv("EHR_TABLE", "patient_encounters")

    # --- embeddings ---
    # "hash"  : dependency-free lexical embedder (offline demo, CI, tests)
    # "st"    : sentence-transformers model (semantic; needs requirements-ml.txt)
    embed_backend: str = os.getenv("EMBED_BACKEND", "hash")
    embed_model: str = os.getenv("EMBED_MODEL", "NeuML/bioclinical-modernbert-embeddings")
    embed_dim: int = int(os.getenv("EMBED_DIM", "768"))

    # --- redaction (Presidio) ---
    spacy_model: str = os.getenv("SPACY_MODEL", "en_core_web_sm")
    redact_entities: list[str] = field(
        default_factory=lambda: _list(
            "REDACT_ENTITIES",
            "PERSON,ORGANIZATION,DATE_TIME,PHONE_NUMBER,EMAIL_ADDRESS,US_SSN,SSN_CUSTOM,MRN,LOCATION",
        )
    )
    redact_threshold: float = float(os.getenv("REDACT_THRESHOLD", "0.4"))
    hospital_names: list[str] = field(
        default_factory=lambda: _list(
            "HOSPITAL_NAMES", "St. Mary's General Hospital,Riverside Medical Center"
        )
    )

    # --- LLM ---
    # "mock"   : extractive answer from redacted context, no API key needed
    # "openai" : any OpenAI-compatible endpoint (OpenAI, DeepSeek, Groq, Ollama, vLLM...)
    llm_provider: str = os.getenv("LLM_PROVIDER", "mock")
    llm_base_url: str = os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_model: str = os.getenv("LLM_MODEL", "deepseek-chat")

    # --- retrieval / guardrails ---
    top_k: int = int(os.getenv("TOP_K", "8"))
    use_nemo: bool = os.getenv("USE_NEMO", "false").lower() == "true"

    # --- API ---
    api_key: str = os.getenv("API_KEY", "")  # if set, /api/v1/* requires X-API-Key
    api_url: str = os.getenv("API_URL", "http://localhost:8000")


@lru_cache
def get_settings() -> Settings:
    return Settings()
