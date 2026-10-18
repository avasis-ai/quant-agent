"""Real FalkorDB integration, isolated embedded graphs (optional developer dependency).

    uv pip install -r requirements-dev.txt falkordblite==0.10.0
    pytest tests/test_tracks_falkor.py

No demo-box connection, credentials or deployment is involved.
"""
from __future__ import annotations

import asyncio
import copy
import json
import uuid

import pytest

from app import agent, brain, knowledge_graph as kg, memory, queries, tools
from app.privacy import PrivacyError
from build import brain as builder
from tests.test_agent import MINT, CREATOR, fake_graph, client  # noqa: F401 - fixtures
from tests.test_mcp import H, init, rpc
from tests.test_tracks import sample_corpus


def data_for(result):
    assert not result.get("isError"), result
    return result.get("structuredContent") or json.loads(result["content"][0]["text"])


@pytest.fixture(scope="module")
def embedded(tmp_path_factory):
    redislite = pytest.importorskip("redislite", reason="optional: install falkordblite==0.10.0 for real Cypher tests")
    db = redislite.FalkorDB(str(tmp_path_factory.mktemp("falkor") / "graphs.rdb"))
    yield db
    db.client.shutdown()


@pytest.fixture()
def real_graph(embedded, monkeypatch):
    suffix = uuid.uuid4().hex[:12]
    monkeypatch.setattr(kg, "graph", lambda name: embedded.select_graph(name + "_" + suffix))
    monkeypatch.setattr(kg, "_ready", set())
    return embedded


def persist_sample(sid=None):
    ctx = memory.begin(sid, entity="coin:" + MINT)
    ev = tools.Evidence(memory=ctx)
    ev.add("coin_dossier", {"mint": MINT}, "The creator launched 4 other coins.",
           [tools._coin(MINT), tools._wallet(CREATOR)], [{"src": "wallet:" + CREATOR, "dst": "coin:" + MINT, "type": "CREATED"}])
    result = {"found": True, "evidence": ["E1"]}
    assert memory.remember(ctx, "coin_dossier", {"mint": MINT}, result, ev.items)
    return ctx, ev


def test_real_memory_paths_indexes_aggregate_and_wallet_references(real_graph):
    ctx, _ = persist_sample()
    assert ctx.available
    rows = kg.read("memory", "MATCH (s:Session)-[:ASKED]->(q:Question)-[:FOUND]->(e:Evidence)-[:ABOUT]->(c:Coin) "
                   "RETURN s.sid AS sid, e.tool AS tool, c.mint AS mint, e.at AS at")
    assert rows[0]["sid"] == ctx.sid and rows[0]["mint"] == MINT and rows[0]["at"] > 0
    session = memory.recall(session=ctx.sid)
    assert {e["type"] for e in session["graph"]["edges"]} == {"ASKED", "FOUND", "ABOUT"}
    assert memory.recall(entity="wallet:" + CREATOR)["rows"]
    aggregate = memory.recall(entity="coin:" + MINT)
    assert aggregate["rows"][0]["sessions"] == 1
    assert ctx.sid not in json.dumps(aggregate) and ctx.qid not in json.dumps(aggregate)
    indexes = kg.read("memory", "CALL db.indexes() YIELD label, properties RETURN label, properties")
    assert any(r["label"] == "Coin" and "mint" in r["properties"] for r in indexes)


def test_cache_remaps_ids_preserves_tool_provenance_and_is_session_scoped(real_graph):
    ctx, _ = persist_sample()
    target = tools.Evidence()
    target.add("shared_handles", {}, "No reused socials.", [tools._coin(MINT)])
    result = memory.cached(memory.begin(ctx.sid), "coin_dossier", {"mint": MINT}, target)
    assert result["recalled"] and result["evidence"] == ["E2"]
    assert target.items[1]["tool"] == "coin_dossier" and target.items[1]["memory"]["at"]
    assert memory.cached(memory.begin(None), "coin_dossier", {"mint": MINT}, tools.Evidence()) is None
    _, cited, _, mismatched = agent.check_citations("No reused socials [E2].", target)
    assert not cited and mismatched == ["E2"]


