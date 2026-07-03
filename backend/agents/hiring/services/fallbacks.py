"""Deterministic, LLM-free reasoners — one per reasoning node.

Each function reconstructs a schema-valid, evidence-grounded artifact from the
Meeting Package and upstream artifacts using rule-based skill-coverage scoring
(`services/evidence.py`). These are the ``fallback_fn`` callables the reasoning
nodes hand to ``LLMClient.generate_structured``; in ``LLM_MODE=fallback`` they
*are* the pipeline. Recommendation thresholds live here and are tunable.
"""

from __future__ import annotations

from backend.agents.hiring.services import evidence as ev
from backend.schemas.artifacts import (
    ActionItem,
    ActionPlan,
    Assessment,
    Decision,
    DraftEmail,
    Drafts,
    EvidenceGraph,
    EvidenceRef,
    Finding,
    Findings,
    InterviewContext,
    TrackerUpdateProposal,
)
from backend.schemas.enums import ActionType, Recommendation
from backend.schemas.meeting_package import MeetingPackage

# --- recommendation thresholds (single tunable place) ---------------------
T_MOVE_FORWARD = 0.70
T_ADDITIONAL_INTERVIEW = 0.45
T_HOLD = 0.25


def recommend(ratio: float) -> Recommendation:
    if ratio >= T_MOVE_FORWARD:
        return Recommendation.MOVE_FORWARD
    if ratio >= T_ADDITIONAL_INTERVIEW:
        return Recommendation.ADDITIONAL_INTERVIEW
    if ratio >= T_HOLD:
        return Recommendation.HOLD
    return Recommendation.REJECT


def _confidence(ratio: float) -> float:
    return round(0.40 + 0.55 * ratio, 2)


def _refs(ids: list[str]) -> list[EvidenceRef]:
    seen: list[str] = []
    for i in ids:
        if i not in seen:
            seen.append(i)
    return [EvidenceRef(evidence_id=i) for i in seen]


# --------------------------------------------------------------------------
def fallback_interview_context(mp: MeetingPackage) -> InterviewContext:
    p = mp.payload
    return InterviewContext(
        interview_stage=p.interview.round_name,
        candidate_name=p.candidate.name,
        candidate_title=p.candidate.current_title,
        role_title=p.role.title,
        role_level=p.role.level,
        meeting_objective=mp.metadata.title,
        historical_context=p.tracker.notes,
        tracker_state=f"{p.tracker.current_stage} / {p.tracker.status}",
        focus_areas=list(p.interview.focus_areas),
    )


def fallback_evidence_graph(mp: MeetingPackage) -> EvidenceGraph:
    return ev.build_evidence_graph(mp)


def fallback_findings(mp: MeetingPackage, graph: EvidenceGraph) -> Findings:
    report = ev.coverage_report(mp)
    strengths: list[Finding] = []
    weaknesses: list[Finding] = []
    contradictions: list[Finding] = []
    missing: list[Finding] = []
    risks: list[Finding] = []

    for i, cov in enumerate(report):
        jd_ref = _refs([f"jd:must:{i}"])
        if cov.covered:
            strengths.append(Finding(
                statement=f"Strong, evidence-backed depth in {cov.skill}.",
                evidence_refs=_refs(cov.support_ids)))
        elif cov.mentioned:
            weaknesses.append(Finding(
                statement=f"Limited demonstrated depth in {cov.skill}.",
                evidence_refs=_refs(cov.disclaimer_ids or cov.support_ids)))
        else:
            missing.append(Finding(
                statement=f"No interview evidence for required skill: {cov.skill}.",
                evidence_refs=jd_ref))
        if cov.contradicted:
            contradictions.append(Finding(
                statement=f"Claimed {cov.skill} but later walked it back.",
                evidence_refs=_refs(cov.support_ids + cov.disclaimer_ids)))

    ratio = ev.coverage_ratio(report)
    if ratio < 0.5 and report:
        risks.append(Finding(
            statement="Majority of core requirements are not yet evidenced.",
            evidence_refs=_refs([f"jd:must:{i}" for i, c in enumerate(report) if not c.covered][:1])))
    if mp.payload.tracker.notes and "up-level" in mp.payload.tracker.notes.lower():
        risks.append(Finding(
            statement="Candidate is applying up-level; leadership scope is unproven.",
            evidence_refs=_refs(["notes:prev"])))
    if mp.payload.role.level.lower() == "lead" and mp.payload.candidate.years_experience < 5:
        risks.append(Finding(
            statement=f"Only {mp.payload.candidate.years_experience} years' experience for a Lead role.",
            evidence_refs=_refs(["tracker:record"])))

    open_qs: list[Finding] = []
    for nice in mp.payload.role.nice_to_have_skills:
        if not ev.assess_skill(mp, nice).covered:
            open_qs.append(Finding(statement=f"Clarify depth in nice-to-have: {nice}."))
    missing.append(Finding(statement="No scoring rubric was provided in the Meeting Package."))

    return Findings(
        strengths=strengths, weaknesses=weaknesses, risks=risks,
        contradictions=contradictions, missing_information=missing,
        open_questions=open_qs,
    )


def fallback_assessment(mp: MeetingPackage, findings: Findings, graph: EvidenceGraph) -> Assessment:
    report = ev.coverage_report(mp)
    ratio = ev.coverage_ratio(report)
    if ratio >= T_MOVE_FORWARD:
        suitability, risk = "Strong fit for the role", "low"
    elif ratio >= T_ADDITIONAL_INTERVIEW:
        suitability, risk = "Partial fit; targeted gaps remain", "medium"
    elif ratio >= T_HOLD:
        suitability, risk = "Limited fit; core requirements unproven", "high"
    else:
        suitability, risk = "Weak fit for the role", "high"
    return Assessment(
        suitability=suitability,
        confidence=_confidence(ratio),
        risk=risk,
        escalation=ratio < 0.5,
        blockers=[c.skill for c in report if not c.covered],
    )


