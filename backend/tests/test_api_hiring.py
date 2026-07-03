"""Hiring API — start / resume (approve, modify) / get, plus error handling."""

from __future__ import annotations

from backend.tests.conftest import meeting_dict

BASE = "/api/v1/agents/hiring"


def _start(client, name="strong"):
    r = client.post(f"{BASE}/sessions", json={"meeting_package": meeting_dict(name)})
    assert r.status_code == 200
    return r.json()


def test_start_returns_waiting_approval(api_client):
    d = _start(api_client)
    assert d["workflow_stage"] == "waiting_approval"
    assert d["waiting_for_human"] is True
    assert d["approval_package"]["recommendation"] == "move_forward"
    # internal reasoning artifact + chat transcript are exposed for the UI
    assert d["operations_package"] is not None
    assert d["operations_package"]["evidence_graph"]["nodes"]
    assert any(m["kind"] == "chat" for m in d["messages"])


def test_approve_completes_and_executes(api_client):
    sid = _start(api_client)["session_id"]
    r = api_client.post(f"{BASE}/sessions/{sid}/messages", json={"message": "approve all"})
    d = r.json()
    assert r.status_code == 200
    assert d["workflow_stage"] == "completed"
    assert d["waiting_for_human"] is False
    assert d["execution_results"]["status"] == "completed"


def test_modify_returns_to_waiting(api_client):
    sid = _start(api_client)["session_id"]
    d = api_client.post(
        f"{BASE}/sessions/{sid}/messages", json={"message": "rewrite the email"}
    ).json()
    assert d["workflow_stage"] == "waiting_approval"
    assert d["waiting_for_human"] is True


def test_get_session(api_client):
    sid = _start(api_client)["session_id"]
    r = api_client.get(f"{BASE}/sessions/{sid}")
    assert r.status_code == 200
    assert r.json()["session_id"] == sid


def test_malformed_meeting_package_422(api_client):
    r = api_client.post(f"{BASE}/sessions", json={"meeting_package": {"bad": 1}})
    assert r.status_code == 422


def test_unknown_session_404(api_client):
    r = api_client.post(f"{BASE}/sessions/nope/messages", json={"message": "approve"})
    assert r.status_code == 404
