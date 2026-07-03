"""Test fixtures.

Forces the whole suite to run offline (`LLM_MODE=fallback`) so no test touches
the network, and gives each test a fresh compiled graph (fresh checkpointer).
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.agents.hiring.nodes import set_llm_client
from backend.agents.hiring.workflow import reset_hiring_app
from backend.core.common.config import REPO_ROOT, Settings
from backend.core.common.json_io import read_json
from backend.core.llm.client import LLMClient
from backend.schemas.meeting_package import MeetingPackage

FIXTURES = REPO_ROOT / "data" / "fixtures" / "meeting_packages"


@pytest.fixture(autouse=True)
def offline_llm():
    set_llm_client(LLMClient(settings=Settings(llm_mode="fallback")))
    reset_hiring_app()
    yield
    set_llm_client(None)
    reset_hiring_app()


@pytest.fixture
def api_client() -> TestClient:
    from backend.api.main import create_app

    return TestClient(create_app(enable_watcher=False))


def load_meeting(name: str) -> MeetingPackage:
    return MeetingPackage.model_validate(read_json(FIXTURES / f"meeting_package_{name}.json"))


def meeting_dict(name: str) -> dict:
    return read_json(FIXTURES / f"meeting_package_{name}.json")
