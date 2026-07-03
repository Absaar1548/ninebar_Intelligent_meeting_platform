"""Renderer — chat recommendation, internal panel, and execution views."""

from __future__ import annotations

from backend.agents.hiring.workflow import resume, run_to_interrupt
from backend.core.renderer import (
    render_agent_recommendation,
    render_execution_markdown,
    render_internal,
)
from backend.tests.conftest import load_meeting


def _snap(thread):
    return run_to_interrupt(load_meeting("strong"), thread_id=thread)


def test_agent_recommendation_has_sections():
    md = render_agent_recommendation(_snap("r1").values["approval_package"])
    assert "MOVE FORWARD" in md
    assert "Why this call:" in md
    assert "Proposed actions" in md
    assert "Draft email" in md
    assert "Evidence cited" in md
    assert "approve" in md.lower()  # call to action


def test_recommendation_citations_carry_quotes():
    ap = _snap("r2").values["approval_package"]
    md = render_agent_recommendation(ap)
    assert any(e.quote for e in ap.evidence)  # quotes backfilled
    quote = next(e.quote for e in ap.evidence if e.quote)
    assert quote[:20] in md  # the quote text is rendered next to the citation


def test_render_accepts_dict():
    ap = _snap("r3").values["approval_package"].model_dump(mode="json")
    assert "MOVE FORWARD" in render_agent_recommendation(ap)


def test_render_internal_has_trace_findings_and_graph():
    ops = _snap("r4").values["operations_package"]
    md = render_internal(ops, ["Analyzed the interview context."], "waiting_approval")
    assert "Processing trace" in md
    assert "Assessment" in md
    assert "Findings" in md
    assert "Evidence graph" in md
    assert "resume:skills" in md  # an evidence node id is listed with content


def test_render_internal_handles_missing_ops():
    md = render_internal(None, ["step one"], "context_analyzed")
    assert "Processing trace" in md
    assert "step one" in md


def test_execution_markdown_lists_adapters():
    run_to_interrupt(load_meeting("strong"), thread_id="r5")
    report = resume("approve", "r5").values["execution_results"]
    md = render_execution_markdown(report)
    assert "completed" in md
    for adapter in ("ats", "email", "teams"):
        assert adapter in md
