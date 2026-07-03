"""Evidence-first enforcement — grounding validators reject ungrounded output,
and the LLMClient ``validate`` hook drives a regenerate (Appendix A#3)."""

from __future__ import annotations

import pytest

from backend.agents.hiring.services.evidence import (
    validate_decision_grounded,
    validate_findings_grounded,
)
from backend.core.common.config import Settings
from backend.core.llm.base import LLMValidationError
from backend.core.llm.client import LLMClient
from backend.schemas.artifacts import (
    Decision,
    EvidenceGraph,
    EvidenceNode,
    EvidenceRef,
    Finding,
    Findings,
)
from backend.schemas.enums import EvidenceSourceType, Recommendation

GRAPH = EvidenceGraph(
    nodes=[EvidenceNode(id="t1", source_type=EvidenceSourceType.TRANSCRIPT,
                        locator="transcript.turn[1]", content="evidence")]
)


def test_ungrounded_findings_rejected():
    bad = Findings(strengths=[Finding(statement="x", evidence_refs=[EvidenceRef(evidence_id="ghost")])])
    with pytest.raises(ValueError):
        validate_findings_grounded(bad, GRAPH)


def test_grounded_findings_pass():
    ok = Findings(strengths=[Finding(statement="x", evidence_refs=[EvidenceRef(evidence_id="t1")])])
    validate_findings_grounded(ok, GRAPH)  # no raise


def test_decision_without_evidence_rejected():
    bad = Decision(recommendation=Recommendation.MOVE_FORWARD, confidence=0.9,
                   reasoning="because", evidence_refs=[])
    with pytest.raises(ValueError):
        validate_decision_grounded(bad, GRAPH)


class _GroundedAfterRetry:
    def __init__(self) -> None:
        self.calls = 0

    def complete_json(self, prompt: str, *, system: str | None = None) -> str:
        self.calls += 1
        ref = "ghost" if self.calls == 1 else "t1"
        return (
            '{"strengths":[{"statement":"strong","evidence_refs":'
            f'[{{"evidence_id":"{ref}"}}]}}],'
            '"weaknesses":[],"risks":[],"contradictions":[],'
            '"missing_information":[],"open_questions":[]}'
        )


def test_validate_hook_triggers_regenerate():
    fake = _GroundedAfterRetry()
    client = LLMClient(
        settings=Settings(llm_mode="cloud", llm_fallback_enabled=False,
                          llm_max_retries=1, llm_retry_backoff_seconds=0.0),
        provider=fake,
    )
    out = client.generate_structured(
        "prompt", Findings,
        validate=lambda f: validate_findings_grounded(f, GRAPH),
    )
    assert fake.calls == 2  # first ungrounded, regenerated grounded
    assert out.strengths[0].evidence_refs[0].evidence_id == "t1"


def test_persistently_ungrounded_raises_without_fallback():
    class _AlwaysGhost:
        def complete_json(self, prompt: str, *, system: str | None = None) -> str:
            return ('{"strengths":[{"statement":"x","evidence_refs":'
                    '[{"evidence_id":"ghost"}]}],"weaknesses":[],"risks":[],'
                    '"contradictions":[],"missing_information":[],"open_questions":[]}')

    client = LLMClient(
        settings=Settings(llm_mode="cloud", llm_fallback_enabled=False,
                          llm_max_retries=1, llm_retry_backoff_seconds=0.0),
        provider=_AlwaysGhost(),
    )
    with pytest.raises(LLMValidationError):
        client.generate_structured(
            "p", Findings, validate=lambda f: validate_findings_grounded(f, GRAPH))