def test_repeated_recall_keeps_original_time_and_expires_without_refreshing(real_graph, monkeypatch):
    now = [1000]
    monkeypatch.setattr(memory.time, "time", lambda: now[0])
    ctx, _ = persist_sample()
    now[0] = 1200
    followup = memory.begin(ctx.sid)
    ev = tools.Evidence(memory=followup)
    reused = memory.cached(followup, "coin_dossier", {"mint": MINT}, ev)
    assert reused["recorded_at"] == 1000
    memory.remember(followup, "coin_dossier", {"mint": MINT}, reused, ev.items)
    assert {r["at"] for r in memory.recall(entity="coin:" + MINT)["rows"]} == {1000}
    now[0] = 4601
    assert memory.cached(memory.begin(ctx.sid), "coin_dossier", {"mint": MINT}, tools.Evidence()) is None


def test_latest_coin_is_deterministic_even_within_one_second(real_graph, monkeypatch):
    from tests.test_agent import OTHER
    monkeypatch.setattr(memory.time, "time", lambda: 1000)
    first = memory.begin(None, entity="coin:" + MINT)
    memory.begin(first.sid, entity="coin:" + OTHER)
    assert memory.latest_entity(first.sid) == "coin:" + OTHER


def test_coordination_note_requires_public_text_and_real_entity_evidence(real_graph):
    ctx, _ = persist_sample()
    eid = memory.recall(session=ctx.sid)["rows"][0]["id"]
    note = memory.note("coin:" + MINT, "quantbase-trading-agent", "Reviewed public launch history; no performance prediction.", [eid])
    recalled = memory.recall(entity="coin:" + MINT)
    assert recalled["notes"][0]["by"] == "quantbase-trading-agent"
    assert recalled["notes"][0]["evidence_ids"] == [eid] and "unverified" in recalled["notes"][0]["status"]
    assert any(edge["type"] == "SUPPORTS" for edge in recalled["graph"]["edges"])
    assert note["id"]
    with pytest.raises(PrivacyError):
        memory.note("coin:" + MINT, "another-agent", "Contact person@example.org")
    with pytest.raises(ValueError, match="must exist"):
        memory.note("coin:" + MINT, "another-agent", "Unverified note.", ["a" * 32])
    assert kg.read("memory", "MATCH (n:Note) RETURN count(n) AS n")[0]["n"] == 1


def test_memory_rejects_pii_call_as_a_whole_before_evidence_writes(real_graph):
    ctx = memory.begin(None)
    ev = tools.Evidence()
    ev.add("coin_dossier", {"mint": MINT}, "Public history.", [tools._coin(MINT)])
    ev.add("shared_handles", {"mint": MINT}, "Contact person@example.org", [tools._coin(MINT)])
    with pytest.raises(PrivacyError):
        memory.remember(ctx, "coin_dossier", {"mint": MINT}, {"found": True}, ev.items)
    assert kg.read("memory", "MATCH (n:Evidence) RETURN count(n) AS n")[0]["n"] == 0


def test_api_followup_without_mint_reuses_evidence_and_never_saves_question(real_graph, client, monkeypatch):
    first = client.post("/api/ask", json={"question": "Contact person@example.org about this coin", "mint": MINT})
    assert first.status_code == 200 and first.json()["memory_available"]
    sid = first.json()["session_id"]
    assert first.cookies["sniff_session"] == sid
    assert "HttpOnly" in first.headers["set-cookie"]
    def forbidden(*_a, **_k):
        pytest.fail("Follow-up must reuse memory rather than re-querying lineage")
    for name in ("coin_dossier", "siblings", "shared_handles", "shared_snipers"):
        monkeypatch.setattr(queries, name, forbidden)
    second = client.post("/api/ask", json={"question": "And what did we learn?"})
    assert second.status_code == 200
    data = second.json()
    assert data["session_id"] == sid and data["verdict"]["cited"]
    assert all(item.get("memory") for item in data["evidence"])
    saved = kg.read("memory", "MATCH (q:Question) RETURN q.text AS text")
    assert all(row["text"] == "Public graph investigation" for row in saved)
    assert "person@" not in json.dumps(kg.read("memory", "MATCH (n) RETURN properties(n) AS p"))


