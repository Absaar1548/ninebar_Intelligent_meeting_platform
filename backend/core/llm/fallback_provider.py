"""Deterministic fallback helpers.

The fallback is a *mechanism*, not domain reasoning: each Phase 2 node supplies
its own deterministic ``fallback_fn``. This module provides the generic scaffold
those functions and tests reuse — most importantly ``minimal_valid_instance``,
which builds a schema-valid instance of any Pydantic model with no LLM and no
network.
"""

from __future__ import annotations

import types
from datetime import date, datetime
from enum import Enum
from typing import Any, Literal, Union, get_args, get_origin

from pydantic import BaseModel

from backend.schemas._time import utcnow

_NoneType = type(None)


def _default_for_annotation(annotation: Any) -> Any:
    """Best-effort schema-valid default value for a type annotation."""
    origin = get_origin(annotation)
    args = get_args(annotation)

    # Optional / Union (both typing.Union and X | Y syntax)
    if origin is Union or origin is types.UnionType:
        if _NoneType in args:
            return None
        return _default_for_annotation(args[0])

    if origin in (list, set, tuple, frozenset):
        return []
    if origin is dict:
        return {}
    if origin is Literal:
        return args[0]

    if isinstance(annotation, type):
        if issubclass(annotation, BaseModel):
            return minimal_valid_instance(annotation)
        if issubclass(annotation, Enum):
            return next(iter(annotation))
        if issubclass(annotation, bool):
            return False
        if issubclass(annotation, int):
            return 0
        if issubclass(annotation, float):
            return 0.0
        if issubclass(annotation, str):
            return ""
        if issubclass(annotation, datetime):
            return utcnow()
        if issubclass(annotation, date):
            return date.today()

    return None


def minimal_valid_instance(model_cls: type[BaseModel]) -> BaseModel:
    """Construct a minimal schema-valid instance of ``model_cls``.

    Only required fields are populated (with type-appropriate zero values);
    optional fields keep their declared defaults. Nested models recurse.
    """
    data: dict[str, Any] = {}
    for name, field in model_cls.model_fields.items():
        if field.is_required():
            data[name] = _default_for_annotation(field.annotation)
    return model_cls.model_validate(data)
