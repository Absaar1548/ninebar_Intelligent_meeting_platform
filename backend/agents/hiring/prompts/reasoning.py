"""Per-node prompt builders (one function per reasoning node).

Each returns the user prompt string; nodes pair it with ``base.SYSTEM_PROMPT``.
Upstream artifacts are embedded as JSON so the model builds on prior stages.
"""

from __future__ import annotations

from backend.agents.hiring.prompts.base import (
    build_user_prompt,
    candidate_block,
    role_block,
    transcript_text,
)
from backend.schemas.approval_package import ApprovalPackage
from backend.schemas.artifacts import (
    ActionPlan,
    Assessment,
    Decision,
    Drafts,
    EvidenceGraph,
    Findings,
    IntentClassification,
    InterviewContext,
)
from backend.schemas.meeting_package import MeetingPackage


def context_analysis_prompt(mp: MeetingPackage) -> str:
    return build_user_prompt(
        "Analyze the hiring context. Understanding only — no judgement, no "
        "decisions. Populate the structured interview context.",
        {
            "Meeting": f"{mp.metadata.title} ({mp.metadata.meeting_type})",
            "Role": role_block(mp),
            "Candidate": candidate_block(mp),
            "Interview": f"{mp.payload.interview.round_name}; focus: "
                         f"{', '.join(mp.payload.interview.focus_areas)}",
            "Tracker": f"{mp.payload.tracker.current_stage} / "
                       f"{mp.payload.tracker.status}; notes: {mp.payload.tracker.notes}",
        },
        InterviewContext,
    )


def evidence_graph_prompt(mp: MeetingPackage, ctx: InterviewContext) -> str:
    return build_user_prompt(
        "Construct an evidence graph relating the interview sources. Create "
        "referenceable evidence nodes (use ids like 't<turn_index>', "
        "'resume:skills', 'tracker:record', 'jd:must:<i>') and relationships. "
        "Record any absent sources (e.g. a scoring rubric) in missing_sources.",
        {
            "Interview Context": ctx.model_dump_json(),
            "Transcript": transcript_text(mp),
            "Resume skills": ", ".join(mp.payload.candidate.skills),
            "Role requirements": role_block(mp),
        },
        EvidenceGraph,
    )


def issue_identification_prompt(ctx: InterviewContext, graph: EvidenceGraph) -> str:
    return build_user_prompt(
        "Surface findings from the evidence graph: strengths, weaknesses, risks, "
        "contradictions, missing information, open questions. Every strength, "
        "weakness, risk, and contradiction MUST cite evidence_refs whose "
        "evidence_id exists in the graph. No decisions here.",
        {
            "Interview Context": ctx.model_dump_json(),
            "Evidence Graph": graph.model_dump_json(),
        },
        Findings,
    )


def operational_assessment_prompt(
    ctx: InterviewContext, findings: Findings, graph: EvidenceGraph
) -> str:
    return build_user_prompt(
        "Produce the hiring assessment (suitability, confidence 0-1, risk, "
        "escalation, blockers) from the findings and evidence. No actions.",
        {
            "Interview Context": ctx.model_dump_json(),
            "Findings": findings.model_dump_json(),
        },
        Assessment,
    )


def decision_synthesis_prompt(
    assessment: Assessment, findings: Findings, graph: EvidenceGraph
) -> str:
    return build_user_prompt(
        "Synthesize the hiring decision. Choose recommendation from the schema "
        "enum only. Provide reasoning and evidence_refs grounded in the graph.",
        {
            "Assessment": assessment.model_dump_json(),
            "Findings": findings.model_dump_json(),
            "Evidence Graph": graph.model_dump_json(),
        },
        Decision,
    )


def action_planning_prompt(
    decision: Decision, assessment: Assessment, ctx: InterviewContext
) -> str:
    return build_user_prompt(
        "Translate the decision into concrete operational tasks (action items). "
        "Use only the action-type enum values in the schema.",
        {
            "Decision": decision.model_dump_json(),
            "Assessment": assessment.model_dump_json(),
            "Interview Context": ctx.model_dump_json(),
        },
        ActionPlan,
    )


def draft_generation_prompt(
    action_plan: ActionPlan, decision: Decision, ctx: InterviewContext
) -> str:
    return build_user_prompt(
        "Generate the human-consumable draft communications: a candidate email "
        "and a tracker update proposal consistent with the action plan.",
        {
            "Action Plan": action_plan.model_dump_json(),
            "Decision": decision.model_dump_json(),
            "Interview Context": ctx.model_dump_json(),
        },
        Drafts,
    )


def intent_classification_prompt(message: str, approval_package: ApprovalPackage) -> str:
    return build_user_prompt(
        "Classify the human's message into exactly one supported workflow intent. "
        "Only operational intents are supported: 'approval' (approve/execute/"
        "proceed), 'modification' (change the recommendation, action items, "
        "tracker update, or email), or 'unsupported' (anything else). For a "
        "modification, set modification_target to the earliest affected node: "
        "'decision_synthesis' (recommendation), 'action_planning' (action/tracker), "
        "or 'draft_generation' (email). If a modification target cannot be "
        "resolved, classify as 'unsupported'.",
        {
            "Human message": message,
            "Current recommendation": approval_package.recommendation.value,
        },
        IntentClassification,
    )
