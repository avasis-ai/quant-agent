"""Sniff's tools: nine lineage reads, shared investigation memory, and the public company brain.

Every tool returns compact rows plus evidence. Evidence is the contract between the graph, the
agent and the UI: each item has an id ("E1", "E2", ...), the tool and arguments that produced it,
a one-line summary, and the nodes and edges to highlight. Node keys are stable across queries
("coin:<mint>", "wallet:<addr>", "hub:<addr>", "handle:<hid>", "ring:<rid>"), never FalkorDB's
internal ids. The same evidence found twice in one investigation keeps its first id.

Hubs (funders of more than 200 wallets, likely exchanges) can end a funding trail but never link
two things together: the queries never walk through them, and evidence marks them.
"""
from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from . import queries
from .graph import read

MAX_RESULT_CHARS = 6000   # per tool result sent back to Claude
MAX_ROWS = 12
BASE58 = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")

# Which properties to keep per label, in this order. Everything else stays in the graph.
KEEP = {
    "Coin": ("mint", "name", "symbol", "created_at", "graduated", "died_min", "outcome", "ath_usd"),
    "Wallet": ("addr", "launches", "graduations", "snipes", "funded", "kind"),
    "Hub": ("addr", "degree", "creator_share"),   # its "label" property would clobber the node label
    "Handle": ("hid", "platform", "handle", "coins"),
    "Ring": ("rid", "creators", "coins", "graduations", "funders", "grad_rate"),
}
EDGE_KEEP = ("at", "sol", "rank", "kind")


# ---- serialization ---------------------------------------------------------------------------

def label_of(n: dict) -> str:
    labels = n.get("labels") or []
    for lab in ("Hub", "Coin", "Wallet", "Handle", "Ring"):
        if lab in labels:
            return lab
    return labels[0] if labels else "?"


def node_key(n: dict) -> str:
    lab = label_of(n)
    ident = {"Coin": "mint", "Wallet": "addr", "Hub": "addr", "Handle": "hid", "Ring": "rid"}.get(lab)
    return f"{lab.lower()}:{n.get(ident)}" if ident else f"node:{n.get('id')}"


def compact_node(n: dict) -> dict:
    lab = label_of(n)
    out = {"key": node_key(n), "label": lab}
    for k in KEEP.get(lab, ()):
        v = n.get(k)
        if v is not None and v != "":
            out[k] = (int(v) if v.is_integer() and k not in ("ath_usd", "creator_share", "grad_rate")
                      else round(v, 4)) if isinstance(v, float) else v
    return out


def compact_path(p: dict) -> dict:
    """A FalkorDB path (as graph.plain returns it) -> nodes and edges keyed by stable node keys."""
    nodes = p.get("nodes") or []
    by_id = {n.get("id"): node_key(n) for n in nodes}
    edges = []
    for e in p.get("edges") or []:
        ed = {"type": e.get("type"), "src": by_id.get(e.get("src"), f"node:{e.get('src')}"),
              "dst": by_id.get(e.get("dst"), f"node:{e.get('dst')}")}
        for k in EDGE_KEEP:
            if e.get(k) is not None:
                ed[k] = round(e[k], 4) if isinstance(e[k], float) else e[k]
        edges.append(ed)
    return {"nodes": [compact_node(n) for n in nodes], "edges": edges}


