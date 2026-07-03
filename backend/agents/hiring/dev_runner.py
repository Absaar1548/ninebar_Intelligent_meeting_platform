"""Offline dev runner: push a Meeting Package fixture through the pipeline to the
WAIT_FOR_HUMAN interrupt and print the resulting Approval Package.

Usage:
    python -m backend.agents.hiring.dev_runner <fixture.json> [cloud|fallback]

Defaults to ``fallback`` so it runs with no network/LLM cost.
"""

from __future__ import annotations

import sys

from backend.agents.hiring.nodes import set_llm_client
from backend.agents.hiring.workflow import (
    reset_hiring_app,
    resume,
    run_to_interrupt,
)
from backend.core.common.config import Settings
from backend.core.common.json_io import read_json
from backend.core.llm.client import LLMClient
from backend.schemas.meeting_package import MeetingPackage


def _print_snapshot(title: str, snap) -> None:
    v = snap.values
    print(f"\n== {title} ==")
    print(f"stage      : {v.get('workflow_stage')}")
    print(f"next       : {snap.next}")
    ap = v.get("approval_package")
    if ap is not None:
        print(f"recommend  : {ap.recommendation.value}  (confidence {ap.confidence:.2f})")
        print(f"approval   : {ap.approval_status.value} | execution: {ap.execution_status.value}")
    report = v.get("execution_results")
    if report is not None:
        for r in report.results:
            print(f"  exec {r.adapter}: {'ok' if r.ok else 'FAIL'} — {r.detail}")


def main(path: str, mode: str = "fallback", message: str | None = None) -> None:
    # Windows consoles default to cp1252; artifacts contain em-dashes/arrows.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    except (AttributeError, ValueError):
        pass

    set_llm_client(LLMClient(settings=Settings(llm_mode=mode)))  # type: ignore[arg-type]
    reset_hiring_app()

    mp = MeetingPackage.model_validate(read_json(path))
    thread_id = f"dev-{mp.meeting_id}"
    print(f"meeting_id : {mp.meeting_id}  |  candidate: {mp.payload.candidate.name}")

    snap = run_to_interrupt(mp, thread_id=thread_id)
    _print_snapshot("after pipeline (interrupt)", snap)
    if snap.values.get("approval_package") is None:
        print("(no approval package — package was rejected)")
        return

    if message:
        snap = resume(message, thread_id)
        _print_snapshot(f'after resume with "{message}"', snap)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(2)
    main(
        sys.argv[1],
        sys.argv[2] if len(sys.argv) > 2 else "fallback",
        sys.argv[3] if len(sys.argv) > 3 else None,
    )