def test_coin_name_search_does_not_persist_visitor_question_in_evidence_arguments(real_graph, client, monkeypatch):
    from tests.test_agent import coin
    monkeypatch.setattr(tools, "read", lambda *_a, **_k: [{"node": coin(MINT, 10)}])
    question = "Who made this Dog"
    response = client.post("/api/ask", json={"question": question})
    assert response.status_code == 200 and response.json()["memory_available"]
    assert response.json()["verdict"]["cited"]
    stored = json.dumps(kg.read("memory", "MATCH (n) RETURN properties(n) AS p"))
    assert question not in stored and "Public coin Dog returned by coin search." in stored


def test_mcp_second_agent_reads_and_adds_a_note_to_first_agent_findings(real_graph, client):
    init(client)
    called = rpc(client, "tools/call", {"name": "coin_dossier", "arguments": {"mint": MINT}})["result"]
    data = data_for(called)
    assert data["memory_available"] and data["session_id"]
    recall = data_for(rpc(client, "tools/call", {"name": "memory_recall", "arguments": {"entity": "coin:" + MINT}})["result"])
    assert recall["result"]["rows"] and data["session_id"] not in json.dumps(recall["result"])
    note = rpc(client, "tools/call", {"name": "memory_note", "arguments": {"entity": "coin:" + MINT, "by": "quantbase-agent", "text": "Trading agent reviewed the public evidence."}})["result"]
    assert not note.get("isError")
    assert memory.recall(entity="coin:" + MINT)["notes"][0]["by"] == "quantbase-agent"
    bad = rpc(client, "tools/call", {"name": "memory_note", "arguments": {"entity": "coin:" + MINT, "by": "quantbase-agent", "text": "Email person@example.org"}})["result"]
    assert bad["isError"] and "person@" not in json.dumps(bad)


def test_memory_recall_hydrates_original_citable_evidence_and_records_it(real_graph):
    persist_sample()
    ctx = memory.begin(None)
    ev = tools.Evidence(memory=ctx)
    result, ok = tools.run_tool(ev, "memory_recall", {"entity": "coin:" + MINT})
    assert ok and result["rows"][0]["evidence"] == "E1"
    assert "payload" not in result["rows"][0]
    assert ev.items[0]["tool"] == "coin_dossier" and ev.items[0]["edges"][0]["type"] == "CREATED"
    assert agent.check_citations("The creator launched 4 other coins [E1].", ev)[1] == ["E1"]
    assert memory.recall(session=ctx.sid)["rows"][0]["tool"] == "coin_dossier"


def test_real_brain_load_rerun_paths_fulltext_and_source_citations(real_graph):
    corpus = sample_corpus()
    section = corpus["documents"][0]["sections"][0]
    section["entities"], section["relations"] = builder.validate_extraction(section, {
        "entities": [{"kind": "Product", "name": "QuantBase", "quote": "QuantBase uses paper mode."},
                     {"kind": "Feature", "name": "paper mode", "quote": "QuantBase uses paper mode."}],
        "relations": [{"from": "paper mode", "to": "QuantBase", "type": "PART_OF", "quote": "QuantBase uses paper mode."}]})
    assert builder.load(corpus) == {"documents": 1, "sections": 1}
    count = kg.read("brain", "MATCH (n) RETURN count(n) AS n")[0]["n"]
    builder.load(corpus)
    assert kg.read("brain", "MATCH (n) RETURN count(n) AS n")[0]["n"] == count
    result = brain.ask("How does QuantBase handle paper vs live?")
    assert result["cited"] == ["B1"] and result["sources"][0]["text"] == section["text"]
    assert {e["type"] for e in result["graph"]["edges"]} >= {"PART_OF", "MENTIONS"}
    assert brain.check_citations(result["answer"], result["evidence"])[1] == result["cited"]
    assert brain.status()["public_only"]


