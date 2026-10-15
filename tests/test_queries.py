"""The 8 core queries, checked against DuckDB ground truth on the same bulk-loader CSVs.

Needs the graph loaded from the same build:
    SNIFF_BUILD_DIR=build/out/20261014T1845Z FALKORDB_PORT=16379 FALKORDB_PASSWORD_FILE=.falkordb.pw pytest tests/test_queries.py
"""
from __future__ import annotations

import json
import os
from collections import defaultdict, deque
from pathlib import Path

import duckdb
import pytest

BUILD = Path(os.environ.get("SNIFF_BUILD_DIR", "build/out/20261014T1845Z"))
N = 6  # samples per question

pytestmark = pytest.mark.skipif(not (BUILD / "Coin.csv").exists(), reason="no build output")


@pytest.fixture(scope="module")
def q():
    from app import queries
    from app.graph import read
    try:
        read("RETURN 1 AS ok")
    except Exception as e:  # noqa: BLE001
        pytest.skip(f"FalkorDB not reachable: {e}")
    return queries


@pytest.fixture(scope="module")
def db():
    d = duckdb.connect()
    cols = {
        "coin": ('"mint:ID(Coin)" mint, "graduated:BOOL" graduated, "created_at:INT" created_at', "Coin"),
        "wallet": ('"addr:ID(W)" addr, "snipes:INT" snipes, "idf:DOUBLE" idf, "launches:INT" launches', "Wallet"),
        "hub": ('"addr:ID(W)" addr', "Hub"),
        "handle": ('"hid:ID(H)" hid, "platform:STRING" platform, "handle:STRING" handle, "coins:INT" coins', "Handle"),
        "created": ('":START_ID(W)" w, ":END_ID(Coin)" mint', "CREATED"),
        "funded": ('":START_ID(W)" f, ":END_ID(W)" w', "FUNDED"),
        "sniped": ('":START_ID(W)" w, ":END_ID(Coin)" mint', "SNIPED"),
        "links": ('":START_ID(Coin)" mint, ":END_ID(H)" hid', "LINKS"),
    }
    for name, (sel, f) in cols.items():
        d.execute(f"CREATE TABLE {name} AS SELECT {sel} FROM read_csv_auto('{BUILD / (f + '.csv')}', header=true, all_varchar=false)")
    d.execute("CREATE TABLE funded_nohub AS SELECT * FROM funded WHERE f NOT IN (SELECT addr FROM hub)")
    return d


EXPECTED: dict[str, list] = defaultdict(list)


def teardown_module(_m):
    out = Path(__file__).parent / f"expected_{BUILD.name}.json"
    if EXPECTED:
        out.write_text(json.dumps(EXPECTED, indent=1, default=str))


# 1 coin_dossier -----------------------------------------------------------------------------------
def test_coin_dossier(q, db):
    samples = db.sql(f"""SELECT c.mint FROM created c JOIN (SELECT w FROM created GROUP BY w HAVING count(*) BETWEEN 2 AND 400) s USING (w)
                        ORDER BY hash(c.mint) LIMIT {N}""").fetchall()
    for (mint,) in samples:
        others, grads = db.sql(f"""SELECT count(*), coalesce(sum(o.graduated::int), 0) FROM created c
            JOIN created c2 ON c2.w = c.w AND c2.mint <> c.mint JOIN coin o ON o.mint = c2.mint WHERE c.mint = '{mint}'""").fetchone()
        g = q.coin_dossier(mint)
        assert g is not None
        assert (g["others"], int(g["other_grads"])) == (others, grads), mint
        EXPECTED["coin_dossier"].append({"mint": mint, "others": others, "other_grads": grads})


# 2 funding_trail --------------------------------------------------------------------------------------
def test_funding_trail(q, db):
    samples = db.sql(f"SELECT DISTINCT w FROM funded_nohub ORDER BY hash(w) LIMIT {N}").fetchall()
    for (addr,) in samples:
        rows = db.sql(f"""
            WITH RECURSIVE up(a, d) AS (SELECT f, 1 FROM funded WHERE w = '{addr}'
              UNION ALL SELECT fu.f, up.d + 1 FROM funded fu JOIN up ON fu.w = up.a WHERE up.d < 3)
            SELECT count(*) FROM up""").fetchone()[0]
        g = q.funding_trail(addr)
        if rows < 60:
            assert len(g) == rows, addr
        EXPECTED["funding_trail"].append({"addr": addr, "paths": rows})


