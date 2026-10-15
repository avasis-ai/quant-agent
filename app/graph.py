"""FalkorDB access for Sniff. Reads go through GRAPH.RO_QUERY with a timeout."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from falkordb import FalkorDB, Node, Path as FPath, Edge

GRAPH = os.environ.get("SNIFF_GRAPH", "lineage")
READ_TIMEOUT_MS = int(os.environ.get("SNIFF_QUERY_TIMEOUT_MS", "8000"))


def _password() -> str | None:
    if os.environ.get("FALKORDB_PASSWORD"):
        return os.environ["FALKORDB_PASSWORD"]
    for f in (os.environ.get("FALKORDB_PASSWORD_FILE"), "/opt/lineage/env/falkordb.env", ".falkordb.pw"):
        if f and Path(f).exists():
            text = Path(f).read_text().strip()
            for line in text.splitlines():
                if line.startswith("FALKORDB_PASSWORD="):
                    return line.split("=", 1)[1]
            if "=" not in text:
                return text
    return None


@lru_cache(maxsize=1)
def graph():
    db = FalkorDB(host=os.environ.get("FALKORDB_HOST", "127.0.0.1"),
                  port=int(os.environ.get("FALKORDB_PORT", "6379")), password=_password())
    return db.select_graph(GRAPH)


def plain(v):
    """Turn FalkorDB result values into JSON-friendly data."""
    if isinstance(v, Node):
        return {"id": v.id, "labels": list(v.labels or []), **(v.properties or {})}
    if isinstance(v, Edge):
        return {"id": v.id, "type": v.relation, "src": v.src_node, "dst": v.dest_node, **(v.properties or {})}
    if isinstance(v, FPath):
        return {"nodes": [plain(n) for n in v.nodes()], "edges": [plain(e) for e in v.edges()]}
    if isinstance(v, list):
        return [plain(x) for x in v]
    if isinstance(v, dict):
        return {k: plain(x) for k, x in v.items()}
    return v


def read(cypher: str, params: dict | None = None, timeout_ms: int | None = None) -> list[dict]:
    res = graph().ro_query(cypher, params or {}, timeout=timeout_ms or READ_TIMEOUT_MS)
    cols = [h[1] if isinstance(h, (list, tuple)) else h for h in res.header]
    return [{c: plain(v) for c, v in zip(cols, row)} for row in res.result_set]


def write(cypher: str, params: dict | None = None, timeout_ms: int = 0):
    return graph().query(cypher, params or {}, timeout=timeout_ms or None)
