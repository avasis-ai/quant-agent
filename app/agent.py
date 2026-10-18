"""The Sniff agent: Claude plans which graph tools to call, calls them, then writes a short verdict
that cites evidence ids. Without a working AI key it falls back to a fixed dossier built from the
same tools, so the evidence never depends on the LLM.

investigate() is an async generator of events, so the route can stream them (SSE) or collect them:
  {"type": "start", "mode": "agent"|"dossier", "model": ...}
  {"type": "step", "tool": ..., "input": {...}, "ok": bool, "ms": int, "evidence": [ids]}
  {"type": "evidence", "items": [...]}          all evidence gathered, once, before the verdict
  {"type": "verdict", "text": ..., "cited": [ids], "unknown_cited": [ids], "mismatched_cited": [ids], "mode": ...}
  {"type": "done", "ms": int}
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from typing import Any, AsyncIterator

from . import ai, tools, memory

log = logging.getLogger("sniff.agent")

MAX_TOOL_TURNS = 8
MAX_TOKENS = 1200
CITE = re.compile(r"\[([EB]\d+)\]")
MINT_IN_TEXT = re.compile(r"\b[1-9A-HJ-NP-Za-km-z]{32,44}\b")
COMPANY_QUESTION = re.compile(r"\b(quantbase|paper\s+(?:vs|versus|and)|company\s+(?:brain|polic)|privacy\s+polic)\b", re.I)

SYSTEM = """You are Sniff, an investigator for pump.fun meme coins on Solana. You answer from a graph of
public on-chain history: coins, the wallets that created them, who funded those wallets, early buyers
(snipers), shared socials, and funding rings. Use the tools; never guess a fact the tools did not return.

How to work:
- Memory is recalled before this turn. Reuse same-session evidence before querying lineage again;
  memory_recall(entity='coin:<mint>' or 'wallet:<address>') shows anonymised findings from others.
  Agent notes are unverified observations with self-declared provenance, never established facts.
- For questions about QuantBase's products, policies, research or paper vs live, use brain_ask.
  Quote its source excerpt exactly and cite [B1], [B2], etc. B citations must match the source text.
  They describe public knowledge, not coin lineage.
- Given a coin, start with coin_dossier. Then follow the strongest lead: siblings (same funder),
  shared_handles, shared_snipers, ring, funding_trail. Use search_coins when you only have a name.
- A hub (a funder of more than 200 wallets, likely an exchange) proves nothing. Never treat two things
  as linked because they share a hub.
- Stop when you have enough; you have at most 8 tool calls.

How to answer (plain words, for traders, no jargon):
- One short paragraph of 2 to 5 plain sentences (never more than 5; pick the strongest facts first), then the closing line. No bullets, lists, headings or bold.
- One claim per sentence, and each sentence ends with the id of the evidence that proves THAT claim, like
  [E2]. Cite the tool that found it: socials and websites -> shared_handles; early buyers -> shared_snipers;
  who funded whom, and other creators paid by the same funder -> coin_dossier, funding_trail or siblings;
  rings -> ring or coin_dossier; links between two things -> connect. Never cite an id for a claim it does
  not show. A tool that found nothing returns a 'none found' evidence id: cite that for a "no ..." sentence.
- Describe history only. Never say buy, sell, safe, scam, rug, or what the price will do. Say "no links found"
  rather than "clean" when the tools find nothing. If asked to predict, say Sniff only shows history.