# 3 siblings --------------------------------------------------------------------------------------------
def test_siblings(q, db):
    samples = db.sql(f"""SELECT DISTINCT c.mint FROM created c JOIN funded_nohub f ON f.w = c.w
        WHERE f.f IN (SELECT f FROM funded_nohub GROUP BY f HAVING count(*) BETWEEN 3 AND 200)
          AND f.f IN (SELECT addr FROM wallet)
        ORDER BY hash(c.mint) LIMIT {N}""").fetchall()
    for (mint,) in samples:
        want = {r[0]: (r[1], r[2], r[3]) for r in db.sql(f"""
            SELECT f.f, count(DISTINCT s.w), count(DISTINCT sc.mint), sum(co.graduated::int)
            FROM created c JOIN funded_nohub f ON f.w = c.w
            JOIN funded_nohub s ON s.f = f.f AND s.w <> c.w
            JOIN created sc ON sc.w = s.w JOIN coin co ON co.mint = sc.mint
            WHERE c.mint = '{mint}' AND f.f IN (SELECT addr FROM wallet) GROUP BY 1""").fetchall()}
        got = {r["funder"]: (r["creators"], r["coins"], int(r["graduated"])) for r in q.siblings(mint)}
        top = dict(sorted(want.items(), key=lambda kv: -kv[1][0])[:20])
        assert {k: got[k] for k in top if k in got} == {k: top[k] for k in top if k in got}
        assert len(got) == min(20, len(want)), mint
        EXPECTED["siblings"].append({"mint": mint, "funders": len(want), "creators": sum(v[0] for v in want.values())})


# 4 shared_snipers ---------------------------------------------------------------------------------------
def test_shared_snipers(q, db):
    samples = db.sql(f"""SELECT s.mint FROM sniped s JOIN wallet w ON w.addr = s.w WHERE w.snipes BETWEEN 3 AND 100
        GROUP BY 1 HAVING count(*) >= 2 ORDER BY hash(s.mint) LIMIT {N}""").fetchall()
    for (mint,) in samples:
        want = {r[0]: (r[1], round(r[2], 3)) for r in db.sql(f"""
            SELECT o.mint, count(*), sum(w.idf) FROM sniped s JOIN wallet w ON w.addr = s.w AND w.snipes <= 100
            JOIN sniped o ON o.w = s.w AND o.mint <> s.mint WHERE s.mint = '{mint}' GROUP BY 1""").fetchall()}
        got = q.shared_snipers(mint)
        assert len(got) == min(20, len(want)), mint
        for r in got:
            assert want[r["mint"]] == (r["shared"], round(r["score"], 3)), (mint, r["mint"])
        if want:
            assert round(got[0]["score"], 3) == max(v[1] for v in want.values())
        EXPECTED["shared_snipers"].append({"mint": mint, "coins": len(want)})


# 5 shared_handles ----------------------------------------------------------------------------------------
def test_shared_handles(q, db):
    samples = db.sql(f"""SELECT l.mint FROM links l JOIN handle h USING (hid) WHERE h.coins BETWEEN 3 AND 300
        ORDER BY hash(l.mint) LIMIT {N}""").fetchall()
    for (mint,) in samples:
        want = {r[0]: (r[1], r[2], r[3]) for r in db.sql(f"""
            SELECT l.hid, count(DISTINCT o.mint), count(DISTINCT c.w), sum(co.graduated::int)
            FROM links l JOIN links o ON o.hid = l.hid AND o.mint <> l.mint
            JOIN created c ON c.mint = o.mint JOIN coin co ON co.mint = o.mint
            WHERE l.mint = '{mint}' GROUP BY 1""").fetchall()}
        got = {f'{r["platform"]}:{r["handle"]}': (r["other_coins"], r["other_creators"], int(r["graduated"]))
               for r in q.shared_handles(mint)}
        assert got == want, mint
        EXPECTED["shared_handles"].append({"mint": mint, "handles": {k: v[0] for k, v in want.items()}})


# 6 ring (union-find in Python as the independent check) -------------------------------------------------
@pytest.fixture(scope="module")
def components(db):
    parent: dict[str, str] = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for f, w in db.sql("SELECT f, w FROM funded_nohub").fetchall():
        union("w:" + f, "w:" + w)
    for w, m in db.sql("SELECT w, mint FROM created WHERE w NOT IN (SELECT addr FROM hub)").fetchall():
        union("w:" + w, "c:" + m)
    return find


