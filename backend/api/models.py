"""API request/response DTOs.

The workflow's own contracts (Approval Package, Execution Report) are reused
directly; these DTOs only wrap the transport surface.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from backend.schemas.approval_package import ApprovalPackage
from backend.schemas.execution import ExecutionReport

WAIT_FOR_HUMAN = "wait_for_human"


def _as_chat(messages: Any) -> list[dict]:
    out: list[dict] = []
    for m in messages or []:
        d = m.model_dump(mode="json") if hasattr(m, "model_dump") else dict(m)
        out.append({
            "role": d.get("role", "agent"),
            "content": d.get("content", ""),
            "kind": d.get("kind", "internal"),
        })
    return out


def _dump(obj: Any) -> dict | None:
    if obj is None:
        return None
    return obj.model_dump(mode="json") if hasattr(obj, "model_dump") else dict(obj)


class StartSessionRequest(BaseModel):
    meeting_package: dict[str, Any]


class MessageRequest(BaseModel):
    message: str


class SessionView(BaseModel):
    """Human-facing snapshot of a session returned by every hiring endpoint."""

    model_config = ConfigDict(extra="ignore")

    session_id: str
    meeting_id: str
    workflow_stage: str
    waiting_for_human: bool
    approval_package: ApprovalPackage | None = None
    execution_results: ExecutionReport | None = None
    # Read-only internal reasoning artifact, for the explainability panel (§11).
    operations_package: dict | None = None
    messages: list[dict] = Field(default_factory=list)

    @classmethod
    def from_result(cls, result: Any) -> "SessionView":
        values = result.values
        stage = values.get("workflow_stage")
        return cls(
            session_id=result.session_id,
            meeting_id=result.meeting_id,
            workflow_stage=str(stage) if stage is not None else "unknown",
            waiting_for_human=(tuple(result.next) == (WAIT_FOR_HUMAN,)),
            approval_package=values.get("approval_package"),
            execution_results=values.get("execution_results"),
            operations_package=_dump(values.get("operations_package")),
            messages=_as_chat(values.get("messages")),
        )


class LLMConfigView(BaseModel):
    """Masked, non-secret view of the effective LLM configuration.

    Never carries a key — only booleans for whether each provider's key is set.
    """

    model_config = ConfigDict(extra="ignore")

    mode: str
    provider: str
    ollama_model: str
    ollama_host: str
    azure_endpoint: str
    azure_deployment: str
    azure_api_version: str
    ollama_key_set: bool
    azure_key_set: bool


class LLMConfigUpdate(BaseModel):
    """Partial LLM-config change from the UI. All fields optional; a blank/omitted
    value leaves the current setting untouched (so a key need not be re-typed)."""

    model_config = ConfigDict(extra="ignore")

    mode: Literal["cloud", "fallback"] | None = None
    # "mock" = deterministic offline reasoner (maps to fallback mode); the cloud
    # providers are "ollama" and "azure_openai".
    provider: Literal["mock", "ollama", "azure_openai"] | None = None
    ollama_model: str | None = None
    ollama_host: str | None = None
    ollama_api_key: str | None = None
    azure_endpoint: str | None = None
    azure_deployment: str | None = None
    azure_api_version: str | None = None
    azure_api_key: str | None = None
