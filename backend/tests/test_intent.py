"""Deterministic intent classifier + §12 modification-target mapping."""

from __future__ import annotations

import pytest

from backend.agents.hiring.services.intent import (
    ACTION_PLANNING,
    DECISION_SYNTHESIS,
    DRAFT_GENERATION,
    classify_intent,
)
from backend.schemas.enums import Intent


@pytest.mark.parametrize(
    "msg", ["approve", "approve all", "please proceed", "execute now", "looks good, ship it"]
)
def test_approvals(msg):
    assert classify_intent(msg).intent is Intent.APPROVAL


def test_modify_email_maps_to_draft_generation():
    r = classify_intent("please rewrite the email to be warmer")
    assert r.intent is Intent.MODIFICATION
    assert r.modification_target == DRAFT_GENERATION


def test_modify_recommendation_maps_to_decision_synthesis():
    r = classify_intent("change the recommendation to reject")
    assert r.intent is Intent.MODIFICATION
    assert r.modification_target == DECISION_SYNTHESIS


def test_modify_tracker_maps_to_action_planning():
    r = classify_intent("remove the tracker update from the actions")
    assert r.intent is Intent.MODIFICATION
    assert r.modification_target == ACTION_PLANNING


@pytest.mark.parametrize("msg", ["what's the weather?", "tell me a joke", "who are you"])
def test_unsupported(msg):
    assert classify_intent(msg).intent is Intent.UNSUPPORTED


def test_modify_verb_without_target_is_unsupported():
    # "change something" has a modify verb but no resolvable target (A#7).
    assert classify_intent("change something please").intent is Intent.UNSUPPORTED


def test_empty_message_unsupported():
    assert classify_intent("").intent is Intent.UNSUPPORTED
