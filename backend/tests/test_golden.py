"""Golden regression — the deterministic (offline) pipeline output for both
fixtures must match the committed expected packages (timestamps ignored)."""

from __future__ import annotations

import pytest

from backend.agents.hiring.workflow import run_to_interrupt
from backend.core.common.config import REPO_ROOT
from backend.core.common.json_io import read_json
from backend.tests.conftest import load_meeting

GOLDEN = REPO_ROOT / "data" / "fixtures" / "expected_outputs"
_VOLATILE = {"generated_at", "timestamp", "started_at", "completed_at"}


def _strip(obj):
    if isinstance(obj, dict):
        return {k: _strip(v) for k, v in obj.items() if k not in _VOLATILE}
    if isinstance(obj, list):
        return [_strip(x) for x in obj]
    return obj


@pytest.mark.parametrize("name", ["strong", "borderline"])
def test_offline_output_matches_golden(name):
    snap = run_to_interrupt(load_meeting(name), thread_id=f"golden-{name}")
    ap = snap.values["approval_package"].model_dump(mode="json")
    ops = snap.values["operations_package"].model_dump(mode="json")

    gold_ap = read_json(GOLDEN / f"meeting_package_{name}.approval.json")
    gold_ops = read_json(GOLDEN / f"meeting_package_{name}.operations.json")

    assert _strip(ap) == _strip(gold_ap)
    assert _strip(ops) == _strip(gold_ops)
