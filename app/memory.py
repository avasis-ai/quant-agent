"""FalkorDB investigation memory and public, attributed agent coordination.

Only random session capabilities and public graph facts are persisted. Raw visitor
questions, keys, headers and IPs never enter this module's write payloads.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
import uuid
from dataclasses import dataclass

from . import knowledge_graph as kg
from .privacy import require_public

SESSION = re.compile(r"^[a-f0-9]{32}$")
ADDRESS = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")
CACHE_SECONDS = 3600


def session_id(value: str | None = None) -> str:
    if value is None:
        return uuid.uuid4().hex
    if not SESSION.fullmatch(value):
        raise ValueError("session_id must be a random 32-character lowercase hex token.")
    return value


def entity_ref(entity: str) -> tuple[str, str, str]:
    kind, sep, address = entity.partition(":")
    if not sep:
        kind, address = "coin", entity
    if kind not in ("coin", "wallet") or not ADDRESS.fullmatch(address):
        raise ValueError("entity must be coin:<mint> or wallet:<address> (Solana base58).")
    return ("Coin", "mint", address) if kind == "coin" else ("Wallet", "addr", address)


def call_key(tool: str, args: dict) -> str:
    return hashlib.sha256(json.dumps([tool, args], sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:32]


@dataclass
class Investigation:
    sid: str
    qid: str
    available: bool = True
    error: str | None = None


def begin(sid: str | None, tool: str = "investigation", entity: str | None = None) -> Investigation:
    ctx = Investigation(session_id(sid), uuid.uuid4().hex)
    try:
        kg.ensure_indexes("memory")
        # Tool names come from our registry. No visitor's free text is ever saved.
        if not re.fullmatch(r"[a-z_]{1,40}", tool):
            tool = "investigation"
        if entity:
            entity_ref(entity)
        kg.write("memory", """
        MERGE (s:Session {sid: $sid}) ON CREATE SET s.at = $at
        SET s.updated_at = $at
        CREATE (q:Question {qid: $qid, text: $text, at: $at, started_ns: $started_ns, entity: $entity})
        CREATE (s)-[:ASKED {at: $at}]->(q)
        RETURN q.qid AS qid
        """, {"sid": ctx.sid, "qid": ctx.qid, "text": "Public graph " + tool, "at": int(time.time()),
              "started_ns": time.time_ns(), "entity": entity or ""})
    except Exception as exc:  # availability is reported, never pretend a write succeeded
        ctx.available, ctx.error = False, type(exc).__name__
    return ctx


def latest_entity(sid: str) -> str | None:
    rows = kg.read("memory", "MATCH (:Session {sid: $sid})-[:ASKED]->(q:Question) "
                   "WHERE q.entity <> '' RETURN q.entity AS entity ORDER BY q.started_ns DESC LIMIT 1", {"sid": session_id(sid)})
    return rows[0]["entity"] if rows else None


def remember(ctx: Investigation, tool: str, args: dict, result: dict, items: list[dict], by: str = "sniff") -> bool:
    if not ctx.available or not items:
        return False
    # Scan the whole call before any write, including names from public coin metadata.
    require_public({"args": args, "result": result, "items": items})
    at, key = int(time.time()), call_key(tool, args)
    stored_args = {} if tool == "search_coins" else args
    for item in items:
        if item["tool"] == "search_coins":
            # A no-mint investigation can pass the entire visitor question to search.
            # Persist only the public coin match, never those visitor-supplied words.
            coin = next((n for n in item["nodes"] if n.get("label") == "Coin"), {})
            item = {**item, "args": {}, "summary": "Public coin " + str(coin.get("name") or coin.get("mint") or "match")
                    + " returned by coin search."}
        eid = uuid.uuid4().hex
        observed_at = int((item.get("memory") or {}).get("at") or at)
        # Hub is deliberately a Wallet reference here; no lineage relationships copied.
        entities = {(n.get("label"), n.get("mint") or n.get("addr")) for n in item.get("nodes", [])
                    if n.get("label") in ("Coin", "Wallet", "Hub")}
        refs = [{"kind": "Coin" if lab == "Coin" else "Wallet", "value": addr}
                for lab, addr in entities if addr and ADDRESS.fullmatch(addr)]
        # One query per evidence, with all ABOUT links in the same atomic write.
        kg.write("memory", """
        MATCH (q:Question {qid: $qid})
        SET q.entity = CASE WHEN q.entity = '' THEN $entity ELSE q.entity END
        CREATE (e:Evidence {eid: $eid, id: $local_id, tool: $tool, summary: $summary,
          at: $observed_at, recorded_at: $at, by: $by, call_key: $key,
          args_json: $args, result_json: $result, payload_json: $payload})
        CREATE (q)-[:FOUND {at: $at}]->(e)
        FOREACH (ref IN $coins | MERGE (c:Coin {mint: ref}) MERGE (e)-[:ABOUT]->(c))
        FOREACH (ref IN $wallets | MERGE (w:Wallet {addr: ref}) MERGE (e)-[:ABOUT]->(w))
        RETURN e.eid AS eid
        """, {"qid": ctx.qid, "eid": eid, "local_id": item["id"], "tool": item["tool"],
              "summary": item["summary"], "at": at, "observed_at": observed_at, "by": by, "key": key,
              "entity": ("coin:" + args["mint"] if args.get("mint") else
                         "wallet:" + args["address"] if args.get("address") else ""),
              "args": json.dumps(stored_args), "result": json.dumps(result), "payload": json.dumps(item),
              "coins": [r["value"] for r in refs if r["kind"] == "Coin"],
              "wallets": [r["value"] for r in refs if r["kind"] == "Wallet"]})
    return True


def cached(ctx: Investigation, tool: str, args: dict, ev) -> dict | None:
    """Replay an exact same-session call, remapping its original E ids into this answer."""
    if not ctx.available:
        return None
    rows = kg.read("memory", """
    MATCH (:Session {sid: $sid})-[:ASKED]->(q:Question)-[:FOUND]->(e:Evidence {call_key: $key})
    WHERE e.at >= $since AND q.qid <> $qid
    RETURN q.qid AS qid, e.payload_json AS payload, e.result_json AS result, e.eid AS eid, e.at AS at
    ORDER BY at DESC LIMIT 100
    """, {"sid": ctx.sid, "key": call_key(tool, args), "qid": ctx.qid, "since": int(time.time()) - CACHE_SECONDS})
    if not rows:
        return None
    newest = rows[0]["qid"]
    rows = [r for r in rows if r["qid"] == newest]
    payloads = [json.loads(r["payload"]) for r in rows]
    stored = json.loads(rows[0]["result"])
    expected = set(re.findall(r'"(E\d+)"', json.dumps(stored)))
    if not expected <= {p["id"] for p in payloads}:
        # Never replay a partially saved call whose result cites missing evidence.
        return None
    mapping = {}
    for row, item in zip(rows, payloads):
        existing = next((i for i in ev.items if i["tool"] == item["tool"] and i["summary"] == item["summary"]
                         and i["args"] == item["args"]), None)
        new = existing["id"] if existing else ev.add(item["tool"], item["args"], item["summary"], item["nodes"], item["edges"])
        mapping[item["id"]] = new
        target = next(i for i in ev.items if i["id"] == new)
        target["memory"] = {"id": row["eid"], "at": row["at"], "by": "sniff"}

    def remap(value):
        if isinstance(value, str):
            return mapping.get(value, value)
        if isinstance(value, list):
            return [remap(v) for v in value]
        if isinstance(value, dict):
            return {k: remap(v) for k, v in value.items()}
        return value

    return {**remap(stored), "recalled": True, "recorded_at": rows[0]["at"]}


def recall(entity: str | None = None, session: str | None = None, *, hydrate: bool = False) -> dict:
    if bool(entity) == bool(session):
        raise ValueError("Give exactly one entity or session.")
    if session:
        sid = session_id(session)
        rows = kg.read("memory", """
        MATCH (s:Session {sid: $sid})-[:ASKED]->(q:Question)
        OPTIONAL MATCH (q)-[:FOUND]->(e:Evidence)
        OPTIONAL MATCH (e)-[:ABOUT]->(n)
        RETURN q.qid AS question, q.at AS asked_at, e.eid AS id, e.tool AS tool, e.summary AS summary,
               e.at AS at, e.by AS by,
               collect(DISTINCT {kind: CASE WHEN n:Coin THEN 'Coin' ELSE 'Wallet' END,
                                 address: coalesce(n.mint, n.addr)}) AS entities
        """ + (", e.payload_json AS payload " if hydrate else "") + """
        ORDER BY at DESC LIMIT 80
        """, {"sid": sid})
        return {"scope": "session", "session_id": sid, "rows": rows, "graph": _graph(rows, sid),
                "note": "Public graph facts only; visitor question text is not stored."}
    label, prop, address = entity_ref(entity)
    # Aggregate across sessions without exposing session or question identifiers.
    rows = kg.read("memory", f"""
    MATCH (s:Session)-[:ASKED]->(:Question)-[:FOUND]->(e:Evidence)-[:ABOUT]->(n:{label} {{{prop}: $address}})
    RETURN e.tool AS tool, e.summary AS summary, count(DISTINCT s) AS sessions,
           collect(DISTINCT e.eid)[..10] AS evidence_ids,
           min(e.at) AS first_seen, max(e.at) AS at
    """ + (", head(collect(e.payload_json)) AS payload " if hydrate else "") + """
    ORDER BY at DESC LIMIT 40
    """, {"address": address})
    notes = kg.read("memory", f"""
    MATCH (note:Note)-[:ABOUT]->(n:{label} {{{prop}: $address}})
    OPTIONAL MATCH (note)-[:SUPPORTS]->(e:Evidence)
    RETURN note.nid AS id, note.by AS by, note.text AS text, note.at AS at,
           collect(e.eid) AS evidence_ids
    ORDER BY at DESC LIMIT 30
    """, {"address": address})
    return {"scope": "entity", "entity": f"{label.lower()}:{address}", "rows": rows,
            "notes": [{**n, "status": "unverified agent note", "provenance": "self-declared agent label"} for n in notes],
            "graph": _graph(rows, entity=f"{label.lower()}:{address}", notes=notes),
            "note": "Anonymised aggregate. Counts represent anonymous sessions, not independent verification."}


def note(entity: str, by: str, text: str, evidence_ids: list[str] | None = None) -> dict:
    label, prop, address = entity_ref(entity)
    if not re.fullmatch(r"[a-z][a-z0-9_-]{1,39}", by):
        raise ValueError("by must be a lowercase agent label, 2-40 letters, digits, hyphens or underscores.")
    text = text.strip()
    if not text or len(text) > 1000:
        raise ValueError("Note text must be 1-1000 characters.")
    require_public({"by": by, "text": text})
    ids = evidence_ids or []
    if len(ids) > 10 or any(not SESSION.fullmatch(e) for e in ids):
        raise ValueError("evidence_ids must be at most ten persistent memory evidence ids.")
    kg.ensure_indexes("memory")
    nid, at = uuid.uuid4().hex, int(time.time())
    if ids:
        found = kg.read("memory", f"MATCH (e:Evidence)-[:ABOUT]->(:{label} {{{prop}: $address}}) "
                        "WHERE e.eid IN $ids RETURN collect(DISTINCT e.eid) AS ids", {"address": address, "ids": ids})
        if not found or set(found[0]["ids"]) != set(ids):
            raise ValueError("Each cited memory evidence id must exist and concern this entity.")
    kg.write("memory", f"""
    MERGE (n:{label} {{{prop}: $address}})
    CREATE (note:Note {{nid: $nid, by: $by, text: $text, at: $at}})
    CREATE (note)-[:ABOUT]->(n)
    WITH note
    OPTIONAL MATCH (e:Evidence) WHERE e.eid IN $ids
    FOREACH (item IN CASE WHEN e IS NULL THEN [] ELSE [e] END | CREATE (note)-[:SUPPORTS]->(item))
    RETURN note.nid AS id
    """, {"address": address, "nid": nid, "by": by, "text": text, "at": at, "ids": ids})
    return {"id": nid, "by": by, "text": text, "at": at, "entity": entity, "evidence_ids": ids,
            "status": "unverified agent note", "provenance": "self-declared agent label"}


def _graph(rows: list[dict], sid: str | None = None, entity: str | None = None, notes: list | None = None) -> dict:
    nodes, edges, aliases = {}, [], {}
    root = f"session:{sid}" if sid else entity
    nodes[root] = {"key": root, "label": "Session" if sid else entity.split(":")[0].title(), "name": "This session" if sid else entity}
    for i, row in enumerate(rows):
        if sid:
            qid = "question:" + row["question"]
            nodes[qid] = {"key": qid, "label": "Question", "name": "Investigation", "at": row["asked_at"]}
            edges.append({"src": root, "dst": qid, "type": "ASKED"})
            if not row.get("id"):
                continue
        persistent_ids = row.get("evidence_ids") or []
        eid = "evidence:" + (row.get("id") or (persistent_ids[0] if persistent_ids else str(i)))
        for persistent in persistent_ids:
            aliases[persistent] = eid
        nodes[eid] = {"key": eid, "label": "Evidence", "name": row["summary"], "tool": row["tool"], "at": row["at"]}
        if sid:
            edges.append({"src": qid, "dst": eid, "type": "FOUND"})
            for ref in row.get("entities", []):
                if not ref.get("address"):
                    continue
                key = ref["kind"].lower() + ":" + ref["address"]
                nodes[key] = {"key": key, "label": ref["kind"], "name": ref["address"]}
                edges.append({"src": eid, "dst": key, "type": "ABOUT"})
        else:
            edges.append({"src": eid, "dst": root, "type": "ABOUT"})
    for note in notes or []:
        key = "note:" + note["id"]
        nodes[key] = {"key": key, "label": "Note", "name": note["by"] + ": " + note["text"], "at": note["at"]}
        edges.append({"src": key, "dst": root, "type": "ABOUT"})
        for persistent in note.get("evidence_ids", []):
            if persistent in aliases:
                edges.append({"src": key, "dst": aliases[persistent], "type": "SUPPORTS"})
    unique = {(e["src"], e["dst"], e["type"]): e for e in edges}
    return {"nodes": list(nodes.values()), "edges": list(unique.values())}
