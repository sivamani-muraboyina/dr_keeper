import json
from pathlib import Path

import pytest

from ehr.guardrails import check_input

EV = json.loads((Path(__file__).resolve().parents[1] / "data" / "eval_guardrail.json").read_text())


@pytest.mark.parametrize("q", EV["allowed"])
def test_history_questions_allowed(q):
    assert check_input(q).allowed, q


@pytest.mark.parametrize("q", EV["blocked"])
def test_unsafe_questions_blocked(q):
    assert not check_input(q).allowed, q


def test_empty_question_blocked():
    assert not check_input("   ").allowed
