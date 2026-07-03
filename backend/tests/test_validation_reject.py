"""Context Validation gatekeeping — malformed / empty packages terminate as
Rejected and no reasoning runs (§7.1, Appendix A#1)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from backend.agents.hiring.nodes.context_validation import (
    business_errors,
    context_validation_node,
)
from backend.agents.hiring.workflow import run_to_interrupt
from backend.core.common.config import REPO_ROOT
from backend.core.common.json_io import read_json
from backend.schemas.enums import WorkflowStage
from backend.schemas.meeting_package import MeetingPackage

STRONG = REPO_ROOT / "data" / "fixtures" / "meeting_packages" / "meeting_package_strong.json"


def test_schema_malformed_package_rejected_before_graph():
    bad = read_json(STRONG)
    del bad["payload"]  # required
    with pytest.raises(ValidationError):
        MeetingPackage.model_validate(bad)


def test_empty_transcript_terminates_rejected():
    data = read_json(STRONG)
    data["transcript"] = []
    mp = MeetingPackage.model_validate(data)  # schema-valid but empty transcript
    snap = run_to_interrupt(mp, thread_id="test-empty")
    assert snap.values["workflow_stage"] == WorkflowStage.REJECTED
    assert snap.next == ()  # terminated, never reached wait_for_human
    assert "approval_package" not in snap.values


def test_business_errors_detects_missing_and_empty():
    data = read_json(STRONG)
    data["transcript"] = []
    data["domain"] = "sales"
    mp = MeetingPackage.model_validate(data)
    errs = business_errors(mp)
    assert any("transcript" in e for e in errs)
    assert any("domain" in e for e in errs)


def test_validation_node_marks_valid_package():
    mp = MeetingPackage.model_validate(read_json(STRONG))
    out = context_validation_node({"meeting_package": mp})
    assert out["workflow_stage"] == WorkflowStage.VALIDATED
