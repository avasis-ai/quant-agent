"""Tool layer, evidence contract and agent loop, with a fake graph and a fake Claude (no network)."""
from __future__ import annotations

import asyncio
import importlib
from types import SimpleNamespace

import pytest

from app import agent, queries, tools

MINT = "DLTiLKB7wuNcXQKkY5SUJkUDME7bsV1Ax8574xZ7pump"
OTHER = "CMK7aMHNUv5pfAMYzhrJWovCBHqzsNwXpAzW6nXBpump"
CREATOR = "CaPwA4gndht45xSCMz7Sq8KuUGjq2W7JWe3mGj3UEpRw"
FUNDER = "691nRgyAFfPbEGFUhf6uS3sg1jJjhxgCFuokf3jvvkcy"
HUB = "2uRy4qE7DZnvqhsKFkx2J3tjSFwfttdYcYGAG5WDVsrA"


def coin(mint, i, **p):
    return {"id": i, "labels": ["Coin"], "mint": mint, "name": "Dog", "symbol": "DOG", "graduated": False,
            "created_at": 1760000000, "mcap_2m": 1.5, **p}


def wallet(addr, i, labels=("Wallet",), **p):
    return {"id": i, "labels": list(labels), "addr": addr, "launches": 3, **p}


def path():
    return {"nodes": [wallet(HUB, 9, labels=("Hub",), degree=900), wallet(FUNDER, 2), wallet(CREATOR, 1)],
            "edges": [{"id": 50, "type": "FUNDED", "src": 9, "dst": 2, "sol": 1.23456, "at": 1},
                      {"id": 51, "type": "FUNDED", "src": 2, "dst": 1, "sol": 0.5, "at": 2}]}


@pytest.fixture()
def fake_graph(monkeypatch):
    monkeypatch.setattr(queries, "coin_dossier", lambda m: None if m != MINT else {
        "coin": coin(MINT, 10), "creator": wallet(CREATOR, 1), "others": 4, "other_grads": 0,
        "recent": [coin(OTHER, 11)], "ring": {"id": 70, "labels": ["Ring"], "rid": 7, "creators": 12, "coins": 40,
                                             "graduations": 0},
        "funders": [{"funder": FUNDER, "hub": False, "sol": 0.5, "at": 2},
                    {"funder": HUB, "hub": True, "sol": 2.0, "at": 1}]})
    monkeypatch.setattr(queries, "funding_trail", lambda a: [{"p": path(), "depth": 2, "hub": True}])
    monkeypatch.setattr(queries, "siblings", lambda m: [{"funder": FUNDER, "creators": 5, "coins": 9, "graduated": 0}])
    monkeypatch.setattr(queries, "shared_handles", lambda m: [])
    monkeypatch.setattr(queries, "shared_snipers", lambda m: [
        {"mint": OTHER, "name": "Cat", "graduated": False, "shared": 3, "score": 7.123456}])
    monkeypatch.setattr(tools, "_BASE", {"coins": 1000, "graduated": 10, "rate": 0.01})


def test_path_serialization_uses_stable_keys():
    p = tools.compact_path(path())
    assert [n["key"] for n in p["nodes"]] == [f"hub:{HUB}", f"wallet:{FUNDER}", f"wallet:{CREATOR}"]
    assert p["edges"][0] == {"type": "FUNDED", "src": f"hub:{HUB}", "dst": f"wallet:{FUNDER}", "at": 1, "sol": 1.2346}
    assert all("id" not in n for n in p["nodes"])  # FalkorDB internal ids never leak


def test_evidence_ids_are_sequential_and_deduplicated():
    ev = tools.Evidence()
    a = tools._coin(MINT)
    e1 = ev.add("x", {}, "one", [a])
    e2 = ev.add("y", {}, "two", [a])
    again = ev.add("x", {"other": "args"}, "same nodes, same tool", [a])
    assert (e1, e2, again) == ("E1", "E2", "E1")
    assert [i["id"] for i in ev.items] == ["E1", "E2"]


def test_every_evidence_item_has_the_contract_fields(fake_graph):
    ev = tools.Evidence()
    for name, args in [("coin_dossier", {"mint": MINT}), ("funding_trail", {"address": CREATOR}),
                       ("siblings", {"mint": MINT}), ("shared_snipers", {"mint": MINT})]:
        res, ok = tools.run_tool(ev, name, args)
        assert ok, res
    keys = {"id", "tool", "args", "summary", "nodes", "edges"}
    for item in ev.items:
        assert keys <= item.keys()
        assert item["nodes"] and all(n["key"].split(":", 1)[0] in {"coin", "wallet", "hub", "handle", "ring"}
                                     for n in item["nodes"])
        node_keys = {n["key"] for n in item["nodes"]}
        assert all(e["src"] in node_keys and e["dst"] in node_keys for e in item["edges"])


def test_hubs_are_marked_and_end_trails(fake_graph):
    ev = tools.Evidence()
    res, _ = tools.run_tool(ev, "funding_trail", {"address": CREATOR})
    assert res["rows"][0]["from_is_hub"] is True
    assert "hub" in ev.items[0]["summary"]
    d, _ = tools.run_tool(ev, "coin_dossier", {"mint": MINT})
    assert [f["label"] for f in d["funders"]] == ["Wallet", "Hub"]


def test_bad_input_is_a_readable_error_not_a_crash(fake_graph):
    res, ok = tools.run_tool(tools.Evidence(), "coin_dossier", {"mint": "not a mint; MATCH (n) DELETE n"})
    assert not ok and "Solana address" in res["error"]
    res, ok = tools.run_tool(tools.Evidence(), "nope", {})
    assert not ok