def test_ring(q, db, components):
    samples = db.sql(f"""SELECT c.mint FROM created c JOIN funded_nohub f ON f.w = c.w ORDER BY hash(c.mint) LIMIT {N}""").fetchall()
    creators = {r[0] for r in db.sql("SELECT DISTINCT w FROM created").fetchall()}
    grads = {r[0] for r in db.sql("SELECT mint FROM coin WHERE graduated").fetchall()}
    by_root: dict[str, list[str]] = defaultdict(list)
    for (w,) in db.sql("SELECT DISTINCT w FROM created WHERE w NOT IN (SELECT addr FROM hub)").fetchall():
        by_root[components("w:" + w)].append(w)
    coins_by_root: dict[str, list[str]] = defaultdict(list)
    for (m,) in db.sql("SELECT mint FROM created WHERE w NOT IN (SELECT addr FROM hub)").fetchall():
        coins_by_root[components("c:" + m)].append(m)
    for (mint,) in samples:
        root = components("c:" + mint)
        n_creators = len([w for w in by_root[root] if w in creators])
        coins = coins_by_root[root]
        g = q.ring(mint=mint)
        if n_creators < 2:
            assert g is None, mint
            continue
        assert g is not None, mint
        assert (g["ring"]["creators"], int(g["ring"]["coins"]), int(g["ring"]["graduations"])) == \
               (n_creators, len(coins), sum(1 for m in coins if m in grads)), mint
        EXPECTED["ring"].append({"mint": mint, "creators": n_creators, "coins": len(coins)})


# 7 connect (BFS in Python as the independent check) ----------------------------------------------------------
def test_connect(q, db):
    adj: dict[str, set[str]] = defaultdict(set)
    hubs = {r[0] for r in db.sql("SELECT addr FROM hub").fetchall()}
    for f, w in db.sql("SELECT f, w FROM funded").fetchall():
        if f not in hubs:
            adj["w:" + f].add("w:" + w); adj["w:" + w].add("w:" + f)
    for w, m in db.sql("SELECT w, mint FROM created").fetchall():
        if w not in hubs:
            adj["w:" + w].add("c:" + m); adj["c:" + m].add("w:" + w)
    for m, h in db.sql("SELECT l.mint, l.hid FROM links l JOIN handle h USING (hid) WHERE h.coins <= 200").fetchall():
        adj["c:" + m].add("h:" + h); adj["h:" + h].add("c:" + m)

    def dist(a, b, cap=6):
        seen, dq = {a: 0}, deque([a])
        while dq:
            x = dq.popleft()
            if x == b:
                return seen[x]
            if seen[x] >= cap:
                continue
            for y in adj[x]:
                if y not in seen:
                    seen[y] = seen[x] + 1
                    dq.append(y)
        return None

    pairs = db.sql(f"""SELECT c1.mint, c2.mint FROM created c1 JOIN funded_nohub f1 ON f1.w = c1.w
        JOIN funded_nohub f2 ON f2.f = f1.f AND f2.w <> f1.w JOIN created c2 ON c2.w = f2.w
        WHERE f1.f IN (SELECT addr FROM wallet) ORDER BY hash(c1.mint || c2.mint) LIMIT {N}""").fetchall()
    for a, b in pairs:
        want = dist("c:" + a, "c:" + b)
        got = q.connect(a, b)
        assert got, (a, b)
        assert got[0]["hops"] == want, (a, b)
        EXPECTED["connect"].append({"a": a, "b": b, "hops": want})


# 8 top_operators ------------------------------------------------------------------------------------------
def test_top_operators(q, db):
    since = db.sql("SELECT max(created_at) - 3 * 86400 FROM coin").fetchone()[0]
    want = db.sql(f"""SELECT f.f, count(DISTINCT f.w), count(*), sum(co.graduated::int)
        FROM funded_nohub f JOIN created c ON c.w = f.w JOIN coin co ON co.mint = c.mint
        WHERE co.created_at >= {since} AND f.f IN (SELECT addr FROM wallet)
        GROUP BY 1 ORDER BY 2 DESC, 3 DESC LIMIT 20""").fetchall()
    got = q.top_operators(since)
    assert [(r["creators"], r["coins"]) for r in got] == [(w[1], w[2]) for w in want]
    top = {w[0] for w in want if (w[1], w[2]) != (want[-1][1], want[-1][2])}  # ignore ties at the cut
    assert top <= {r["funder"] for r in got}
    EXPECTED["top_operators"] = [{"funder": w[0], "creators": w[1], "coins": w[2], "graduated": w[3]} for w in want[:5]]
