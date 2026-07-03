"""Node: Issue Identification (§7.4). Findings only — no decisions. Evidence-
first is enforced: ungrounded findings trigger a regenerate (Appendix A#3)."""

from __future__ import annotations

from backend.agents.hiring.nodes.base import get_llm_client, with_message
from backend.agents.hiring.prompts.base import SYSTEM_PROMPT
from backend.agents.hiring.prompts.reasoning import issue_identification_prompt
from backend.agents.hiring.services.evidence import validate_findings_grounded
from backend.agents.hiring.services.fallbacks import fallback_findings
from backend.schemas.artifacts import Findings
from backend.schemas.enums import WorkflowStage
from backend.schemas.workflow_state import WorkflowState


def issue_identification_node(state: WorkflowState) -> dict:
    mp = state["meeting_package"]
    ctx = state["interview_context"]
    graph = state["evidence_graph"]
    findings = get_llm_client().generate_structured(
        issue_identification_prompt(ctx, graph),
        Findings,
        system=SYSTEM_PROMPT,
        fallback_fn=lambda: fallback_findings(mp, graph),
        validate=lambda f: validate_findings_grounded(f, graph),
    )
    return with_message(
        state,
        {"findings": findings, "workflow_stage": WorkflowStage.ISSUES_IDENTIFIED},
        f"Identified {len(findings.strengths)} strength(s) and "
        f"{len(findings.weaknesses)} gap(s).",
    )
