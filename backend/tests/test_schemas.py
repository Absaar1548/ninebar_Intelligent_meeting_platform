"""Schema contract tests — every file under ``data/`` validates, malformed
input is rejected, and the generated packages round-trip through JSON."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from backend.core.common.config import REPO_ROOT
from backend.core.common.json_io import read_json
from backend.core.llm.fallback_provider import minimal_valid_instance
from backend.schemas import (
    ApprovalPackage,
    ApprovalStatus,
    ExecutionStatus,
    HiringTracker,
    MeetingPackage,
    OperationsPackage,
)

FIXTURES = REPO_ROOT / "data" / "fixtures" / "meeting_packages"
STRONG = FIXTURES / "meeting_package_strong.json"
BORDERLINE = FIXTURES / "meeting_package_borderline.json"
TRACKER = REPO_ROOT / "data" / "hiring_tracker.json"


@pytest.mark.parametrize("path", [STRONG, BORDERLINE])
def test_meeting_packages_validate(path):
    mp = MeetingPackage.model_validate(read_json(path))
    assert mp.schema_version == "1.0"
    assert mp.domain == "hiring"
    assert mp.meeting_id == mp.metadata.meeting_id
    assert len(mp.transcript) == 24
    assert mp.payload.candidate.name
    assert mp.payload.role.title == "Lead AI Engineer"
    assert mp.payload.tracker.candidate_id


def test_hiring_tracker_validates():
    ht = HiringTracker.model_validate(read_json(TRACKER))
    assert len(ht.candidates) == 2
    assert len(ht.role.pipeline_stages) == 5
    absaar = ht.find("cand-001-absaar")
    assert absaar is not None
    assert absaar.name == "Absaar Ali"
    assert len(absaar.history) == 3  # history entries preserved
    assert ht.find("does-not-exist") is None


def test_malformed_meeting_package_rejected():
    bad = read_json(STRONG)
    del bad["metadata"]  # drop a required field
    with pytest.raises(ValidationError):
        MeetingPackage.model_validate(bad)


def test_malformed_tracker_rejected():
    with pytest.raises(ValidationError):
        HiringTracker.model_validate({"role": {"title": "x"}})  # missing fields


def test_operations_package_round_trips():
    ops = minimal_valid_instance(OperationsPackage)
    assert isinstance(ops, OperationsPackage)
    reloaded = OperationsPackage.model_validate(ops.model_dump(mode="json"))
    assert reloaded.model_dump() == ops.model_dump()


def test_approval_package_defaults_and_round_trip():
    ap = minimal_valid_instance(ApprovalPackage)
    assert isinstance(ap, ApprovalPackage)
    # §7.10: pending / not_started at generation time
    assert ap.approval_status is ApprovalStatus.PENDING
    assert ap.execution_status is ExecutionStatus.NOT_STARTED
    reloaded = ApprovalPackage.model_validate(ap.model_dump(mode="json"))
    assert reloaded.approval_status is ApprovalStatus.PENDING
