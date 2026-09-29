"""PHI redaction with Microsoft Presidio (analyzer + anonymizer).

Design (mirrors the live session, plus hardening):
* spaCy NER + Presidio built-ins (PERSON, PHONE, EMAIL, DATE_TIME, LOCATION ...)
* custom SSN regex (score 0.9), MRN regex, clinician-title regex ("Dr. Patel")
* hospital-name deny-list forced to ORGANIZATION with score 1.0
* threshold filter, then replace with [ENTITY] placeholders
* NOT every number is PII: lab values / counts are deliberately left alone
"""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field

from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

from .config import Settings, get_settings


@dataclass
class RedactionResult:
    text: str
    counts: dict[str, int] = field(default_factory=dict)

    @property
    def total(self) -> int:
        return sum(self.counts.values())


_FREQ_WORDS = {"daily", "nightly", "weekly", "monthly", "hourly", "bid", "tid", "qid", "qd", "prn", "qhs"}
_TITLE_BEFORE = re.compile(r"(?:Dr|Mr|Mrs|Ms|Prof)\.?\s*$")


def _is_clinical_false_positive(text: str, r) -> bool:
    """Generic clinical heuristics that stop NER from eating drug names, lab names and units.

    * PERSON that is <=2 chars ("L" in mmol/L) or immediately followed by a number+unit
      ("Bilirubin 3.8 mg/dL", "Sevelamer 800 mg") is a measurement/drug, not a person.
    * DATE_TIME that is just a dosing-frequency word ("daily", "BID", "q8h").
    """
    span = text[r.start : r.end]
    if r.entity_type == "PERSON":
        if len(span.strip()) <= 2:
            return True
        if re.match(r"\s+\d", text[r.end : r.end + 4]) and not _TITLE_BEFORE.search(text[: r.start]):
            return True
    if r.entity_type == "DATE_TIME":
        low = span.strip().lower()
        if low in _FREQ_WORDS or re.fullmatch(r"q\d+h", low):
            return True
    return False


class ClinicalPIIRedactor:
    def __init__(self, settings: Settings | None = None):
        s = settings or get_settings()
        self.entities = list(s.redact_entities)
        self.threshold = s.redact_threshold
        # spaCy's ORG tagger fires on clinical abbreviations ("WBC 14.2", "SSN 123-..."),
        # so generic ORG hits must clear a high bar; only our hospital deny-list (score 1.0) passes.
        self.entity_thresholds = {"ORGANIZATION": 0.95}

        nlp = NlpEngineProvider(
            nlp_configuration={
                "nlp_engine_name": "spacy",
                "models": [{"lang_code": "en", "model_name": s.spacy_model}],
            }
        ).create_engine()
        self.analyzer = AnalyzerEngine(nlp_engine=nlp, supported_languages=["en"])
        self.anonymizer = AnonymizerEngine()

        reg = self.analyzer.registry
        reg.add_recognizer(
            PatternRecognizer(
                supported_entity="SSN_CUSTOM",
                patterns=[Pattern("ssn_dashed", r"\b\d{3}-\d{2}-\d{4}\b", 0.9)],
            )
        )
        reg.add_recognizer(
            PatternRecognizer(
                supported_entity="MRN",
                patterns=[Pattern("mrn", r"\bMRN[:#\s-]*\d{5,10}\b", 0.9)],
            )
        )
        reg.add_recognizer(
            PatternRecognizer(
                supported_entity="PERSON",
                patterns=[
                    Pattern(
                        "clinician_title",
                        r"\b(?:Dr|Mr|Mrs|Ms|Prof)\.?\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b",
                        0.85,
                    )
                ],
            )
        )
        reg.add_recognizer(
            PatternRecognizer(
                supported_entity="LOCATION",
                patterns=[
                    Pattern(
                        "street_address",
                        r"\b\d{1,5}\s+(?:[A-Z][a-z]+\s+){1,3}(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Way|Court|Ct)\b\.?",
                        0.85,
                    )
                ],
            )
        )
        if s.hospital_names:
            reg.add_recognizer(
                PatternRecognizer(
                    supported_entity="ORGANIZATION",
                    deny_list=s.hospital_names,
                    deny_list_score=1.0,
                )
            )

        self._operators = {
            e: OperatorConfig("replace", {"new_value": f"[{e}]"}) for e in self.entities
        }

    def redact(self, text: str) -> RedactionResult:
        if not text or not text.strip():
            return RedactionResult(text or "")
        found = self.analyzer.analyze(
            text=text, language="en", entities=self.entities, score_threshold=self.threshold
        )
        found = [
            r for r in found
            if r.score >= self.entity_thresholds.get(r.entity_type, 0.0)
            and not _is_clinical_false_positive(text, r)
        ]
        if not found:
            return RedactionResult(text)
        out = self.anonymizer.anonymize(text=text, analyzer_results=found, operators=self._operators)
        return RedactionResult(out.text, dict(Counter(r.entity_type for r in found)))