def cap(obj: Any, limit: int = MAX_RESULT_CHARS) -> str:
    """JSON for Claude, trimmed list by list until it fits."""
    text = json.dumps(obj, default=str, separators=(",", ":"))
    if len(text) <= limit:
        return text
    if isinstance(obj, dict) and isinstance(obj.get("rows"), list) and len(obj["rows"]) > 1:
        rows = obj["rows"]
        keep = max(1, len(rows) // 2)
        return cap({**obj, "rows": rows[:keep], "truncated": obj.get("truncated", 0) + len(rows) - keep}, limit)
    # An oversized single row or graph must still be valid JSON for MCP clients.
    # Keep the existing evidence outside this compact result; callers receive it separately.
    trimmed = json.loads(text)
    for _ in range(100):
        candidates = []

        def visit(value, parent=None, key=None):
            if isinstance(value, list) and len(value) > 1:
                candidates.append((len(json.dumps(value, default=str)), parent, key, value))
            if isinstance(value, str) and len(value) > 128:
                candidates.append((len(value), parent, key, value))
            if isinstance(value, dict):
                for k, v in value.items():
                    visit(v, value, k)
            elif isinstance(value, list):
                for k, v in enumerate(value):
                    visit(v, value, k)

        visit(trimmed)
        if not candidates:
            break
        _, parent, key, value = max(candidates, key=lambda c: c[0])
        replacement = value[:max(1, len(value) // 2)]
        if isinstance(value, str):
            replacement += "…"
        if parent is None:
            trimmed = replacement
        else:
            parent[key] = replacement
        out = json.dumps(trimmed, default=str, separators=(",", ":"))
        if len(out) <= limit:
            return out
    return json.dumps({"truncated": True, "note": "Result is too large; narrow the query."})


# ---- evidence --------------------------------------------------------------------------------

@dataclass
class Evidence:
    items: list[dict] = field(default_factory=list)
    _seen: dict[str, str] = field(default_factory=dict)
    memory: Any = None  # memory.Investigation, kept request-local

    def add(self, tool: str, args: dict, summary: str, nodes: list[dict], edges: list[dict] | None = None,
            *, identity: str | None = None) -> str:
        edges = edges or []
        sig = json.dumps([tool, sorted(n["key"] for n in nodes),
                          sorted((e["type"], e["src"], e["dst"]) for e in edges)])
        if identity:
            sig += ":" + identity
        if sig in self._seen:
            return self._seen[sig]
        eid = f"E{1 + sum(i['id'].startswith('E') for i in self.items)}"
        self._seen[sig] = eid
        self.items.append({"id": eid, "tool": tool, "args": args, "summary": summary,
                           "nodes": nodes, "edges": edges})
        return eid

    def ids(self) -> set[str]:
        return {i["id"] for i in self.items}


def _ints(row: dict) -> dict:
    """FalkorDB returns sum() as a float; counts read better as whole numbers."""
    return {k: int(v) if isinstance(v, float) and k in ("graduated", "coins", "creators", "shared",
                                                          "other_coins", "other_creators") else v
            for k, v in row.items()}


def _short(addr: str | None) -> str:
    return f"{addr[:4]}…{addr[-4:]}" if addr and len(addr) > 10 else str(addr)


def _coin_name(c: dict) -> str:
    sym = c.get("symbol")
    return f"{c.get('name') or '?'}" + (f" (${sym})" if sym else "")


def _wallet(addr: str, **props) -> dict:
    return {"key": f"wallet:{addr}", "label": "Wallet", "addr": addr, **props}


def _coin(mint: str, **props) -> dict:
    return {"key": f"coin:{mint}", "label": "Coin", "mint": mint, **props}


def _none(ev: Evidence, tool: str, args: dict, note: str, *subjects: dict) -> dict:
    """An empty answer is evidence too: a 'none found' item lets a verdict cite a negative
    ("no other coin reuses its socials") instead of borrowing an unrelated tool's id."""
    return {"rows": [], "note": note, "evidence": ev.add(tool, args, note, list(subjects))}


# ---- the tools -------------------------------------------------------------------------------

class BadInput(ValueError):
    pass


def _need_addr(v: Any, what: str) -> str:
    v = str(v or "").strip()
    if not BASE58.match(v):
        raise BadInput(f"{what} must be a Solana address (base58, 32-44 characters).")
    return v


def t_search_coins(ev: Evidence, query: str) -> dict:
    words = re.findall(r"[A-Za-z0-9]+", str(query or ""))[:4]
    if not words:
        raise BadInput("query needs a word from the coin's name or ticker.")
    q = " ".join(words)
    rows = read("CALL db.idx.fulltext.queryNodes('Coin', $q) YIELD node, score "
                "RETURN node ORDER BY score DESC, node.created_at DESC LIMIT 10", {"q": q})
    out = []
    for r in rows:
        c = compact_node(r["node"])
        c["evidence"] = ev.add("search_coins", {"query": q}, f"{_coin_name(c)} matches '{q}'", [c])
        out.append(c)
    return {"rows": out, "note": "Several coins can share a name; pick by mint." if len(out) > 1 else ""}


def t_coin_dossier(ev: Evidence, mint: str) -> dict:
    mint = _need_addr(mint, "mint")
    r = queries.coin_dossier(mint)
    if not r:
        return {"found": False, **_none(ev, "coin_dossier", {"mint": mint},
                                        "This coin is not in the graph (too new, or not a pump.fun launch).",
                                        _coin(mint))}
    coin, creator = compact_node(r["coin"]), compact_node(r["creator"])
    created = {"type": "CREATED", "src": creator["key"], "dst": coin["key"]}
    r["others"], r["other_grads"] = int(r["others"] or 0), int(r["other_grads"] or 0)
    out = {"found": True, "coin": coin, "creator": creator,
           "creator_other_coins": r["others"], "creator_other_graduated": r["other_grads"]}
    out["evidence"] = [ev.add("coin_dossier", {"mint": mint},
                              f"{_short(creator.get('addr'))} created {_coin_name(coin)} and "
                              f"{r['others']} other coins ({r['other_grads']} graduated)",
                              [creator, coin] + [compact_node(o) for o in (r.get("recent") or [])[:5]],
                              [created] + [{"type": "CREATED", "src": creator["key"], "dst": node_key(o)}
                                           for o in (r.get("recent") or [])[:5]])]
    out["recent_other_coins"] = [compact_node(o) for o in (r.get("recent") or [])[:8]]
    funders = []
    for f in r.get("funders") or []:
        fnode = ({"key": f"hub:{f['funder']}", "label": "Hub", "addr": f["funder"]} if f.get("hub")
                 else _wallet(f["funder"]))
        edge = {"type": "FUNDED", "src": fnode["key"], "dst": creator["key"], "sol": f.get("sol"), "at": f.get("at")}
        what = "a hub (likely an exchange)" if f.get("hub") else "wallet " + _short(f["funder"])
        funders.append({**fnode, "sol": f.get("sol"), "at": f.get("at"),
                        "evidence": ev.add("coin_dossier", {"mint": mint},
                                           f"The creator was funded by {what}", [fnode, creator], [edge])})
    out["funders"] = funders
    if r.get("ring"):
        ring = compact_node(r["ring"])
        out["ring"] = {**ring, "evidence": ev.add(
            "coin_dossier", {"mint": mint},
            f"The creator is in funding ring {ring.get('rid')}: {ring.get('creators')} creators, "
            f"{ring.get('coins')} coins, {ring.get('graduations')} graduated",
            [creator, ring], [{"type": "IN_RING", "src": creator["key"], "dst": ring["key"]}])}
    return out


def t_funding_trail(ev: Evidence, address: str) -> dict:
    addr = _need_addr(address, "address")
    rows = queries.funding_trail(addr)
    out = []
    for r in rows[:MAX_ROWS]:
        p = compact_path(r["p"])
        start = p["nodes"][0] if p["nodes"] else {}
        what = "a hub (likely an exchange), where the trail stops" if r.get("hub") else _short(start.get("addr"))
        out.append({"depth": r["depth"], "from": start.get("addr"), "from_is_hub": bool(r.get("hub")),
                    "evidence": ev.add("funding_trail", {"address": addr},
                                       f"{_short(addr)} was funded {r['depth']} hop(s) back by {what}",
                                       p["nodes"], p["edges"])})
    if not rows:
        return _none(ev, "funding_trail", {"address": addr}, "No known funder for this wallet.", _wallet(addr))
    return {"rows": out, "truncated": max(0, len(rows) - MAX_ROWS), "note": ""}


def t_siblings(ev: Evidence, mint: str) -> dict:
    mint = _need_addr(mint, "mint")
    rows = [_ints(x) for x in queries.siblings(mint)]
    out = []
    for r in rows[:MAX_ROWS]:
        f = _wallet(r["funder"])
        out.append({**r, "evidence": ev.add(
            "siblings", {"mint": mint},
            f"Funder {_short(r['funder'])} also paid {r['creators']} other creators: "
            f"{r['coins']} coins, {r['graduated']} graduated", [f, _coin(mint)])})
    if not rows:
        return _none(ev, "siblings", {"mint": mint},
                     "No other creator shares a (non-hub) funder with this creator.", _coin(mint))
    return {"rows": out, "truncated": max(0, len(rows) - MAX_ROWS), "note": ""}


def t_shared_snipers(ev: Evidence, mint: str) -> dict:
    mint = _need_addr(mint, "mint")
    rows = [_ints(x) for x in queries.shared_snipers(mint)]
    out = []
    for r in rows[:MAX_ROWS]:
        r = {**r, "score": round(r.get("score") or 0, 2)}
        out.append({**r, "evidence": ev.add(
            "shared_snipers", {"mint": mint},
            f"{r['shared']} early buyers of this coin also bought early into {r.get('name') or _short(r['mint'])}"
            f" ({'graduated' if r.get('graduated') else 'did not graduate'})",
            [_coin(mint), _coin(r["mint"], name=r.get("name"), graduated=r.get("graduated"))])})
    if not rows:
        return _none(ev, "shared_snipers", {"mint": mint},
                     "No early buyer of this coin bought early into another coin (bots ignored).", _coin(mint))
    return {"rows": out, "truncated": max(0, len(rows) - MAX_ROWS),
            "note": "score = sum of each shared buyer's rarity; bots (>100 snipes) are ignored."}


def t_shared_handles(ev: Evidence, mint: str) -> dict:
    mint = _need_addr(mint, "mint")
    rows = [_ints(x) for x in queries.shared_handles(mint)]
    out = []
    for r in rows[:MAX_ROWS]:
        h = {"key": f"handle:{r['platform']}:{r['handle']}", "label": "Handle",
             "platform": r["platform"], "handle": r["handle"], "coins": r["total_coins"]}
        out.append({**r, "evidence": ev.add(
            "shared_handles", {"mint": mint},
            f"{r['platform']} '{r['handle']}' is also on {r['other_coins']} other coins by "
            f"{r['other_creators']} creators ({r['graduated']} graduated)",
            [_coin(mint), h], [{"type": "LINKS", "src": f"coin:{mint}", "dst": h["key"]}])})
    if not rows:
        return _none(ev, "shared_handles", {"mint": mint},
                     "No other coin uses this coin's socials or website.", _coin(mint))
    return {"rows": out, "truncated": max(0, len(rows) - MAX_ROWS), "note": ""}


def t_ring(ev: Evidence, mint: str | None = None, address: str | None = None) -> dict:
    if mint:
        r = queries.ring(mint=_need_addr(mint, "mint"))
    elif address:
        r = queries.ring(addr=_need_addr(address, "address"))
    else:
        raise BadInput("Give a mint or an address.")
    if not r:
        subject = _coin(mint) if mint else _wallet(address)
        return {"found": False, **_none(ev, "ring", {"mint": mint, "address": address},
                                        "Not part of a funding ring (no two creators linked by funding).", subject)}
    ring = compact_node(r["ring"])
    top = [_wallet(t["creator"], launches=t["launches"], graduations=t["graduations"]) for t in r["top_creators"]]
    eid = ev.add("ring", {"mint": mint, "address": address},
                 f"Funding ring {ring.get('rid')}: {ring.get('creators')} creators linked by funding, "
                 f"{ring.get('coins')} coins, {ring.get('graduations')} graduated",
                 [ring] + top, [{"type": "IN_RING", "src": t["key"], "dst": ring["key"]} for t in top])
    return {"found": True, "ring": ring, "top_creators": top, "evidence": eid}


def t_connect(ev: Evidence, a: str, b: str) -> dict:
    a, b = _need_addr(a, "a"), _need_addr(b, "b")
    # Deepen step by step: short links come back fast, and a 6-hop search between two busy wallets can
    # time out. Stop at the first depth that finds a link, or at the first timeout.
    rows, searched = [], 0
    for max_len in (4, 5, 6):
        try:
            rows = queries.connect(a, b, max_len=max_len)
        except Exception:  # noqa: BLE001 - a timeout at this depth: report what was searched
            if not searched:
                raise
            break
        searched = max_len
        if rows:
            break
    out = []
    for r in rows:
        p = compact_path(r["path"])
        out.append({"hops": r["hops"], "evidence": ev.add(
            "connect", {"a": a, "b": b}, f"{_short(a)} and {_short(b)} are linked in {r['hops']} hops "
            f"({' → '.join(e['type'] for e in p['edges'])})", p["nodes"], p["edges"])})
    if not rows:
        ends = [_coin(x) if x.endswith("pump") else _wallet(x) for x in (a, b)]
        return _none(ev, "connect", {"a": a, "b": b},
                     f"No link within {searched} hops (hubs and platform-sized handles excluded).", *ends)
    return {"rows": out, "note": ""}


def t_top_operators(ev: Evidence, days: int = 7) -> dict:
    days = max(1, min(int(days or 7), 30))
    since = _graph_now() - days * 86400
    rows = [_ints(x) for x in queries.top_operators(since, limit=10)]
    out = []
    for r in rows:
        out.append({**r, "evidence": ev.add(
            "top_operators", {"days": days},
            f"Funder {_short(r['funder'])} paid {r['creators']} creators in {days} days: "
            f"{r['coins']} coins, {r['graduated']} graduated", [_wallet(r["funder"])])})
    return {"rows": out, "window_days": days}


_NOW: dict[str, float] = {}


def _graph_now() -> int:
    """The newest launch in the graph: windows are measured from the data, not the wall clock."""
    if "t" not in _NOW or time.time() - _NOW["fetched"] > 600:
        rows = read("MATCH (c:Coin) RETURN max(c.created_at) AS t", timeout_ms=15000)
        _NOW.update(t=int(rows[0]["t"]), fetched=time.time())
    return int(_NOW["t"])


_BASE: dict[str, Any] = {}


def base_rate() -> dict:
    """How often a pump.fun launch in the graph graduated: the line every answer ends with."""
    if not _BASE:
        rows = read("MATCH (c:Coin) RETURN count(c) AS coins, "
                    "sum(CASE WHEN c.graduated THEN 1 ELSE 0 END) AS grads", timeout_ms=15000)
        coins, grads = int(rows[0]["coins"]), int(rows[0]["grads"])
        _BASE.update(coins=coins, graduated=grads, rate=grads / coins if coins else 0.0)
    return dict(_BASE)


# ---- Claude tool definitions -----------------------------------------------------------------

def _schema(**props: tuple[str, str]) -> dict:
    return {"type": "object", "properties": {k: {"type": t, "description": d} for k, (t, d) in props.items()},
            "required": [k for k in props if k not in ("days", "mint_opt", "address_opt")]}


MINT = ("string", "The coin's mint address (base58).")
ADDR = ("string", "A wallet address (base58).")

TOOLS: dict[str, tuple[Callable[..., dict], str, dict]] = {
    "search_coins": (t_search_coins, "Find coins by name or ticker. Use when the user gives a name, not an address.",
                     _schema(query=("string", "Words from the coin's name or ticker."))),
    "coin_dossier": (t_coin_dossier, "Start here for any coin: its creator, the creator's other coins and how they "
                     "did, who funded the creator, and the creator's funding ring.", _schema(mint=MINT)),
    "funding_trail": (t_funding_trail, "Who funded a wallet, up to 3 hops back. A hub (likely an exchange) ends "
                      "a trail and proves nothing.", _schema(address=ADDR)),
    "siblings": (t_siblings, "Other creators paid by the same funder as this coin's creator, and how their coins "
                 "did.", _schema(mint=MINT)),
    "shared_snipers": (t_shared_snipers, "Other coins that this coin's early buyers also bought early, weighted by "
                       "how rare each buyer is. Bots ignored.", _schema(mint=MINT)),
    "shared_handles": (t_shared_handles, "Other coins that reuse this coin's X/Telegram/website.", _schema(mint=MINT)),
    "ring": (t_ring, "The funding ring (creators linked through funding) a coin's creator or a wallet belongs to.",
             {"type": "object", "properties": {"mint": {"type": "string", "description": MINT[1]},
                                               "address": {"type": "string", "description": ADDR[1]}}}),
    "connect": (t_connect, "Shortest funding/creation/social link between two coins or wallets, never through a "
                "hub.", _schema(a=("string", "First mint or wallet."), b=("string", "Second mint or wallet."))),
    "top_operators": (t_top_operators, "Funders behind the most creators recently.",
                      {"type": "object", "properties": {"days": {"type": "integer", "description": "Window, 1-30."}}}),
}


def claude_tools() -> list[dict]:
    return [{"name": n, "description": d, "input_schema": s} for n, (_f, d, s) in TOOLS.items()]


def run_tool(ev: Evidence, name: str, args: dict) -> tuple[dict, bool]:
    """(result, ok). Bad input and query errors come back as results Claude can read and recover from."""
    if name not in TOOLS:
        return {"error": f"Unknown tool {name}."}, False
    fn = TOOLS[name][0]
    try:
        args = {k: v for k, v in (args or {}).items() if v not in (None, "")}
        is_lineage = name not in {"memory_recall", "memory_note", "brain_ask"}
        before = len(ev.items)
        if ev.memory and is_lineage:
            from . import memory
            try:
                result = memory.cached(ev.memory, name, args, ev)
                if result is not None:
                    memory.remember(ev.memory, name, args, result, ev.items[before:])
                    return result, True
            except Exception as exc:
                ev.memory.error = type(exc).__name__
        result = fn(ev, **args)
        if ev.memory and (is_lineage or name == "memory_recall"):
            from . import memory
            try:
                memory.remember(ev.memory, name, args, result, ev.items[before:])
            except Exception as exc:
                ev.memory.error = type(exc).__name__
        return result, True
    except BadInput as e:
        return {"error": str(e)}, False
    except ValueError as e:
        if name in {"memory_recall", "memory_note", "brain_ask"}:
            return {"error": str(e)}, False
        return {"error": f"Invalid value for {name}."}, False
    except TypeError:
        return {"error": f"Wrong arguments for {name}."}, False
    except Exception as e:  # noqa: BLE001 - a graph timeout or error; the agent should try something else
        return {"error": f"The graph query failed ({type(e).__name__})."}, False


def t_memory_recall(ev: Evidence, entity: str | None = None, session: str | None = None) -> dict:
    from .memory import recall
    result = recall(entity=entity, session=session or (ev.memory.sid if ev.memory and not entity else None), hydrate=True)
    for row in result["rows"]:
        payload = row.pop("payload", None)
        if not payload:
            continue
        item = json.loads(payload)
        persistent = row.get("id") or row["evidence_ids"][0]
        existing = next((i for i in ev.items if i["tool"] == item["tool"] and i["summary"] == item["summary"]
                         and i["args"] == item["args"]), None)
        eid = existing["id"] if existing else ev.add(item["tool"], item["args"], item["summary"], item["nodes"],
                                                    item["edges"], identity="memory:" + persistent)
        target = next(i for i in ev.items if i["id"] == eid)
        target["memory"] = {"id": persistent, "at": row["at"], "by": "sniff", "scope": result["scope"]}
        row["evidence"] = eid
    return result


def t_memory_note(ev: Evidence, entity: str, by: str, text: str, evidence_ids: list[str] | None = None) -> dict:
    from .memory import note
    return note(entity, by, text, evidence_ids)


def t_brain_ask(ev: Evidence, question: str) -> dict:
    from .brain import ask
    result = ask(question)
    by_section = {i["source"]["section_id"]: i for i in ev.items if i.get("tool") == "brain_ask"}
    mapping, current = {}, []
    for item in result["evidence"]:
        old = item["id"]
        section = item["source"]["section_id"]
        if section in by_section:
            target = by_section[section]
        else:
            target = {**item, "id": f"B{1 + sum(i['id'].startswith('B') for i in ev.items)}"}
            ev.items.append(target)
            by_section[section] = target
        mapping[old] = target["id"]
        current.append(target)
    result["answer"] = re.sub(r"\[(B\d+)\]", lambda m: "[" + mapping.get(m[1], m[1]) + "]", result["answer"])
    result["cited"] = [mapping[i] for i in result["cited"]]
    result["evidence"] = current
    for source in result["sources"]:
        source["id"] = mapping[source["id"]]
    for node in result["graph"]["nodes"]:
        if node.get("citation"):
            node["citation"] = mapping[node["citation"]]
    return result


TOOLS.update({
    "memory_recall": (t_memory_recall, "Recall what Sniff already learned, with timestamps and original tool provenance. "
                      "Give entity coin:<mint>/wallet:<address> for anonymised findings across sessions, or session for "
                      "one random session token. With no arguments uses this investigation's session.",
                      {"type": "object", "properties": {"entity": {"type": "string"}, "session": {"type": "string"}}}),
    "memory_note": (t_memory_note, "Coordinate with another agent by adding a public, attributed note about a coin or wallet. "
                    "No secrets or PII. by is a self-declared agent label, never a verified identity. Notes remain unverified.",
                    {"type": "object", "properties": {"entity": {"type": "string"}, "by": {"type": "string"},
                     "text": {"type": "string"}, "evidence_ids": {"type": "array", "items": {"type": "string"}}},
                     "required": ["entity", "by", "text"]}),
    "brain_ask": (t_brain_ask, "Ask QuantBase's public company knowledge graph about products, policies, decisions, "
                  "research and metrics. Retrieves entity neighbourhoods plus original source sections; cite [B#] evidence.",
                  _schema(question=("string", "A question about QuantBase or Sniff's public knowledge."))),
})
