"""The /mcp endpoint: tool listing and calls over streamable HTTP (JSON-RPC, stateless), with a fake
graph, plus one call against the live graph when FalkorDB is reachable (tunnel per docs/GRAPH.md)."""
from __future__ import annotations

import importlib
import json

import pytest

from tests.test_agent import MINT, fake_graph  # noqa: F401 - fixture

H = {"accept": "application/json, text/event-stream", "content-type": "application/json"}
EXPECTED = {"search_coins", "coin_dossier", "funding_trail", "siblings", "shared_snipers", "shared_handles",
            "ring", "connect", "top_operators", "memory_recall", "memory_note", "brain_ask"}


def rpc(c, method, params=None, i=1):
    r = c.post("/mcp", headers=H, json={"jsonrpc": "2.0", "id": i, "method": method, "params": params or {}})
    assert r.status_code == 200, r.text
    return r.json()


def init(c):
    return rpc(c, "initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                 "clientInfo": {"name": "test", "version": "0"}})


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("SNIFF_ENV_FILE", str(tmp_path / "app.env"))
    monkeypatch.setenv("SNIFF_LANDING_DIR", str(tmp_path))
    from fastapi.testclient import TestClient
    from app import mcp as sniff_mcp, secrets as s
    importlib.reload(s)
    from app import main
    importlib.reload(main)
    monkeypatch.setattr(sniff_mcp, "per_ip", sniff_mcp.Limiter(120, 3600))
    with TestClient(main.app, base_url="http://127.0.0.1:8080") as c:
        yield c


def test_mcp_lists_lineage_memory_and_brain_tools(client):
    assert init(client)["result"]["serverInfo"]["name"] == "sniff"
    listed = rpc(client, "tools/list", i=2)["result"]["tools"]
    assert {t["name"] for t in listed} == EXPECTED
    for t in listed:
        assert len(t["description"]) > 40 and t["inputSchema"]["type"] == "object"


def test_mcp_tool_call_returns_rows_and_evidence(client, fake_graph):  # noqa: F811
    out = rpc(client, "tools/call", {"name": "coin_dossier", "arguments": {"mint": MINT}}, i=3)["result"]
    assert not out.get("isError")
    data = out.get("structuredContent") or json.loads(out["content"][0]["text"])
    assert data["result"]["found"] is True and data["evidence"][0]["id"] == "E1"


def test_mcp_bad_input_is_a_tool_error_not_a_crash(client):
    out = rpc(client, "tools/call", {"name": "coin_dossier", "arguments": {"mint": "MATCH (n) DELETE n"}}, i=4)
    assert out["result"]["isError"] is True and "Solana address" in out["result"]["content"][0]["text"]


def test_mcp_rejects_foreign_hosts_and_is_rate_limited(client, monkeypatch):
    from app import mcp as sniff_mcp
    r = client.post("/mcp", headers={**H, "host": "evil.example"},
                    json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    assert r.status_code in (400, 421)
    monkeypatch.setattr(sniff_mcp, "per_ip", sniff_mcp.Limiter(2, 3600))
    codes = [client.post("/mcp", headers=H, json={"jsonrpc": "2.0", "id": i, "method": "tools/list"}).status_code
             for i in range(3)]
    assert codes[-1] == 429


def test_mcp_live_graph_call(client):
    from app.graph import read
    try:
        mint = read("MATCH (c:Coin) WHERE c.graduated RETURN c.mint AS m LIMIT 1")[0]["m"]
    except Exception as e:  # noqa: BLE001
        pytest.skip(f"FalkorDB not reachable: {e}")
    out = rpc(client, "tools/call", {"name": "coin_dossier", "arguments": {"mint": mint}}, i=5)["result"]
    data = out.get("structuredContent") or json.loads(out["content"][0]["text"])
    assert data["result"]["found"] is True and data["result"]["coin"]["mint"] == mint
    assert all(e["id"].startswith("E") for e in data["evidence"])
