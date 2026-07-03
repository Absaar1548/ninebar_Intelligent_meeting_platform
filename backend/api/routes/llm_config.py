"""LLM configuration router.

Thin HTTP adapter over ``LLMRuntime`` (backend owns the logic — §46). Lets the
UI read the effective LLM config and switch provider/mode/credentials at runtime.
Responses are masked (key booleans only); the raw key is never returned.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.api.models import LLMConfigUpdate, LLMConfigView
from backend.core.llm.runtime import LLMConfigError, get_llm_runtime

router = APIRouter(prefix="/api/v1/llm", tags=["llm"])


@router.get("/config", response_model=LLMConfigView)
def get_config() -> LLMConfigView:
    return LLMConfigView(**get_llm_runtime().snapshot())


@router.put("/config", response_model=LLMConfigView)
def update_config(body: LLMConfigUpdate) -> LLMConfigView:
    try:
        snapshot = get_llm_runtime().apply(body.model_dump(exclude_none=True))
    except LLMConfigError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return LLMConfigView(**snapshot)
