import importlib
import logging
import os
import stat

import pytest
from fastapi.testclient import TestClient

FAKE = "sk-ant-api03-" + "x" * 40 + "ABCD"
VISITOR = "sk-ant-api03-" + "v" * 40 + "WXYZ"


@pytest.fixture()
def client(tmp_path, monkeypatch, caplog):
    env = tmp_path / "app.env"
    monkeypatch.setenv("SNIFF_ENV_FILE", str(env))
    monkeypatch.setenv("SNIFF_LANDING_DIR", str(tmp_path))
    from app import secrets as s
    importlib.reload(s)
    s.write_env({"ADMIN_PASSCODE_HASH": s.hash_passcode("open-sesame-123")})
    from app import ai, main
    importlib.reload(ai)
    importlib.reload(main)

    async def fake_check(key):
        if key.strip() not in (FAKE, VISITOR):
            raise ai.KeyError_("Anthropic did not accept that key.")
        return "claude-sonnet-5-5"

    monkeypatch.setattr(ai, "check_key", fake_check)
    caplog.set_level(logging.INFO)
    with TestClient(main.app, base_url="http://127.0.0.1:8080") as c:
        c.env = env
        yield c


def test_owner_key_needs_passcode(client):
    r = client.post("/api/settings/owner-key", json={"key": FAKE})
    assert r.status_code == 401


def test_wrong_passcode(client):
    assert client.post("/api/settings/login", json={"passcode": "nope"}).status_code == 401


def test_login_limited(client):
    codes = [client.post("/api/settings/login", json={"passcode": "nope"}).status_code for _ in range(6)]
    assert codes[-1] == 429


def test_activate_and_remove(client, caplog):
    assert client.post("/api/settings/login", json={"passcode": "open-sesame-123"}).status_code == 200
    r = client.post("/api/settings/owner-key", json={"key": FAKE})
    assert r.status_code == 200
    body = r.text
    assert FAKE not in body and r.json()["owner"] == {"active": True, "model": "claude-sonnet-5-5", "last4": "…ABCD"}
    # stored with mode 600, the key itself never logged
    assert stat.S_IMODE(os.stat(client.env).st_mode) == 0o600
    assert f"ANTHROPIC_API_KEY={FAKE}" in client.env.read_text()
    assert FAKE not in caplog.text
    # anyone can see it is active, only the owner sees the last 4
    anon = TestClient(client.app, base_url="http://127.0.0.1:8080")
    assert anon.get("/api/settings/status").json()["owner"] == {"active": True, "model": "claude-sonnet-5-5"}
    r = client.delete("/api/settings/owner-key")
    assert r.json()["owner"]["active"] is False
    assert "ANTHROPIC_API_KEY" not in client.env.read_text()


def test_bad_owner_key(client):
    client.post("/api/settings/login", json={"passcode": "open-sesame-123"})
    r = client.post("/api/settings/owner-key", json={"key": "sk-ant-wrong-" + "y" * 40})
    assert r.status_code == 400 and "sk-ant" not in r.text


def test_visitor_key_never_stored(client, caplog):
    r = client.post("/api/settings/visitor-check", headers={"x-anthropic-key": VISITOR})
    assert r.status_code == 200 and VISITOR not in r.text
    assert VISITOR not in client.env.read_text()
    assert VISITOR not in caplog.text


def test_cross_origin_refused(client):
    r = client.post("/api/settings/login", json={"passcode": "open-sesame-123"}, headers={"origin": "https://evil.example"})
    assert r.status_code == 403


def test_mask():
    from app.secrets import mask
    assert mask(f"key={FAKE} done") == "key=sk-ant-…ABCD done"
