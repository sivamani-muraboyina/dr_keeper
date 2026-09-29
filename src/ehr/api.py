"""FastAPI backend.  Run: uvicorn ehr.api:app --host 0.0.0.0 --port 8000  (PYTHONPATH=src)"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text

from .config import get_settings
from .db import get_engine
from .pipeline import SecurePipeline
from .retrieval import list_patients

_state: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    _state["pipeline"] = SecurePipeline()  # heavy objects (spaCy, embedder) loaded ONCE
    yield
    _state.clear()


app = FastAPI(title="Secure EHR Insight & Clinical Validator", version="1.0.0", lifespan=lifespan)


def require_key(x_api_key: str | None = Header(default=None)):
    key = get_settings().api_key
    if key and x_api_key != key:
        raise HTTPException(status_code=401, detail="invalid or missing X-API-Key")


class Message(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str = Field(max_length=4000)


class ChatRequest(BaseModel):
    patient_id: int
    messages: list[Message] = Field(min_length=1, max_length=40)


@app.get("/health")
def health():
    with get_engine().connect() as c:
        c.execute(text("SELECT 1"))
    s = get_settings()
    return {"status": "ok", "llm": s.llm_provider, "embed": s.embed_backend, "guard_nemo": s.use_nemo}


@app.get("/api/v1/patients", dependencies=[Depends(require_key)])
def patients():
    return {"patients": list_patients()}


# sync def on purpose: FastAPI runs it in a threadpool (blocking DB / LLM calls stay off the event loop)
@app.post("/api/v1/chat", dependencies=[Depends(require_key)])
def chat(req: ChatRequest):
    if req.messages[-1].role != "user":
        raise HTTPException(400, "last message must be from the user")
    res = _state["pipeline"].chat(req.patient_id, [m.model_dump() for m in req.messages])
    return {
        "response": res.answer,
        "blocked": res.blocked,
        "category": res.category,
        "trace": res.trace,
        "disclaimer": "AI-generated from redacted records. Not for diagnostic use.",
    }


@app.get("/api/v1/audit", dependencies=[Depends(require_key)])
def audit(limit: int = 50):
    with get_engine().connect() as c:
        rows = c.execute(
            text("SELECT id, ts, patient_id, question_redacted, decision, category, rows_retrieved "
                 "FROM audit_log ORDER BY id DESC LIMIT :n"),
            {"n": min(limit, 500)},
        ).all()
    return {"events": [dict(r._mapping) for r in rows]}
