"""JSON read/write helpers with atomic writes and Pydantic (de)serialization.

Runtime artifacts (Operations/Approval packages, logs) are persisted as JSON.
``write_json`` writes to a temp file and atomically replaces the target so a
reader never observes a half-written file.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel

_M = TypeVar("_M", bound=BaseModel)


def read_json(path: str | Path) -> Any:
    """Load and parse a JSON file."""
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: str | Path, data: Any, *, indent: int = 2) -> Path:
    """Atomically write ``data`` as JSON to ``path`` (temp file + replace)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=indent, ensure_ascii=False, default=str)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)
    return path


def load_model(path: str | Path, model_cls: type[_M]) -> _M:
    """Load a JSON file and validate it into ``model_cls``."""
    return model_cls.model_validate(read_json(path))


def dump_model(path: str | Path, model: BaseModel, *, indent: int = 2) -> Path:
    """Serialize a Pydantic model to JSON at ``path`` (atomic)."""
    return write_json(path, model.model_dump(mode="json"), indent=indent)
