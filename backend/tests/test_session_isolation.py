"""Two Meeting Packages processed close together never share state (§14.2)."""

from __future__ import annotations

from backend.tests.conftest import meeting_dict

BASE = "/api/v1/agents/hiring"


def _start(client, name):
    return client.post(f"{BASE}/sessions", json={"meeting_package": meeting_dict(name)}).json()


def test_two_sessions_are_independent(api_client):
    strong = _start(api_client, "strong")
    border = _start(api_client, "borderline")

    assert strong["session_id"] != border["session_id"]
    assert strong["approval_package"]["recommendation"] == "move_forward"
    assert border["approval_package"]["recommendation"] != "move_forward"

    listed = api_client.get(f"{BASE}/sessions").json()
    assert len(listed) == 2

    # Approving one does not affect the other.
    api_client.post(f"{BASE}/sessions/{border['session_id']}/messages",
                    json={"message": "approve"})
    still = api_client.get(f"{BASE}/sessions/{strong['session_id']}").json()
    assert still["workflow_stage"] == "waiting_approval"
