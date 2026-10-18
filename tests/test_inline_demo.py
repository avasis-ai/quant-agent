"""Input identity regressions: a fresh coin must never inherit the previous coin."""
import asyncio

import pytest

from app import agent, memory, resolve, tools
from test_agent import MINT, OTHER, fake_graph  # noqa: F401
from test_qb_shared_key import shared_client  # noqa: F401


@pytest.fixture()
def search(monkeypatch):
    calls = []
    coins = [
        {"mint": OTHER, "name": "Cat", "symbol": "CAT"},
        {"mint": MINT, "name": "Subprime Cat", "symbol": "SPCAT", "evidence": "E1"},
    ]
    def run(ev, name, args):
        calls.append((name, args))
        if name == "coin_dossier":
            return {"found": args["mint"] == MINT, "coin": coins[1]}, True
        return {"rows": coins}, True
    monkeypatch.setattr(tools, "run_tool", run)
    return calls


@pytest.mark.parametrize("text", ["Subprime Cat", "$SPCAT", "Who funded the creator of Subprime Cat?", "What is the funding ring behind $SPCAT?"])
def test_resolves_names_tickers_and_questions_without_picking_partial_match(search, text):
    result = resolve.resolve(text)
    assert result["status"] == "found" and result["coin"]["mint"] == MINT
    assert "evidence" not in result["coin"]
    assert result["question"] == (text if "?" in text else resolve.DEFAULT_QUESTION)


def test_mint_is_checked_against_snapshot(search):
    assert resolve.resolve(MINT)["coin"]["mint"] == MINT
    missing = resolve.resolve(OTHER)
    assert missing["status"] == "missing" and "ends 14 Oct 2026" in missing["message"]
    assert search[-1][0] == "coin_dossier"


def test_unknown_coin_does_not_resolve_to_partial_search_results(search):
    result = resolve.resolve("Totally Unknown Launch")
    assert result["status"] == "missing" and result["coin"] is None


def test_search_outage_is_not_reported_as_absent(monkeypatch):
    monkeypatch.setattr(tools, "run_tool", lambda *_: ({"error": "down"}, False))
    assert resolve.resolve("Subprime Cat")["status"] == "error"


def test_generic_followup_can_remain_a_question(search):
    assert resolve.resolve("Who funded its creator?")["status"] == "question"
    assert search == []


@pytest.mark.parametrize("question,expected", [("Subprime Cat", None), ("Who funded Subprime Cat?", None), ("Who funded its creator?", MINT), ("And what did we learn?", MINT)])
def test_session_coin_reuse_is_limited_to_explicit_followups(monkeypatch, question, expected):
    ctx = memory.Investigation(memory.session_id(None), "fixture", available=True)
    monkeypatch.setattr(memory, "begin", lambda *_: ctx)
    monkeypatch.setattr(memory, "recall", lambda **_: {})
    monkeypatch.setattr(memory, "latest_entity", lambda *_: "coin:" + MINT)
    received = []
    async def investigate(question, mint, *_):
        received.append(mint)
        yield {"type": "done"}
    monkeypatch.setattr(agent, "_investigate", investigate)
    async def collect():
        return [event async for event in agent.investigate(question)]
    asyncio.run(collect())
    assert received == [expected]


def test_resolve_endpoint_uses_existing_lookup_rate_limit(shared_client, monkeypatch):
    from app.limits import Limiter
    client, _, main = shared_client
    monkeypatch.setattr(main.resolve, "resolve", lambda q: {"status": "found", "coin": {"mint": MINT}, "question": q})
    monkeypatch.setattr(main, "lookup_limit", Limiter(1, 3600))
    assert client.get("/api/resolve", params={"q": "Subprime Cat"}).json()["coin"]["mint"] == MINT
    assert client.get("/api/resolve", params={"q": "Higher"}).status_code == 429


def test_exact_name_wins_over_a_different_coin_with_the_same_ticker(monkeypatch):
    rows = [{"mint": OTHER, "name": "methuselah", "symbol": "METHU"}, {"mint": MINT, "name": "METHU", "symbol": "METHU"}]
    monkeypatch.setattr(tools, "run_tool", lambda *_: ({"rows": rows}, True))
    result = resolve.resolve("Who funded METHU?")
    assert result["coin"]["mint"] == MINT
    assert len(result["rows"]) == 2 and result["note"]


def test_coin_late_in_a_long_question_is_not_dropped_by_four_word_search(monkeypatch):
    calls = []
    def search(ev, tool, args):
        calls.append(args["query"])
        return {"rows": [{"mint": MINT, "name": "Subprime Cat", "symbol": "SPCAT"}] if "Subprime" in args["query"] else []}, True
    monkeypatch.setattr(tools, "run_tool", search)
    question = "Do you see any evidence suggesting Subprime Cat reused a funding ring?"
    result = resolve.resolve(question)
    assert result["coin"]["mint"] == MINT and result["question"] == question
    assert len(calls) > 1