def test_changed_brain_sections_and_relationships_stop_being_retrieved(real_graph):
    corpus = sample_corpus()
    section = corpus["documents"][0]["sections"][0]
    section["entities"], section["relations"] = builder.validate_extraction(section, {
        "entities": [{"kind": "Product", "name": "QuantBase", "quote": "QuantBase uses paper mode."},
                     {"kind": "Feature", "name": "paper mode", "quote": "QuantBase uses paper mode."}],
        "relations": [{"from": "paper mode", "to": "QuantBase", "type": "PART_OF", "quote": "QuantBase uses paper mode."}]})
    builder.load(corpus)
    assert kg.read("brain", "MATCH (:Entity)-[r:PART_OF]->(:Entity) RETURN count(r) AS n")[0]["n"] == 1
    updated = copy.deepcopy(corpus)
    current = updated["documents"][0]["sections"][0]
    current.update(sid=builder.ident("updated"), text="Refunds follow the public terms.", entities=[], relations=[])
    builder.load(updated)
    assert kg.read("brain", "MATCH (:Entity)-[r:PART_OF]->(:Entity) RETURN count(r) AS n")[0]["n"] == 0
    assert brain.ask("paper mode")["cited"] == []
    assert brain.ask("refunds")["sources"][0]["section_id"] == current["sid"]


def test_multiple_brain_calls_do_not_collide_or_allow_cross_source_citations(real_graph):
    corpus = sample_corpus()
    other = copy.deepcopy(corpus["documents"][0]["sections"][0])
    other.update(sid=builder.ident("refunds"), title="Refunds", text="Refunds follow the public terms.", entities=[], relations=[])
    corpus["documents"][0]["sections"].append(other)
    builder.load(corpus)
    ev = tools.Evidence()
    first, ok = tools.run_tool(ev, "brain_ask", {"question": "paper mode"})
    assert ok and first["cited"] == ["B1"]
    second, ok = tools.run_tool(ev, "brain_ask", {"question": "refunds"})
    assert ok and second["cited"] == ["B2"]
    assert {e["id"] for e in ev.items} == {"B1", "B2"}
    cleaned, cited, _, mismatched = agent.check_citations("Guaranteed profits [B1]. Refunds follow the public terms [B2].", ev)
    assert cited == ["B2"] and mismatched == ["B1"] and "Guaranteed" not in cleaned


def test_brain_pages_api_and_agent_work_without_ai_key(real_graph, client):
    builder.load(sample_corpus())
    for page in ("memory", "brain"):
        response = client.get("/" + page)
        assert response.status_code == 200 and "QuantBase" in response.text and "/track-assets/tracks.js" in response.text
    response = client.post("/api/brain/ask", json={"question": "How does QuantBase handle paper vs live?"})
    assert response.status_code == 200 and response.json()["cited"] == ["B1"]
    assert client.post("/api/brain/ask", json={"question": ""}).status_code == 400
    assert client.post("/api/brain/ask", json={"question": "paper"}, headers={"origin": "https://evil.example"}).status_code == 403
    # A company question must not inherit the mint from an earlier coin investigation.
    client.post("/api/ask", json={"question": "Who made this?", "mint": MINT})
    asked = client.post("/api/ask", json={"question": "How does QuantBase handle paper vs live?"}).json()
    assert asked["mode"] == "brain" and asked["verdict"]["cited"] == ["B1"]
    init(client)
    mcp = rpc(client, "tools/call", {"name": "brain_ask", "arguments": {"question": "paper mode"}})["result"]
    assert data_for(mcp)["result"]["cited"] == ["B1"]