- End with exactly this line: {base_line}"""


def base_line() -> str:
    try:
        b = tools.base_rate()
        pct = f"{100 * b['rate']:.1f}%"
        return f"For context: {pct} of the {b['coins']:,} pump.fun launches in this graph graduated. History, not a prediction."
    except Exception:  # noqa: BLE001
        return "History, not a prediction."


def _ids_in(result: Any) -> list[str]:
    found = re.findall(r'"([EB]\d+)"', json.dumps(result, default=str))
    return list(dict.fromkeys(found))


# A sentence about one of these topics may only cite evidence from the tools that can show it.
# Sentences about nothing in particular ("launched 72 coins") may cite any real evidence.
TOPICS: list[tuple[re.Pattern, set[str]]] = [
    (re.compile(r"\b(socials?|twitter|telegram|websites?|site|handles?|x account)\b", re.I), {"shared_handles"}),
    (re.compile(r"\b(early buyers?|snipers?|sniped|bought early)\b", re.I), {"shared_snipers"}),
    (re.compile(r"\brings?\b", re.I), {"ring", "coin_dossier"}),
    (re.compile(r"\b(fund(ed|er|ers|ing|s)?|paid|pays|hubs?|exchange)\b", re.I),
     {"coin_dossier", "funding_trail", "siblings", "top_operators", "connect", "ring"}),
    (re.compile(r"\b(linked|links?|connected|hops?|path)\b", re.I),
     {"connect", "coin_dossier", "funding_trail", "siblings", "ring"}),
]
SENTENCE_END = re.compile(r"(?<=[.!?\]])\s+(?=[A-Z0-9\"'(])")
BULLET = re.compile(r"^\s*(?:[-*\u2022]|\d+[.)])\s+", re.M)


def allowed_tools(sentence: str) -> set[str] | None:
    """Tools whose evidence can support this sentence, or None when it names no specific topic."""
    hit = [tools_ for pat, tools_ in TOPICS if pat.search(sentence)]
    return set().union(*hit) if hit else None


def check_citations(text: str, ev: tools.Evidence) -> tuple[str, list[str], list[str], list[str]]:
    """Clean a verdict so the UI only ever links evidence that shows the claim.

    Returns (text, cited, unknown, mismatched). Unknown ids (never returned by a tool) are removed.
    Mismatched ids (a real id from a tool that cannot show the sentence's topic, e.g. a siblings id on a
    "no reused socials" sentence) are removed too, and a sentence left with no citation at all is dropped:
    an unsupported claim is worse than a shorter answer. Bullets become plain sentences."""
    known = {i["id"]: i["tool"] for i in ev.items}
    by_id = {i["id"]: i for i in ev.items}
    text = BULLET.sub("", text.replace("**", "")).replace("\n", " ")
    text = re.sub(r"\s+", " ", text).strip()
    cited, unknown, mismatched, kept = [], [], [], []
    for sent in SENTENCE_END.split(text):
        ids = CITE.findall(sent)
        if not ids:
            kept.append(sent)
            continue
        ok_tools = allowed_tools(CITE.sub("", sent))
        good = []
        for eid in ids:
            if eid not in known:
                unknown.append(eid)
            elif eid.startswith("B") and (
                known[eid] != "brain_ask" or not by_id[eid].get("source", {}).get("url")
                or re.sub(r"\s+", " ", CITE.sub("", sent)).strip(" .") not in
                   re.sub(r"\s+", " ", by_id[eid].get("section", ""))
            ):
                mismatched.append(eid)
            elif (eid.startswith("B") and known[eid] != "brain_ask") or (
                eid.startswith("E") and ok_tools is not None and known[eid] not in ok_tools
            ):
                mismatched.append(eid)
            else:
                good.append(eid)
        if not good:
            continue
        for eid in set(ids) - set(good):
            sent = sent.replace(f"[{eid}]", "")
        kept.append(re.sub(r"\s+([.!?,])", r"\1", re.sub(r"\s{2,}", " ", sent)).strip())
        cited += good
    dedup = lambda xs: list(dict.fromkeys(xs))  # noqa: E731
    return " ".join(kept).strip(), dedup(cited), dedup(unknown), dedup(mismatched)


# ---- dossier fallback --------------------------------------------------------------------------

async def dossier(question: str, mint: str | None, ev: tools.Evidence | None = None) -> AsyncIterator[dict]:
    """Fixed tools, fixed sentences. Used when no AI key is active or the AI call fails."""
    ev = ev if ev is not None else tools.Evidence()
    mint = mint or _mint_from(question)
    if not mint:
        name = question.strip()
        res, ok = await _step_call(ev, "search_coins", {"query": name})
        yield _step("search_coins", {"query": name}, ok, res)
        rows = res.get("rows") or []
        if not rows:
            yield {"type": "evidence", "items": ev.items}
            yield _verdict("Paste the coin's address (mint) and Sniff will look it up.", ev, "dossier")
            return
        mint = rows[0]["mint"]
    results: dict[str, dict] = {}
    for name in ("coin_dossier", "siblings", "shared_handles", "shared_snipers"):
        res, ok = await _step_call(ev, name, {"mint": mint})
        results[name] = res
        yield _step(name, {"mint": mint}, ok, res)
        if name == "coin_dossier" and not res.get("found"):
            break
    yield {"type": "evidence", "items": ev.items}
    yield _verdict(_dossier_text(results), ev, "dossier")


def _dossier_text(r: dict[str, dict]) -> str:
    d = r.get("coin_dossier") or {}
    if not d.get("found"):
        return ("This coin is not in Sniff's graph yet: it may be brand new or not a pump.fun launch. "
                + base_line())
    s = []
    coin, n, g = d["coin"], d["creator_other_coins"], d["creator_other_graduated"]
    s.append(f"Its creator launched {n} other coin{'s' if n != 1 else ''}, and {g} of them graduated [{d['evidence'][0]}].")
    real = [f for f in d.get("funders", []) if f.get("label") != "Hub"]
    if real:
        s.append(f"The creator was funded by wallet {tools._short(real[0]['addr'])} [{real[0]['evidence']}].")
    elif d.get("funders"):
        s.append(f"The creator was funded from a hub, likely an exchange, which links it to nobody [{d['funders'][0]['evidence']}].")
    sib = (r.get("siblings") or {}).get("rows") or []
    if sib:
        top = sib[0]
        s.append(f"That funder also paid {top['creators']} other creators, who launched {top['coins']} coins; "
                 f"{top['graduated']} graduated [{top['evidence']}].")
    hand = (r.get("shared_handles") or {}).get("rows") or []
    if hand:
        h = hand[0]
        s.append(f"Its {h['platform']} '{h['handle']}' also appears on {h['other_coins']} other coins [{h['evidence']}].")
    sn = (r.get("shared_snipers") or {}).get("rows") or []
    if sn:
        s.append(f"{sn[0]['shared']} of its early buyers also bought early into {sn[0].get('name') or 'another coin'} "
                 f"[{sn[0]['evidence']}].")
    if d.get("ring"):
        ring = d["ring"]
        s.append(f"The creator sits in a funding ring of {ring.get('creators')} creators and {ring.get('coins')} coins, "
                 f"{ring.get('graduations')} graduated [{ring['evidence']}].")
    if len(s) == 1 and not g and not n:
        s.append("No links to other creators were found, which is not the same as safe.")
    s.append(base_line())
    return " ".join(s)


# ---- the agent -------------------------------------------------------------------------------

async def investigate(question: str, mint: str | None = None, visitor_key: str | None = None,
                      session_id: str | None = None) -> AsyncIterator[dict]:
    """Every investigation records safe tool evidence; a graph outage is visible to the caller."""
    ctx = await asyncio.to_thread(memory.begin, session_id, "investigation", "coin:" + mint if mint else None)
    recalled = {}
    if ctx.available:
        try:
            recalled = await asyncio.to_thread(memory.recall, session=ctx.sid)
            if not mint and not _mint_from(question) and not COMPANY_QUESTION.search(question):
                subject = await asyncio.to_thread(memory.latest_entity, ctx.sid)
                if subject and subject.startswith("coin:"):
                    mint = subject.split(":", 1)[1]
        except Exception as exc:
            ctx.error = type(exc).__name__
    ev = tools.Evidence(memory=ctx)
    async for event in _investigate(question, mint, visitor_key, ev, recalled):
        if event["type"] == "start":
            event = {**event, "session_id": ctx.sid, "memory_available": ctx.available}
        if event["type"] == "done":
            if ctx.error:
                text = ("A privacy check refused to save some public evidence to shared memory." if ctx.error == "PrivacyError"
                        else "Shared memory is unavailable; this investigation may not appear in memory.")
                yield {"type": "notice", "text": text, "memory_error": ctx.error}
            event = {**event, "session_id": ctx.sid, "memory_available": ctx.available and not ctx.error}
        yield event


async def _investigate(question: str, mint: str | None, visitor_key: str | None,
                       ev: tools.Evidence, recalled: dict) -> AsyncIterator[dict]:
    t0 = time.monotonic()
    if not mint and COMPANY_QUESTION.search(question):
        # Public company retrieval is useful with or without an AI key.
        yield {"type": "start", "mode": "brain", "model": None, "using": "none"}
        res, ok = await _step_call(ev, "brain_ask", {"question": question})
        yield _step("brain_ask", {"question": question}, ok, res)
        yield {"type": "evidence", "items": ev.items}
        text = res.get("answer", "The company brain is unavailable right now. Please try again later.")
        yield {"type": "verdict", "text": text, "cited": res.get("cited", []), "unknown_cited": [],
               "mismatched_cited": [], "mode": "brain", "sources": res.get("sources", []), "graph": res.get("graph", {})}
        yield {"type": "done", "ms": int(1000 * (time.monotonic() - t0))}
        return
    client, model, who = ai.client_for(visitor_key)
    if not client:
        yield {"type": "start", "mode": "dossier", "model": None, "using": "none"}
        async for e in dossier(question, mint, ev):
            yield e
        yield {"type": "done", "ms": int(1000 * (time.monotonic() - t0))}
        return

    yield {"type": "start", "mode": "agent", "model": model, "using": who}
    user = question.strip() + (f"\n\nCoin (mint): {mint}" if mint else "")
    if recalled.get("rows"):
        user += "\n\nPreviously recorded public evidence (tool results will reuse these if unchanged):\n" + tools.cap({"rows": recalled["rows"][:12]}, 6000)
    messages: list[dict] = [{"role": "user", "content": user}]
    system = [{"type": "text", "text": SYSTEM.format(base_line=base_line()), "cache_control": {"type": "ephemeral"}}]
    tool_defs = tools.claude_tools()
    tool_defs[-1] = {**tool_defs[-1], "cache_control": {"type": "ephemeral"}}
    text = ""
    try:
        for turn in range(MAX_TOOL_TURNS + 1):
            last = turn == MAX_TOOL_TURNS
            msg = await client.messages.create(
                model=model, max_tokens=MAX_TOKENS, system=system, tools=tool_defs, messages=messages,
                **({"tool_choice": {"type": "none"}} if last else {}))
            uses = [b for b in msg.content if getattr(b, "type", "") == "tool_use"]
            text = "".join(getattr(b, "text", "") for b in msg.content if getattr(b, "type", "") == "text")
            if not uses or msg.stop_reason != "tool_use":
                break
            messages.append({"role": "assistant", "content": [b.model_dump(exclude_none=True) for b in msg.content]})
            results = []
            for u in uses:
                res, ok = await _step_call(ev, u.name, u.input)
                yield _step(u.name, u.input, ok, res)
                results.append({"type": "tool_result", "tool_use_id": u.id, "content": tools.cap({k: v for k, v in res.items() if k != "_ms"}),
                                **({} if ok else {"is_error": True})})
            messages.append({"role": "user", "content": results})
    except Exception as e:  # noqa: BLE001 - never the message: it can echo request data
        log.warning("agent AI call failed: %s; falling back to the dossier", type(e).__name__)
        yield {"type": "notice", "text": f"The AI call failed ({type(e).__name__}); showing the fixed dossier instead."}
        async for e2 in dossier(question, mint, ev):
            yield e2
        yield {"type": "done", "ms": int(1000 * (time.monotonic() - t0))}
        return

    if not text.strip():
        text = "Sniff could not finish this investigation. " + base_line()
    yield {"type": "evidence", "items": ev.items}
    yield _verdict(text, ev, "agent")
    yield {"type": "done", "ms": int(1000 * (time.monotonic() - t0))}


# ---- helpers ---------------------------------------------------------------------------------

def _mint_from(text: str) -> str | None:
    m = MINT_IN_TEXT.search(text or "")
    return m.group(0) if m else None


async def _step_call(ev: tools.Evidence, name: str, args: dict) -> tuple[dict, bool]:
    t = time.monotonic()
    res, ok = await asyncio.to_thread(tools.run_tool, ev, name, args)
    res = {**res, "_ms": int(1000 * (time.monotonic() - t))}
    return res, ok


def _step(name: str, args: dict, ok: bool, res: dict) -> dict:
    return {"type": "step", "tool": name, "input": args, "ok": ok, "ms": res.get("_ms"),
            "evidence": _ids_in(res), **({} if ok else {"error": res.get("error")})}


MAX_CLAIMS = 5


def cap_claims(text: str, limit: int = MAX_CLAIMS) -> str:
    """Keep the first `limit` claim sentences plus the closing context line. The prompt asks for 2 to 5,
    but the model sometimes writes more; it leads with the strongest facts, so the tail is what goes."""
    sents = SENTENCE_END.split(text)
    close = [x for x in sents if x.startswith("For context:") or x.startswith("History, not a prediction")]
    claims = [x for x in sents if x not in close]
    return " ".join(claims[:limit] + close).strip()


def _verdict(text: str, ev: tools.Evidence, mode: str) -> dict:
    text, cited, unknown, mismatched = check_citations(text, ev)
    if mode == "agent":
        text = cap_claims(text)
        cited = [c for c in cited if f"[{c}]" in text]
    return {"type": "verdict", "text": text, "cited": cited, "unknown_cited": unknown,
            "mismatched_cited": mismatched, "mode": mode}
