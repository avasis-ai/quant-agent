"""Anonymous visitors use the existing shared-key path, with a mocked Claude and graph."""
from __future__ import annotations

import importlib
import json

import pytest
from fastapi.testclient import TestClient

from app import ai, memory
from app.limits import Limiter
from test_agent import FakeClaude, MINT, fake_graph  # reuse the established graph/tool fixtures


@pytest.fixture()
def shared_client(tmp_path, monkeypatch, fake_graph):
    monkeypatch.setenv("SNIFF_ENV_FILE", str(tmp_path / "app.env"))
    from app import secrets, main
    importlib.reload(secrets)
    importlib.reload(main)
    fake = FakeClaude()
    owner = ai.Owner(key="fixture-shared-key", model="fixture-claude", client=fake)
    monkeypatch.setattr(ai, "OWNER", owner)
    monkeypatch.setattr(ai, "load_owner", lambda: None)
    # Keep this contract test independent of any local memory server.
    monkeypatch.setattr(memory, "begin", lambda sid, *_: memory.Investigation(memory.session_id(sid), "fixture", available=False))
    with TestClient(main.app, base_url="http://127.0.0.1:8080") as client:
        yield client, fake, main


def test_anonymous_shared_key_runs_claude_tools_and_citations_over_sse(shared_client, caplog):
    client, fake, _ = shared_client
    status = client.get("/api/settings/status")
    assert status.json() == {"admin": False, "owner": {"active": True, "model": "fixture-claude"}}
    response = client.post("/api/ask", json={"mint": MINT, "question": "Who is behind this coin?"}, headers={"accept": "text/event-stream"})
    assert response.status_code == 200
    events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith("data: ")]
    assert events[0]["mode"] == "agent" and events[0]["using"] == "owner"
    assert next(event for event in events if event["type"] == "step")["tool"] == "coin_dossier"
    verdict = next(event for event in events if event["type"] == "verdict")
    assert verdict["mode"] == "agent" and verdict["cited"] == ["E1"]
    assert "4 other coins" in verdict["text"] and "[E1]" in verdict["text"]
    assert len(fake.calls) == 2
    assert "fixture-shared-key" not in status.text + response.text + caplog.text
    assert response.cookies.get("sniff_session")


def test_anonymous_shared_key_keeps_existing_hourly_cap(shared_client, monkeypatch):
    client, _, main = shared_client
    monkeypatch.setattr(main, "ask_owner_limit", Limiter(1, 3600))
    assert client.post("/api/ask", json={"mint": MINT, "question": "Who is behind this coin?"}).status_code == 200
    assert client.post("/api/ask", json={"mint": MINT, "question": "Who is behind this coin?"}).status_code == 429


def test_anonymous_shared_key_keeps_existing_daily_cap(shared_client, monkeypatch):
    client, _, main = shared_client
    daily = Limiter(1, 86400)
    assert daily.allow("all")
    monkeypatch.setattr(main, "ask_owner_daily", daily)
    response = client.post("/api/ask", json={"mint": MINT, "question": "Who is behind this coin?"})
    assert response.status_code == 429 and "busy today" in response.json()["error"]