def fallback_decision(mp: MeetingPackage, assessment: Assessment,
                      findings: Findings, graph: EvidenceGraph) -> Decision:
    report = ev.coverage_report(mp)
    ratio = ev.coverage_ratio(report)
    rec = recommend(ratio)
    covered = [c for c in report if c.covered]
    n_cov, n_tot = len(covered), len(report)

    grounding: list[str] = []
    for c in covered:
        grounding.extend(c.support_ids)
    if not grounding:  # ground a negative decision on the unmet requirements
        grounding = [f"jd:must:{i}" for i in range(len(report))]

    alt = {
        Recommendation.MOVE_FORWARD: [Recommendation.ADDITIONAL_INTERVIEW],
        Recommendation.ADDITIONAL_INTERVIEW: [Recommendation.HOLD, Recommendation.MOVE_FORWARD],
        Recommendation.HOLD: [Recommendation.ADDITIONAL_INTERVIEW, Recommendation.REJECT],
        Recommendation.REJECT: [Recommendation.HOLD],
    }[rec]

    return Decision(
        recommendation=rec,
        alternatives=alt,
        confidence=_confidence(ratio),
        reasoning=(f"{n_cov}/{n_tot} must-have requirements are evidenced "
                   f"({assessment.suitability.lower()}). Recommendation: "
                   f"{rec.value.replace('_', ' ')}."),
        evidence_refs=_refs(grounding),
    )


def fallback_action_plan(mp: MeetingPackage, decision: Decision) -> ActionPlan:
    tr = mp.payload.tracker
    name = mp.payload.candidate.name
    next_stage = mp.payload.interview.next_stage or "Hiring Manager / Final Round"
    d_refs = list(decision.evidence_refs)

    items = [ActionItem(type=ActionType.TRACKER_UPDATE,
                        description=f"Record R{tr.interview_round} outcome for {name}.",
                        target=tr.candidate_id, evidence_refs=d_refs)]
    rec = decision.recommendation
    if rec == Recommendation.MOVE_FORWARD:
        items += [
            ActionItem(type=ActionType.NOTIFY_HIRING_MANAGER,
                       description="Notify hiring manager of a strong pass.", target="Hiring Manager"),
            ActionItem(type=ActionType.SCHEDULE_INTERVIEW,
                       description=f"Schedule {next_stage}.", target=name),
            ActionItem(type=ActionType.CANDIDATE_EMAIL,
                       description="Send advancement email to the candidate.", target=name),
        ]
    elif rec == Recommendation.ADDITIONAL_INTERVIEW:
        items += [
            ActionItem(type=ActionType.NOTIFY_HIRING_MANAGER,
                       description="Flag unproven areas for calibration.", target="Hiring Manager"),
            ActionItem(type=ActionType.SCHEDULE_INTERVIEW,
                       description="Schedule a focused follow-up on the gaps.", target=name),
        ]
    elif rec == Recommendation.HOLD:
        items.append(ActionItem(type=ActionType.NOTIFY_HIRING_MANAGER,
                                description="Discuss hold / pipeline calibration.", target="Hiring Manager"))
    else:  # REJECT
        items.append(ActionItem(type=ActionType.CANDIDATE_EMAIL,
                                description="Send a respectful rejection.", target=name))
    return ActionPlan(items=items)


def fallback_drafts(mp: MeetingPackage, decision: Decision, action_plan: ActionPlan) -> Drafts:
    name = mp.payload.candidate.name
    role = mp.payload.role.title
    rec = decision.recommendation
    next_stage = mp.payload.interview.next_stage or "the next round"

    if rec == Recommendation.MOVE_FORWARD:
        subject = f"Great news on your {role} interview"
        body = (f"Hi {name},\n\nThank you for the round-{mp.payload.tracker.interview_round} "
                f"conversation. We were impressed and would like to move you forward to "
                f"{next_stage}. We'll follow up shortly with scheduling.\n\nBest regards,\nNorthwind AI")
        status = "Advanced"
    elif rec == Recommendation.ADDITIONAL_INTERVIEW:
        subject = f"Next steps on your {role} interview"
        body = (f"Hi {name},\n\nThanks for the recent conversation. We'd like to schedule a short "
                f"additional session to go deeper on a couple of areas before a final decision.\n\n"
                f"Best regards,\nNorthwind AI")
        status = "Additional Interview"
    elif rec == Recommendation.HOLD:
        subject = f"Update on your {role} application"
        body = (f"Hi {name},\n\nThank you for your time. We're completing our review and will be "
                f"in touch with next steps soon.\n\nBest regards,\nNorthwind AI")
        status = "On Hold"
    else:
        subject = f"Update on your {role} application"
        body = (f"Hi {name},\n\nThank you for interviewing with us. After careful consideration we "
                f"won't be moving forward at this time. We appreciated the conversation and wish you "
                f"the best.\n\nBest regards,\nNorthwind AI")
        status = "Rejected"

    proposal = TrackerUpdateProposal(
        candidate_id=mp.payload.tracker.candidate_id,
        summary=f"R{mp.payload.tracker.interview_round} → {rec.value.replace('_', ' ')}",
        changes={"status": status,
                 "current_stage": next_stage if rec == Recommendation.MOVE_FORWARD
                 else mp.payload.tracker.current_stage},
    )
    return Drafts(draft_email=DraftEmail(to=name, subject=subject, body=body),
                  tracker_update_proposal=proposal)
