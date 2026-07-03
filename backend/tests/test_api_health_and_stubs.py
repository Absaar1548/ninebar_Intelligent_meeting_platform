"""Health endpoint + pluggability: unimplemented agent routers return 501."""

from __future__ import annotations

import pytest


def test_health_ok(api_client):
    r = api_client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@pytest.mark.parametrize("agent", ["engineering", "sales", "customer_success"])
def test_stub_agents_not_implemented(api_client, agent):
    r = api_client.post(f"/api/v1/agents/{agent}/sessions")
    assert r.status_code == 501
