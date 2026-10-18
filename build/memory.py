"""Initialise memory indexes and optionally record a real, no-AI public coin investigation.

    python -m build.memory
    python -m build.memory --mint <public-mint>
"""
from __future__ import annotations

import argparse
import json

from app import knowledge_graph as kg, memory, tools


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mint", help="Optionally seed with a real investigation from the lineage graph.")
    args = parser.parse_args()
    kg.ensure_indexes("memory")
    if not args.mint:
        print(json.dumps({"graph": "memory", "indexes": "ready"}))
        return
    mint = tools._need_addr(args.mint, "mint")
    ctx = memory.begin(None, entity="coin:" + mint)
    ev = tools.Evidence(memory=ctx)
    results = {}
    for name in ("coin_dossier", "siblings", "shared_handles", "shared_snipers"):
        result, ok = tools.run_tool(ev, name, {"mint": mint})
        if not ok:
            raise RuntimeError("Public investigation tool failed: " + name)
        results[name] = result
        if name == "coin_dossier" and not result.get("found"):
            break
    if not ctx.available or ctx.error:
        raise RuntimeError("Memory did not save completely.")
    print(json.dumps({"graph": "memory", "session_id": ctx.sid, "evidence_count": len(ev.items),
                      "coin_found": results["coin_dossier"].get("found", False),
                      "view": "/memory?session=" + ctx.sid}))


if __name__ == "__main__":
    main()
