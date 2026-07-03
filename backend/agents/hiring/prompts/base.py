"""Prompt scaffolding shared by every reasoning node.

Each prompt embeds the target artifact's JSON Schema (so the model returns
schema-shaped output) and states the evidence-first + exact-enum rules. The
Phase 1 live smoke showed the model emits free-text enums ("Strong Hire")
unless constrained, so enum values are surfaced explicitly via the schema.
"""

from __future__ import annotations

import json
from typing import Mapping

from pydantic import BaseModel

from backend.schemas.meeting_package import MeetingPackage

SYSTEM_PROMPT = (
    "You are a Hiring Operations Agent: an evidence-first operational workflow "
    "engine, not a chatbot. You reason over structured interview context and "
    "ground every finding, decision, and action in concrete evidence. "
    "Return ONLY one JSON object that conforms to the provided JSON Schema. "
    "Use EXACTLY the enum values defined in the schema. Do not add prose, "
    "markdown, or fields outside the schema."
)


def schema_block(model_cls: type[BaseModel]) -> str:
    return json.dumps(model_cls.model_json_schema(), ensure_ascii=False)


def build_user_prompt(
    task: str, context: Mapping[str, str], model_cls: type[BaseModel]
) -> str:
    parts = [task, ""]
    for title, body in context.items():
        parts.append(f"## {title}\n{body}\n")
    parts.append("## Output JSON Schema\n" + schema_block(model_cls))
    parts.append("\nReturn ONLY the JSON object described by the schema.")
    return "\n".join(parts)


def transcript_text(mp: MeetingPackage) -> str:
    return "\n".join(
        f"[{t.turn_index}] {t.speaker}: {t.text}" for t in mp.transcript
    )


def role_block(mp: MeetingPackage) -> str:
    r = mp.payload.role
    return (
        f"Title: {r.title} ({r.level}) @ {r.company}\n"
        f"Must-have skills: {', '.join(r.must_have_skills)}\n"
        f"Nice-to-have skills: {', '.join(r.nice_to_have_skills)}\n"
        f"JD highlights: {', '.join(r.jd_highlights)}"
    )


def candidate_block(mp: MeetingPackage) -> str:
    c = mp.payload.candidate
    return (
        f"Name: {c.name} — {c.current_title} @ {c.current_company}\n"
        f"Experience: {c.years_experience} years\n"
        f"Skills: {', '.join(c.skills)}\n"
        f"Highlights: {' | '.join(c.highlights)}"
    )
