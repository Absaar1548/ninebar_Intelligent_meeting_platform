"""Offline dev runner: push a Meeting Package fixture through the pipeline to the
WAIT_FOR_HUMAN interrupt and print the resulting Approval Package.

Usage:
    python -m backend.agents.hiring.dev_runner <fixture.json> [cloud|fallback]

Defaults to ``fallback`` so it runs with no network/LLM cost.
"""

from __future__ import annotations

import sys

from backend.agents.hiring.nodes import set_llm_client
from backend.agents.hiring.workflow import reset_hiring_app, run_to_interrupt
from backend.core.common.config import Settings
from backend.core.common.json_io import read_json
from backend.core.llm.client import LLMClient
from backend.schemas.meeting_package import MeetingPackage


def main(path: str, mode: str = "fallback") -> None:
    # Windows consoles default to cp1252; artifacts contain em-dashes/arrows.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    except (AttributeError, ValueError):
        pass

    set_llm_client(LLMClient(settings=Settings(llm_mode=mode)))  # type: ignore[arg-type]
    reset_hiring_app()

    mp = MeetingPackage.model_validate(read_json(path))
    snap = run_to_interrupt(mp, thread_id=f"dev-{mp.meeting_id}")
    values = snap.values

    print(f"\nmeeting_id : {mp.meeting_id}")
    print(f"candidate  : {mp.payload.candidate.name}")
    print(f"stage      : {values.get('workflow_stage')}")
    print(f"next       : {snap.next}")

    ap = values.get("approval_package")
    if ap is not None:
        print(f"recommend  : {ap.recommendation.value}  (confidence {ap.confidence:.2f})")
        print(f"summary    : {ap.executive_summary}")
        print("\n--- Approval Package (JSON) ---")
        print(ap.model_dump_json(indent=2))
    else:
        print("(no approval package — package was rejected)")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(2)
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "fallback")