def test_cap_trims_rows_to_fit():
    big = {"rows": [{"x": "y" * 500} for _ in range(40)]}
    out = tools.cap(big, 3000)
    assert len(out) <= 3000 and '"truncated"' in out


def test_citations_unknown_ids_are_removed():
    ev = tools.Evidence()
    ev.add("x", {}, "one", [tools._coin(MINT)])
    text, cited, unknown = agent.check_citations("Creator made 4 coins [E1]. Made up [E9].", ev)
    assert cited == ["E1"] and unknown == ["E9"] and "[E9]" not in text and "[E1]" in text


def collect(gen):
    async def run():
        return [e async for e in gen]
    return asyncio.run(run())


def test_dossier_fallback_without_a_key(fake_graph, monkeypatch):
    monkeypatch.setattr(agent.ai, "client_for", lambda k: (None, None, "none"))
    events = collect(agent.investigate("who made this?", MINT))
    assert events[0]["mode"] == "dossier"
    verdict = next(e for e in events if e["type"] == "verdict")
    assert verdict["cited"] and not verdict["unknown_cited"]
    assert "History, not a prediction." in verdict["text"]
    for word in ("buy", "sell", "scam"):
        assert word not in verdict["text"].lower().replace("buyers", "")


class FakeClaude:
    """Asks for coin_dossier, then answers citing E1 and a made-up E99."""

    def __init__(self):
        self.calls = []
        self.messages = SimpleNamespace(create=self.create)

    async def create(self, **kw):
        self.calls.append(kw)
        if len(self.calls) == 1:
            block = SimpleNamespace(type="tool_use", id="tu1", name="coin_dossier", input={"mint": MINT},
                                    model_dump=lambda **_: {"type": "tool_use", "id": "tu1", "name": "coin_dossier",
                                                            "input": {"mint": MINT}})
            return SimpleNamespace(content=[block], stop_reason="tool_use")
        text = SimpleNamespace(type="text", text="The creator launched 4 other coins, none graduated [E1]. Also [E99].")
        return SimpleNamespace(content=[text], stop_reason="end_turn")


def test_agent_loop_runs_tools_and_verifies_citations(fake_graph, monkeypatch):
    fake = FakeClaude()
    monkeypatch.setattr(agent.ai, "client_for", lambda k: (fake, "claude-sonnet-5-5", "owner"))
    events = collect(agent.investigate("who is behind this coin?", MINT))
    steps = [e for e in events if e["type"] == "step"]
    assert [s["tool"] for s in steps] == ["coin_dossier"] and steps[0]["evidence"][0] == "E1"
    verdict = next(e for e in events if e["type"] == "verdict")
    assert verdict["mode"] == "agent" and verdict["cited"] == ["E1"] and verdict["unknown_cited"] == ["E99"]
    sent = fake.calls[1]["messages"][-1]["content"][0]
    assert sent["type"] == "tool_result" and sent["tool_use_id"] == "tu1" and '"E1"' in sent["content"]
    assert "1.0%" in fake.calls[0]["system"][0]["text"]  # base-rate line is in the prompt


def test_agent_falls_back_when_the_ai_call_fails(fake_graph, monkeypatch):
    async def boom(**_):
        raise RuntimeError("down")
    broken = SimpleNamespace(messages=SimpleNamespace(create=boom))
    monkeypatch.setattr(agent.ai, "client_for", lambda k: (broken, "m", "owner"))
    events = collect(agent.investigate("x", MINT))
    assert any(e["type"] == "notice" for e in events)
    assert next(e for e in events if e["type"] == "verdict")["mode"] == "dossier"


@pytest.fixture()
def client(tmp_path, monkeypatch, fake_graph):
    monkeypatch.setenv("SNIFF_ENV_FILE", str(tmp_path / "app.env"))
    monkeypatch.setenv("SNIFF_LANDING_DIR", str(tmp_path))
    from fastapi.testclient import TestClient
    from app import secrets as s
    importlib.reload(s)
    from app import main
    importlib.reload(main)
    monkeypatch.setattr(main.ai, "client_for", lambda k: (None, None, "none"))
    with TestClient(main.app, base_url="http://127.0.0.1:8080") as c:
        yield c


def test_ask_route_json(client):
    r = client.post("/api/ask", json={"question": "who?", "mint": MINT})
    assert r.status_code == 200
    body = r.json()
    assert body["mode"] == "dossier" and body["steps"] and body["evidence"] and body["verdict"]["cited"]


def test_ask_route_sse(client):
    r = client.post("/api/ask", json={"question": "who?", "mint": MINT}, headers={"accept": "text/event-stream"})
    assert r.status_code == 200 and "event: verdict" in r.text and "event: done" in r.text


def test_ask_route_rejects_bad_input_and_foreign_origin(client):
    assert client.post("/api/ask", json={"question": ""}).status_code == 400
    assert client.post("/api/ask", json={"question": "x", "mint": "abc"}).status_code == 400
    assert client.post("/api/ask", json={"question": "x", "mint": MINT},
                       headers={"origin": "https://evil.example"}).status_code == 403


def test_ask_route_is_rate_limited(client):
    codes = [client.post("/api/ask", json={"question": "x", "mint": MINT}).status_code for _ in range(62)]
    assert codes[-1] == 429 and codes[0] == 200
