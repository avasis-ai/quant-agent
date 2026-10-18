"""Explicitly named writable graphs; the lineage read contract stays separate."""
from __future__ import annotations

import os
from functools import lru_cache
from threading import Lock

from falkordb import FalkorDB

from .graph import _password, plain

NAMES = {"memory", "brain"}
_ready: set[str] = set()
_lock = Lock()
INDEXES = {
    "memory": {"Session": ("sid",), "Question": ("qid",), "Evidence": ("eid", "call_key", "at"),
               "Coin": ("mint",), "Wallet": ("addr",), "Note": ("nid",)},
    "brain": {"Doc": ("did",), "Section": ("sid", "active"), "Entity": ("eid", "name"),
              "Decision": ("eid",), "Finding": ("eid",), "Metric": ("eid",),
              "Product": ("eid",), "Feature": ("eid",), "Policy": ("eid",)},
}


@lru_cache(maxsize=2)
def graph(name: str):
    if name not in NAMES:
        raise ValueError("Unknown knowledge graph.")
    return FalkorDB(host=os.environ.get("FALKORDB_HOST", "127.0.0.1"),
                    port=int(os.environ.get("FALKORDB_PORT", "6379")), password=_password(),
                    socket_connect_timeout=2, socket_timeout=15).select_graph(name)


def rows(result) -> list[dict]:
    cols = [h[1] if isinstance(h, (list, tuple)) else h for h in result.header]
    return [{c: plain(v) for c, v in zip(cols, row)} for row in result.result_set]


def read(name: str, cypher: str, params: dict | None = None) -> list[dict]:
    return rows(graph(name).ro_query(cypher, params or {}, timeout=8000))


def write(name: str, cypher: str, params: dict | None = None) -> list[dict]:
    return rows(graph(name).query(cypher, params or {}, timeout=8000))


def ensure_indexes(name: str) -> None:
    with _lock:
        if name in _ready:
            return
        g = graph(name)
        have = {(r[0], p) for r in g.query("CALL db.indexes() YIELD label, properties RETURN label, properties").result_set
                for p in r[1]}
        for label, props in INDEXES[name].items():
            for prop in props:
                if (label, prop) not in have:
                    g.query(f"CREATE INDEX FOR (n:{label}) ON (n.{prop})")
        if name == "brain" and ("Section", "text") not in have:
            g.query("CREATE FULLTEXT INDEX FOR (s:Section) ON (s.text, s.title)")
        _ready.add(name)
