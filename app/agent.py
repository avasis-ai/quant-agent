"""The Sniff agent: Claude plans which graph tools to call, calls them, then writes a short verdict
that cites evidence ids. Without a working AI key it falls back to a fixed dossier built from the
same tools, so the evidence never depends on the LLM.

investigate() is an async generator of events, so the route can stream them (SSE) or collect them:
  {"type": "start", "mode": "agent"|"dossier", "model": ...}
  {"type": "step", "tool": ..., "input": {...}, "ok": bool, "ms": int, "evidence": [ids]}
  {"type": "evidence", "items": [...]}          all evidence gathered, once, before the verdict
  {"type": "verdict", "text": ..., "cited": [ids], "unknown_cited": [ids], "mode": ...}
  {"type": "done", "ms": int}
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from typing import Any, AsyncIterator

from . import ai, tools

log = logging.getLogger("sniff.agent")

MAX_TOOL_TURNS = 8
MAX_TOKENS = 1200
CITE = re.compile(r"\[(E\d+)\]")
MINT_IN_TEXT = re.compile(r"\b[1-9A-HJ-NP-Za-km-z]{32,44}\b")

SYSTEM = """You are Sniff, an investigator for pump.fun meme coins on Solana. You answer from a graph of
public on-chain history: coins, the wallets that created them, who funded those wallets, early buyers
(snipers), shared socials, and funding rings. Use the tools; never guess a fact the tools did not return.

How to work:
- Given a coin, start with coin_dossier. Then follow the strongest lead: siblings (same funder),
  shared_handles, shared_snipers, ring, funding_trail. Use search_coins when you only have a name.
- A hub (a funder of more than 200 wallets, likely an exchange) proves nothing. Never treat two things
  as linked because they share a hub.
- Stop when you have enough; you have at most 8 tool calls.

How to answer (plain words, for traders, no jargon):
- 2 to 5 short sentences. Every factual sentence ends with the evidence ids it rests on, like [E2] or
  [E1][E4]. Only cite ids that appeared in tool results.
- Describe history only. Never say buy, sell, safe, scam, or what the price will do. Say "no links found"
  rather than "clean" when the tools find nothing.
- End with exactly this line: {base_line}"""


def base_line() -> str:
    try:
        b = tools.base_rate()
        pct = f"{100 * b['rate']:.1f}%"
        return f"For context: {pct} of the {b['coins']:,} pump.fun launches in this graph graduated. History, not a prediction."
    except Exception:  # noqa: BLE001
        return "History, not a prediction."


def _ids_in(result: Any) -> list[str]:
    found = re.findall(r'"(E\d+)"', json.dumps(result, default=str))
    return list(dict.fromkeys(found))


def check_citations(text: str, ev: tools.Evidence) -> tuple[str, list[str], list[str]]:
    """(text with unknown citations removed, cited ids, unknown ids). The UI only ever links real evidence."""
    known = ev.ids()
    cited, unknown = [], []
    for eid in CITE.findall(text):
        (cited if eid in known else unknown).append(eid)
    for eid in set(unknown):
        text = text.replace(f"[{eid}]", "")
    return text.strip(), list(dict.fromkeys(cited)), list(dict.fromkeys(unknown))


# ---- dossier fallback --------------------------------------------------------------------------

async def dossier(question: str, mint: str | None) -> AsyncIterator[dict]:
    """Fixed tools, fixed sentences. Used when no AI key is active or the AI call fails."""
    ev = tools.Evidence()
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

async def investigate(question: str, mint: str | None = None, visitor_key: str | None = None) -> AsyncIterator[dict]:
    t0 = time.monotonic()
    client, model, who = ai.client_for(visitor_key)
    if not client:
        yield {"type": "start", "mode": "dossier", "model": None, "using": "none"}
        async for e in dossier(question, mint):
            yield e
        yield {"type": "done", "ms": int(1000 * (time.monotonic() - t0))}
        return

    yield {"type": "start", "mode": "agent", "model": model, "using": who}
    ev = tools.Evidence()
    user = question.strip() + (f"\n\nCoin (mint): {mint}" if mint else "")
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
        async for e2 in dossier(question, mint):
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


def _verdict(text: str, ev: tools.Evidence, mode: str) -> dict:
    text, cited, unknown = check_citations(text, ev)
    return {"type": "verdict", "text": text, "cited": cited, "unknown_cited": unknown, "mode": mode}
