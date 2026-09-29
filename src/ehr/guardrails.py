"""Two-layer guardrails.

Layer 1 (always on, deterministic, zero API cost): regex intent rules.
    - medical_advice   : "should I prescribe...", "recommend an antibiotic..."
    - prompt_injection : "ignore previous instructions", "reveal your system prompt"
    - out_of_scope     : "write a python script", "tell me a joke"
    - identity_request : asks for the patient's name / SSN / address / phone
Layer 2 (optional, USE_NEMO=true): NVIDIA NeMo Guardrails + Colang (see src/ehr/nemo/).

History questions ("last recorded dosage of furosemide") must pass; advice requests must not.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

REFUSAL_MEDICAL = (
    "I am an enterprise EHR retrieval system. For legal and compliance reasons I cannot "
    "provide treatment, prescribing or diagnostic recommendations. Please consult the "
    "attending physician."
)
REFUSAL_INJECTION = "I can't follow instructions that try to change my rules or reveal my configuration."
REFUSAL_SCOPE = "I can only answer questions about the selected patient's historical records."
REFUSAL_IDENTITY = (
    "Patient identifiers (name, SSN, address, phone, email) are redacted in this system "
    "and cannot be retrieved."
)

_F = re.IGNORECASE | re.DOTALL
_RULES: list[tuple[str, str, list[re.Pattern]]] = [
    (
        "prompt_injection",
        REFUSAL_INJECTION,
        [
            re.compile(r"\b(ignore|disregard|forget|override)\b.{0,40}\b(previous|prior|above|all|your)\b.{0,30}\b(instruction|rule|prompt|guardrail)s?", _F),
            re.compile(r"\b(reveal|show|print|repeat)\b.{0,30}\b(system prompt|instructions|configuration|api key)", _F),
            re.compile(r"\b(jailbreak|developer mode|DAN mode)\b", _F),
        ],
    ),
    (
        "identity_request",
        REFUSAL_IDENTITY,
        [
            re.compile(r"\b(what('?s| is)|tell me|give me|show me|reveal)\b.{0,25}\b(patient'?s?|his|her|their)?\s*(full name|real name|name|ssn|social security|home address|address|phone number|email)\b", _F),
            re.compile(r"\bwho is (this|the) patient\b", _F),
        ],
    ),
    (
        "medical_advice",
        REFUSAL_MEDICAL,
        [
            re.compile(r"\bshould (i|we|the patient)\b.{0,60}\b(prescribe|start|give|increase|decrease|stop|switch|order|administer|use|take|treat)\b", _F),
            re.compile(r"\b(can|could|may) (i|we)\b.{0,20}\b(prescribe|give|start|increase|order|administer)\b", _F),
            re.compile(r"\b(recommend|suggest|advise)\b.{0,40}\b(drug|medication|medicine|antibiotic|treatment|therapy|dose|dosage|regimen)\b", _F),
            re.compile(r"\bwhat\b.{0,25}\b(drug|medicine|medication|antibiotic|treatment|therapy|dose|dosage)\b.{0,25}\b(should|would|do you recommend|is best|is appropriate)\b", _F),
            re.compile(r"\b(which|what)\b.{0,30}\b(should i|do you)\b.{0,20}\b(prescribe|start|give|order)\b", _F),
            re.compile(r"\b(diagnose|differential diagnosis|what does (he|she|the patient) have)\b", _F),
            re.compile(r"\b(best|optimal|ideal|appropriate|right|recommended)\b.{0,20}\b(treatment|therapy|drug|medication|regimen|antibiotic|approach)\b", _F),
            re.compile(r"\b(treatment plan|management plan|next step in (treatment|management))\b", _F),
            re.compile(r"\b(is it safe|safe to)\b.{0,30}\b(give|prescribe|combine|administer)\b", _F),
        ],
    ),
    (
        "out_of_scope",
        REFUSAL_SCOPE,
        [
            re.compile(r"\b(write|generate|create|debug)\b.{0,25}\b(python|javascript|code|script|program|sql|poem|story|essay|joke)\b", _F),
            re.compile(r"\b(tell me a joke|who won|weather|stock price|capital of)\b", _F),
        ],
    ),
]


@dataclass
class GuardResult:
    allowed: bool
    category: str = "ok"
    message: str = ""
    layer: str = "rules"


def check_input(question: str) -> GuardResult:
    q = (question or "").strip()
    if not q:
        return GuardResult(False, "empty", "Please type a question.", "rules")
    for category, message, patterns in _RULES:
        if any(p.search(q) for p in patterns):
            return GuardResult(False, category, message, "rules")
    return GuardResult(True)
