"""Rendering — artifacts → Markdown views for the UI.

Two surfaces:
- ``render_agent_recommendation`` — the human-facing recommendation the agent
  posts **in chat** (from the Approval Package, the source of truth).
- ``render_internal`` — the read-only **Internal Processing & Memory** panel
  (from the Operations Package + the reasoning trace + workflow stage).

Markdown produced here is a *view*; the JSON artifacts remain authoritative.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from backend.core.common.config import get_settings
from backend.schemas.approval_package import ApprovalPackage
from backend.schemas.execution import ExecutionReport
from backend.schemas.operations_package import OperationsPackage


@lru_cache
def _env() -> Environment:
    templates_dir = get_settings().data_dir / "templates"
    return Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(enabled_extensions=(), default=False),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def _as_dict(obj: Any) -> dict:
    if hasattr(obj, "model_dump"):
        return obj.model_dump(mode="json")
    return dict(obj)


def _trunc(text: str, limit: int) -> str:
    text = " ".join((text or "").split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def render_agent_recommendation(approval_package: ApprovalPackage | dict) -> str:
    """The agent's chat message presenting its recommendation (§8.2 fields)."""
    ap = _as_dict(approval_package)
    return _env().get_template("agent_recommendation.md.j2").render(ap=ap).strip()


def render_execution_markdown(report: ExecutionReport | dict | None) -> str:
    if report is None:
        return ""
    return _env().get_template("execution.md.j2").render(report=_as_dict(report)).strip()


_FINDING_GROUPS = [
    ("Strengths", "strengths"),
    ("Weaknesses", "weaknesses"),
    ("Risks", "risks"),
    ("Contradictions", "contradictions"),
    ("Missing information", "missing_information"),
    ("Open questions", "open_questions"),
]


def render_internal(
    operations_package: OperationsPackage | dict | None,
    trace: list[str] | None,
    stage: str,
) -> str:
    """The Internal Processing & Memory panel (reasoning trace + Ops Package)."""
    lines: list[str] = [f"**Workflow stage:** `{stage}`", ""]

    if trace:
        lines.append("### Processing trace")
        lines += [f"{i}. {step}" for i, step in enumerate(trace, 1)]
        lines.append("")

    if operations_package is None:
        lines.append("_Reasoning artifacts appear once the pipeline runs._")
        return "\n".join(lines).strip()

    ops = _as_dict(operations_package)

    a = ops.get("assessment") or {}
    lines.append("### Assessment")
    lines.append(f"- **Suitability:** {a.get('suitability', '—')}")
    lines.append(f"- **Confidence:** {float(a.get('confidence', 0)) * 100:.0f}%")
    risk = f"- **Risk:** {a.get('risk', '—')}"
    if a.get("escalation"):
        risk += " · escalation flagged"
    lines.append(risk)
    if a.get("blockers"):
        lines.append(f"- **Unmet must-haves:** {', '.join(a['blockers'])}")
    lines.append("")

    findings = ops.get("findings") or {}
    lines.append("### Findings")
    wrote = False
    for label, key in _FINDING_GROUPS:
        items = findings.get(key) or []
        if not items:
            continue
        wrote = True
        lines.append(f"**{label}**")
        for item in items:
            cites = ", ".join(r["evidence_id"] for r in (item.get("evidence_refs") or []))
            suffix = f" — _{cites}_" if cites else ""
            lines.append(f"- {item.get('statement', '')}{suffix}")
        lines.append("")
    if not wrote:
        lines += ["_No findings._", ""]

    graph = ops.get("evidence_graph") or {}
    nodes = graph.get("nodes") or []
    rels = graph.get("relationships") or []
    lines.append(f"### Evidence graph ({len(nodes)} nodes, {len(rels)} links)")
    for node in nodes:
        lines.append(
            f"- `{node.get('id')}` _{node.get('source_type')}_ — "
            f"{_trunc(node.get('content', ''), 120)}"
        )
    if graph.get("missing_sources"):
        lines += ["", f"_Missing sources:_ {', '.join(graph['missing_sources'])}"]

    return "\n".join(lines).strip()
