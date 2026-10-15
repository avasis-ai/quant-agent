"""The 8 core graph questions Sniff can answer. Each is a fixed, parameterised read-only Cypher query.

Every function returns plain data and, where it matters, the paths that prove it, so the agent can cite
evidence and the UI can draw it. Hubs (likely exchanges) are never walked through.
"""
from __future__ import annotations

from .graph import read

BOT_SNIPES = 100      # wallets that sniped more coins than this are bots: sharing them proves nothing
BIG_HANDLE = 200      # a handle on more coins than this is a platform, not an operator


# 1 ---------------------------------------------------------------------------------------------
COIN_DOSSIER = """
MATCH (c:Coin {mint: $mint})<-[:CREATED]-(cr)
OPTIONAL MATCH (cr)-[:CREATED]->(o:Coin) WHERE o <> c
WITH c, cr, o ORDER BY o.created_at DESC
WITH c, cr, count(o) AS others, sum(CASE WHEN o.graduated THEN 1 ELSE 0 END) AS other_grads, collect(o)[..8] AS recent
OPTIONAL MATCH (cr)-[:IN_RING]->(r:Ring)
OPTIONAL MATCH (cr)<-[fe:FUNDED]-(f)
RETURN c AS coin, cr AS creator, others, other_grads, recent, r AS ring,
       collect({funder: f.addr, hub: f:Hub, sol: fe.sol, at: fe.at})[..5] AS funders
"""


def coin_dossier(mint: str) -> dict | None:
    rows = read(COIN_DOSSIER, {"mint": mint})
    if not rows:
        return None
    r = rows[0]
    r["funders"] = [f for f in r["funders"] if f.get("funder")]
    return r


# 2 ---------------------------------------------------------------------------------------------
FUNDING_TRAIL = """
MATCH p = (f)-[:FUNDED*1..3]->(w:Wallet {addr: $addr})
RETURN p, length(p) AS depth, f:Hub AS hub
ORDER BY depth LIMIT 60
"""


def funding_trail(addr: str) -> list[dict]:
    """Who funded this wallet, up to 3 hops back. A hub is always the end of a trail
    (hubs have no incoming funding edges in the graph)."""
    return read(FUNDING_TRAIL, {"addr": addr})


# 3 ---------------------------------------------------------------------------------------------
SIBLINGS = """
MATCH (c:Coin {mint: $mint})<-[:CREATED]-(cr:Wallet)<-[:FUNDED]-(f:Wallet)-[:FUNDED]->(s:Wallet)-[:CREATED]->(sc:Coin)
WHERE s <> cr
RETURN f.addr AS funder, count(DISTINCT s) AS creators, count(DISTINCT sc) AS coins,
       sum(CASE WHEN sc.graduated THEN 1 ELSE 0 END) AS graduated
ORDER BY creators DESC LIMIT 20
"""


def siblings(mint: str) -> list[dict]:
    """Creators who share a (non-hub) funder with this coin's creator, and how their coins did."""
    return read(SIBLINGS, {"mint": mint})


# 4 ---------------------------------------------------------------------------------------------
SHARED_SNIPERS = """
MATCH (c:Coin {mint: $mint})<-[:SNIPED]-(w:Wallet)-[:SNIPED]->(o:Coin)
WHERE w.snipes <= $bot AND o <> c
RETURN o.mint AS mint, o.name AS name, o.graduated AS graduated, count(w) AS shared, sum(w.idf) AS score
ORDER BY score DESC LIMIT 20
"""


def shared_snipers(mint: str) -> list[dict]:
    """Other coins sniped by this coin's early buyers, weighted by how rare each buyer is. Bots skipped."""
    return read(SHARED_SNIPERS, {"mint": mint, "bot": BOT_SNIPES})


# 5 ---------------------------------------------------------------------------------------------
SHARED_HANDLES = """
MATCH (c:Coin {mint: $mint})-[:LINKS]->(h:Handle)<-[:LINKS]-(o:Coin)<-[:CREATED]-(oc)
WHERE o <> c
RETURN h.platform AS platform, h.handle AS handle, h.coins AS total_coins,
       count(DISTINCT o) AS other_coins, count(DISTINCT oc) AS other_creators,
       sum(CASE WHEN o.graduated THEN 1 ELSE 0 END) AS graduated
ORDER BY other_coins DESC LIMIT 20
"""


def shared_handles(mint: str) -> list[dict]:
    return read(SHARED_HANDLES, {"mint": mint})


# 6 ---------------------------------------------------------------------------------------------
RING_OF_COIN = """
MATCH (c:Coin {mint: $mint})<-[:CREATED]-(:Wallet)-[:IN_RING]->(r:Ring)
RETURN r AS ring
"""
RING_OF_WALLET = """
MATCH (:Wallet {addr: $addr})-[:IN_RING]->(r:Ring) RETURN r AS ring
"""
RING_TOP = """
MATCH (w:Wallet)-[:IN_RING]->(r:Ring {rid: $rid})
RETURN w.addr AS creator, w.launches AS launches, w.graduations AS graduations
ORDER BY launches DESC LIMIT 10
"""


def ring(mint: str | None = None, addr: str | None = None) -> dict | None:
    rows = read(RING_OF_COIN, {"mint": mint}) if mint else read(RING_OF_WALLET, {"addr": addr})
    if not rows:
        return None
    r = rows[0]["ring"]
    return {"ring": r, "top_creators": read(RING_TOP, {"rid": r["rid"]})}


# 7 ---------------------------------------------------------------------------------------------
CONNECT = """
MATCH (a) WHERE (a:Coin AND a.mint = $a) OR (a:Wallet AND a.addr = $a)
MATCH (b) WHERE (b:Coin AND b.mint = $b) OR (b:Wallet AND b.addr = $b)
CALL algo.SPpaths({sourceNode: a, targetNode: b, relTypes: ['FUNDED', 'CREATED', 'LINKS'],
                   relDirection: 'both', maxLen: $max_len, pathCount: 0})
YIELD path
WITH path WHERE none(n IN nodes(path) WHERE n:Hub OR (n:Handle AND n.coins > $big))
RETURN path, length(path) AS hops ORDER BY hops LIMIT 3
"""


def connect(a: str, b: str, max_len: int = 6) -> list[dict]:
    """Shortest funding/creation/social links between two coins or wallets, never through a hub
    or a platform-sized handle."""
    return read(CONNECT, {"a": a, "b": b, "max_len": max_len, "big": BIG_HANDLE})


# 8 ---------------------------------------------------------------------------------------------
TOP_OPERATORS = """
MATCH (f:Wallet)-[:FUNDED]->(s:Wallet)-[:CREATED]->(c:Coin)
WHERE c.created_at >= $since
RETURN f.addr AS funder, count(DISTINCT s) AS creators, count(c) AS coins,
       sum(CASE WHEN c.graduated THEN 1 ELSE 0 END) AS graduated
ORDER BY creators DESC, coins DESC LIMIT $limit
"""


def top_operators(since: int, limit: int = 20) -> list[dict]:
    """Funders behind the most creators whose coins launched since `since` (epoch seconds)."""
    return read(TOP_OPERATORS, {"since": since, "limit": limit}, timeout_ms=15000)
