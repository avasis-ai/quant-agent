"""Indexes for the lineage graph. Idempotent: existing indexes are skipped.

    FALKORDB_PORT=16379 python -m build.indexes
"""
from app.graph import graph

RANGE = [("Coin", "mint"), ("Coin", "created_at"), ("Wallet", "addr"), ("Hub", "addr"),
         ("Handle", "hid"), ("Handle", "handle"), ("Ring", "rid")]


def main() -> None:
    g = graph()
    have = {(r[0], p) for r in g.query("CALL db.indexes() YIELD label, properties RETURN label, properties").result_set
            for p in r[1]}
    for label, prop in RANGE:
        if (label, prop) in have:
            print("exists", label, prop)
            continue
        g.query(f"CREATE INDEX FOR (n:{label}) ON (n.{prop})")
        print("created", label, prop)
    if ("Coin", "name") not in have:
        # FalkorDB 6.0.2: the 3-argument db.idx.fulltext.createNodeIndex in the docs is refused
        g.query("CREATE FULLTEXT INDEX FOR (c:Coin) ON (c.name, c.symbol)")
        print("created fulltext Coin(name, symbol)")
    for r in g.query("CALL db.indexes() YIELD label, properties, types, status RETURN label, properties, types, status").result_set:
        print(r)


if __name__ == "__main__":
    main()
