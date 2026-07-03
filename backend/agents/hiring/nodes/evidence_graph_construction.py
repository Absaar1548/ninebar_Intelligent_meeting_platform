"""Node: Evidence Graph Construction (§7.3). Relationship construction, not
retrieval. Absent sources are recorded as missing, not failed (Appendix A#2)."""

from __future__ import annotations

from backend.agents.hiring.nodes.base import get_llm_client, with_message
from backend.agents.hiring.prompts.base import SYSTEM_PROMPT
from backend.agents.hiring.prompts.reasoning import evidence_graph_prompt
from backend.agents.hiring.services.fallbacks import fallback_evidence_graph
from backend.schemas.artifacts import EvidenceGraph
from backend.schemas.enums import WorkflowStage
from backend.schemas.workflow_state import WorkflowState


def evidence_graph_construction_node(state: WorkflowState) -> dict:
    mp = state["meeting_package"]
    ctx = state["interview_context"]
    graph = get_llm_client().generate_structured(
        evidence_graph_prompt(mp, ctx),
        EvidenceGraph,
        system=SYSTEM_PROMPT,
        fallback_fn=lambda: fallback_evidence_graph(mp),
    )
    return with_message(
        state,
        {"evidence_graph": graph, "workflow_stage": WorkflowStage.EVIDENCE_CONSTRUCTED},
        f"Constructed the evidence graph ({len(graph.nodes)} nodes).",
    )
