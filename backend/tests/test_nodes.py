"""Unit tests for the deterministic reasoner and individual nodes (offline)."""

from __future__ import annotations

from backend.agents.hiring.nodes.context_analysis import context_analysis_node
from backend.agents.hiring.services import evidence as ev
from backend.agents.hiring.services.fallbacks import (
    fallback_findings,
    recommend,
)
from backend.schemas.artifacts import InterviewContext
from backend.schemas.enums import EvidenceSourceType, Recommendation, WorkflowStage
from backend.tests.conftest import load_meeting


def test_coverage_differentiates_candidates():
    strong = ev.coverage_ratio(ev.coverage_report(load_meeting("strong")))
    border = ev.coverage_ratio(ev.coverage_report(load_meeting("borderline")))
    assert strong >= 0.70
    assert border < 0.50
    assert strong > border


def test_disclaimer_downgrades_borderline_multiagent():
    mp = load_meeting("borderline")
    cov = ev.assess_skill(mp, "Multi-agent orchestration (LangGraph)")
    # Meera mentions it but disclaims depth ("newer territory") -> not covered.
    assert cov.mentioned and not cov.covered
    assert cov.disclaimer_ids


def test_evidence_graph_structure_and_missing_rubric():
    graph = ev.build_evidence_graph(load_meeting("strong"))
    ids = ev.evidence_ids(graph)
    assert "resume:skills" in ids
    assert any(i.startswith("jd:must:") for i in ids)
    assert any(i.startswith("t") for i in ids)
    assert EvidenceSourceType.RUBRIC in graph.missing_sources


def test_fallback_findings_are_grounded():
    mp = load_meeting("strong")
    graph = ev.build_evidence_graph(mp)
    findings = fallback_findings(mp, graph)
    assert findings.strengths
    ev.validate_findings_grounded(findings, graph)  # must not raise


def test_recommend_thresholds():
    assert recommend(1.0) is Recommendation.MOVE_FORWARD
    assert recommend(0.5) is Recommendation.ADDITIONAL_INTERVIEW
    assert recommend(0.3) is Recommendation.HOLD
    assert recommend(0.1) is Recommendation.REJECT


def test_context_analysis_node_offline():
    mp = load_meeting("strong")
    out = context_analysis_node({"meeting_package": mp})
    assert isinstance(out["interview_context"], InterviewContext)
    assert out["workflow_stage"] == WorkflowStage.CONTEXT_ANALYZED
    assert out["interview_context"].candidate_name == "Absaar Ali"
