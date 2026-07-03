"""Evidence service: matching primitives, Evidence Graph construction, and the
evidence-first grounding validator.

Everything here is deterministic and LLM-free. It is used both to *build* the
Evidence Graph fallback and to *enforce* that findings/decisions reference real
evidence nodes (`system_flow.md` §7.3/§7.4/§7.6, Appendix A#3). Skill matching
is disclaimer-aware: a requirement the candidate mentions only while disclaiming
depth ("newer territory", "haven't…") is not counted as covered — this is what
lets the offline reasoner separate a strong candidate from a borderline one.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from backend.schemas.artifacts import (
    Decision,
    EvidenceGraph,
    EvidenceNode,
    EvidenceRef,
    EvidenceRelationship,
    Finding,
    Findings,
)
from backend.schemas.enums import EvidenceSourceType
from backend.schemas.meeting_package import MeetingPackage, TranscriptTurn

# Grammatical stop-words only — domain terms like "production"/"scale" are kept.
_STOP = {
    "and", "the", "for", "with", "of", "in", "to", "at", "a", "an", "on",
    "as", "is", "or", "by", "via", "using", "use", "your", "our",
}

# Cues that indicate the candidate is disclaiming depth on the matched topic.
_DISCLAIMER_CUES = (
    "haven't", "have not", "havent", "not production", "never went to production",
    "newer territory", "i admit", "haven't formalized", "haven't had to",
    "haven't worked much", "haven't designed", "haven't owned", "not a lot of",
    "know the terms but", "didn't really", "want to grow", "most want to grow",
    "newer to", "less experience", "prototyped", "hasn't", "wasn't", "no formal",
)


def tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def keywords(skill: str) -> list[str]:
    """Significant tokens from a skill/requirement string."""
    return [t for t in tokens(skill) if len(t) >= 3 and t not in _STOP]


def _tok_match(kw: str, hay: set[str]) -> bool:
    if kw in hay:
        return True
    if len(kw) >= 4:
        pre = kw[:4]
        return any(len(h) >= 4 and h[:4] == pre for h in hay)
    return False


def text_hits_skill(skill: str, text: str) -> bool:
    """True if at least half a requirement's keywords appear in ``text``."""
    ks = keywords(skill)
    if not ks:
        return False
    hay = set(tokens(text))
    hits = sum(1 for k in ks if _tok_match(k, hay))
    return hits >= max(1, (len(ks) + 1) // 2)


def has_disclaimer(text: str) -> bool:
    low = text.lower()
    return any(cue in low for cue in _DISCLAIMER_CUES)


def candidate_name(mp: MeetingPackage) -> str:
    return mp.payload.candidate.name


def candidate_turns(mp: MeetingPackage) -> list[TranscriptTurn]:
    name = candidate_name(mp)
    return [t for t in mp.transcript if t.speaker == name]


# --------------------------------------------------------------------------
# Skill coverage (the heart of the deterministic differentiation)
# --------------------------------------------------------------------------
@dataclass
class SkillCoverage:
    skill: str
    covered: bool
    mentioned: bool
    contradicted: bool
    support_ids: list[str] = field(default_factory=list)
    disclaimer_ids: list[str] = field(default_factory=list)


def _skills_haystack(mp: MeetingPackage) -> str:
    c = mp.payload.candidate
    return " ".join(c.skills + c.highlights + [c.current_title])


def assess_skill(mp: MeetingPackage, skill: str) -> SkillCoverage:
    """Classify how well the candidate covers one requirement.

    Covered when it appears in the candidate's skills/highlights, or in a
    transcript turn with no disclaimer *and* no walk-back elsewhere. A clean
    claim plus a disclaiming mention of the same skill is a contradiction.
    """
    skills_hit = text_hits_skill(skill, _skills_haystack(mp))
    clean_ids: list[str] = []
    disclaimer_ids: list[str] = []
    for turn in candidate_turns(mp):
        if text_hits_skill(skill, turn.text):
            if has_disclaimer(turn.text):
                disclaimer_ids.append(f"t{turn.turn_index}")
            else:
                clean_ids.append(f"t{turn.turn_index}")

    mentioned = bool(skills_hit or clean_ids or disclaimer_ids)
    contradicted = bool(clean_ids and disclaimer_ids)
    covered = bool(skills_hit or (clean_ids and not disclaimer_ids))

    support_ids: list[str] = []
    if skills_hit:
        support_ids.append("resume:skills")
    support_ids.extend(clean_ids if covered else [])
    return SkillCoverage(
        skill=skill,
        covered=covered,
        mentioned=mentioned,
        contradicted=contradicted,
        support_ids=support_ids or clean_ids or disclaimer_ids,
        disclaimer_ids=disclaimer_ids,
    )


def coverage_report(mp: MeetingPackage) -> list[SkillCoverage]:
    return [assess_skill(mp, s) for s in mp.payload.role.must_have_skills]


def coverage_ratio(report: list[SkillCoverage]) -> float:
    if not report:
        return 0.0
    return sum(1 for c in report if c.covered) / len(report)


# --------------------------------------------------------------------------
# Evidence Graph construction (deterministic fallback for the evidence node)
# --------------------------------------------------------------------------
def build_evidence_graph(mp: MeetingPackage) -> EvidenceGraph:
    nodes: list[EvidenceNode] = []
    rels: list[EvidenceRelationship] = []

    # Transcript — one node per candidate turn.
    for turn in candidate_turns(mp):
        nodes.append(
            EvidenceNode(
                id=f"t{turn.turn_index}",
                source_type=EvidenceSourceType.TRANSCRIPT,
                locator=f"transcript.turn[{turn.turn_index}]",
                content=turn.text,
            )
        )

    c = mp.payload.candidate
    nodes.append(EvidenceNode(id="resume:skills", source_type=EvidenceSourceType.RESUME,
                              locator="payload.candidate.skills", content=", ".join(c.skills)))
    nodes.append(EvidenceNode(id="resume:highlights", source_type=EvidenceSourceType.RESUME,
                              locator="payload.candidate.highlights", content=" | ".join(c.highlights)))

    tr = mp.payload.tracker
    nodes.append(EvidenceNode(id="tracker:record", source_type=EvidenceSourceType.TRACKER,
                              locator="payload.tracker",
                              content=f"{tr.current_stage} / {tr.status} (round {tr.interview_round})"))
    if tr.notes:
        nodes.append(EvidenceNode(id="notes:prev", source_type=EvidenceSourceType.INTERVIEW_NOTES,
                                  locator="payload.tracker.notes", content=tr.notes))

    for i, skill in enumerate(mp.payload.role.must_have_skills):
        nodes.append(EvidenceNode(id=f"jd:must:{i}", source_type=EvidenceSourceType.JOB_DESCRIPTION,
                                  locator=f"payload.role.must_have_skills[{i}]", content=skill))

    # Relationships: link supporting evidence to each must-have requirement.
    for i, cov in enumerate(coverage_report(mp)):
        for sid in cov.support_ids:
            rels.append(EvidenceRelationship(
                from_id=sid, to_id=f"jd:must:{i}",
                relation="supports" if cov.covered else "addresses"))

    return EvidenceGraph(
        nodes=nodes,
        relationships=rels,
        missing_sources=[EvidenceSourceType.RUBRIC],  # no rubric ships in the package
    )


# --------------------------------------------------------------------------
# Grounding enforcement (evidence-first)
# --------------------------------------------------------------------------
def evidence_ids(graph: EvidenceGraph) -> set[str]:
    return {n.id for n in graph.nodes}


def refs_grounded(refs: list[EvidenceRef], ids: set[str]) -> bool:
    return all(r.evidence_id in ids for r in refs)


def validate_findings_grounded(findings: Findings, graph: EvidenceGraph) -> None:
    """Raise if any substantive finding is ungrounded. Missing-info / open
    questions may be evidence-free (they are about *absence*)."""
    ids = evidence_ids(graph)
    grounded_groups: list[list[Finding]] = [
        findings.strengths, findings.weaknesses, findings.risks, findings.contradictions,
    ]
    for group in grounded_groups:
        for f in group:
            if not f.evidence_refs or not refs_grounded(f.evidence_refs, ids):
                raise ValueError(f"Ungrounded finding: {f.statement!r}")
    # Any refs that *are* supplied elsewhere must still point at real nodes.
    for group in (findings.missing_information, findings.open_questions):
        for f in group:
            if not refs_grounded(f.evidence_refs, ids):
                raise ValueError(f"Finding references unknown evidence: {f.statement!r}")


def validate_decision_grounded(decision: Decision, graph: EvidenceGraph) -> None:
    ids = evidence_ids(graph)
    if not decision.evidence_refs or not refs_grounded(decision.evidence_refs, ids):
        raise ValueError("Decision is not grounded in evidence")


# --------------------------------------------------------------------------
# Citation enrichment — attach the evidence node's content to each reference so
# citations are self-resolving (works for both LLM and deterministic output).
# --------------------------------------------------------------------------
def _truncate(text: str, limit: int = 140) -> str:
    text = " ".join((text or "").split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def quote_for(evidence_id: str, graph: EvidenceGraph) -> str | None:
    for node in graph.nodes:
        if node.id == evidence_id:
            return _truncate(node.content)
    return None


def _enrich_refs(refs: list[EvidenceRef], graph: EvidenceGraph) -> None:
    for ref in refs:
        if not ref.quote:
            quote = quote_for(ref.evidence_id, graph)
            if quote:
                ref.quote = quote


def enrich_evidence_quotes(ops) -> None:
    """Backfill ``EvidenceRef.quote`` from the Evidence Graph for every finding
    and the decision, in place, so citations carry concrete text."""
    graph = ops.evidence_graph
    f = ops.findings
    for group in (f.strengths, f.weaknesses, f.risks, f.contradictions,
                  f.missing_information, f.open_questions):
        for finding in group:
            _enrich_refs(finding.evidence_refs, graph)
    _enrich_refs(ops.decision.evidence_refs, graph)
