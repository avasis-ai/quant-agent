"""Snapshot CSVs -> FalkorDB bulk-loader CSVs for the `lineage` graph.

    python build/transform.py <snapshot_dir> <out_dir> [--hub-cutoff 200]

Decisions (see docs/GRAPH.md):
- Only pump.fun launches: mint ends in "pump" (pump.fun's vanity suffix) or the create was seen on the
  pump.fun program on chain. Older collector rows also hold other launchpads and existing tokens
  "reported as new" (e.g. BONK), which must not become graph facts.
- Hub cut: a funder that funded more than --hub-cutoff wallets is a :Hub (likely an exchange). Hub edges
  are kept but queries never walk through a hub, or every coin would link to every other.
- Handles are normalised (lowercase, x.com/twitter.com URLs reduced to the handle, communities kept as
  their own platform) and junk/famous handles are dropped.
- Sniper rarity: each sniper wallet gets idf = ln(coins sniped in the snapshot / coins this wallet sniped).
  Wallets with more than 100 snipes are marked kind 'bot'; shared-sniper links ignore them.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import duckdb

JUNK_X = {"i", "home", "search", "intent", "share", "hashtag", "explore", "settings", "messages",
          "notifications", "compose", "status", "x", "twitter", "login", "signup", "tos", "privacy"}
FAMOUS_X = {"elonmusk", "realdonaldtrump", "cz_binance", "pumpdotfun", "solana", "binance", "coinbase",
            "potus", "whitehouse", "vitalikbuterin", "aeyakovenko", "rajgokal", "kanyewest", "nasa", "spacex",
            "tesla", "openai", "sama", "jupiterexchange", "raydiumprotocol", "phantom", "dexscreener",
            "barackobama", "nytimes", "cnn", "bbcbreaking", "foxnews", "mrbeast", "drake", "billgates"}
GENERIC_SITES = {"x.com", "twitter.com", "t.me", "telegram.me", "pump.fun", "youtube.com", "youtu.be",
                 "tiktok.com", "instagram.com", "facebook.com", "google.com", "dexscreener.com", "reddit.com",
                 "github.com", "medium.com", "linktr.ee", "discord.gg", "discord.com", "wikipedia.org",
                 "en.wikipedia.org", "solscan.io", "birdeye.so", "gmgn.ai", "coinmarketcap.com", "coingecko.com",
                 "truthsocial.com", "bsky.app", "threads.net", "vm.tiktok.com", "m.youtube.com"}


def sql_list(xs) -> str:
    return ", ".join("'" + x.replace("'", "''") + "'" for x in sorted(xs))


def build(snap: Path, out: Path, hub_cutoff: int) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    db = duckdb.connect()
    db.execute("SET threads TO 4")
    db.execute("SET TimeZone = 'UTC'")
    src = lambda name: f"read_csv_auto('{snap / (name + '.csv.gz')}', header=true, all_varchar=false, sample_size=-1)"

    # snapshot time: newest launch seen
    db.execute(f"CREATE TABLE raw_coins AS SELECT * FROM {src('coins')}")
    snap_ts = db.execute("SELECT max(created_at) FROM raw_coins").fetchone()[0]

    # ---- coins (pump.fun launches only) -----------------------------------------
    db.execute("""
        CREATE TABLE coins AS
        SELECT DISTINCT ON (c.mint) c.*, h.dead_at_minute
        FROM raw_coins c
        LEFT JOIN (SELECT mint, min(dead_at_minute) dead_at_minute FROM {hold} GROUP BY mint) h USING (mint)
        WHERE c.creator IS NOT NULL
          AND (c.mint LIKE '%pump' OR c.create_source = 'chain')
          AND c.created_at >= TIMESTAMPTZ '2026-09-01'
        ORDER BY c.mint, c.created_at
    """.format(hold=src("hold_summary")))
    db.execute("""
        COPY (
          SELECT mint AS "mint:ID(Coin)",
                 left(trim(regexp_replace(name, '[\\x00-\\x1f\\x7f]+', ' ', 'g')), 80) AS "name:STRING",
                 left(trim(regexp_replace(symbol, '[\\x00-\\x1f\\x7f]+', ' ', 'g')), 32) AS "symbol:STRING",
                 epoch(created_at)::BIGINT AS "created_at:INT",
                 (graduated_at IS NOT NULL) AS "graduated:BOOL",
                 epoch(graduated_at)::BIGINT AS "graduated_at:INT",
                 round(mcap_usd_2m, 2) AS "mcap_2m:DOUBLE", round(mcap_usd_10m, 2) AS "mcap_10m:DOUBLE",
                 round(mcap_usd_120m, 2) AS "mcap_120m:DOUBLE", round(ath_mcap_usd, 2) AS "ath_usd:DOUBLE",
                 dead_at_minute::BIGINT AS "died_min:INT",
                 CASE WHEN graduated_at IS NOT NULL THEN 'graduated'
                      WHEN created_at < TIMESTAMPTZ '{snap}' - INTERVAL 24 HOUR THEN 'never_graduated'
                      ELSE 'too_new' END AS "outcome:STRING",
                 trades_5m::BIGINT AS "trades_5m:INT", uniq_wallets_5m::BIGINT AS "buyers_5m:INT",
                 creator_sold_by_5m AS "dev_sold_5m:BOOL"
          FROM coins
        ) TO '{out}/Coin.csv' (HEADER, DELIMITER ',')
    """.replace("{out}", str(out)).replace("{snap}", str(snap_ts)))

    # ---- funding edges, hubs ----------------------------------------------------------
    db.execute(f"""
        CREATE TABLE fund AS
        SELECT DISTINCT ON (wallet, funder) wallet, funder, funded_at, lamports, depth
        FROM {src('funders')}
        WHERE ok AND funder IS NOT NULL AND wallet IS NOT NULL AND funder <> wallet
        ORDER BY wallet, funder, funded_at
    """)
    db.execute("CREATE TABLE outdeg AS SELECT funder AS addr, count(DISTINCT wallet) deg FROM fund GROUP BY 1")
    db.execute(f"CREATE TABLE hubs AS SELECT addr, deg FROM outdeg WHERE deg > {int(hub_cutoff)}")

    # ---- snipes -------------------------------------------------------------------------
    db.execute(f"""
        CREATE TABLE snipes AS
        SELECT s.wallet, s.mint, min(s."at") sniped_at FROM {src('snipes')} s JOIN coins c USING (mint)
        WHERE s.wallet IS NOT NULL GROUP BY 1, 2
    """)
    db.execute("""
        CREATE TABLE sniper AS
        SELECT wallet AS addr, count(*) n,
               ln((SELECT count(DISTINCT mint) FROM snipes) / count(*)) idf
        FROM snipes GROUP BY 1
    """)

    # ---- creators -------------------------------------------------------------------------
    db.execute(f"CREATE TABLE creators AS SELECT * FROM {src('creators')}")
    db.execute("""
        CREATE TABLE created AS
        SELECT creator AS addr, count(*) launches, sum((graduated_at IS NOT NULL)::int)::BIGINT graduations,
               min(created_at) first_launch
        FROM coins GROUP BY 1
    """)

    # ---- wallets (everything that is not a hub) -----------------------------------------
    db.execute("""
        CREATE TABLE wallets AS
        WITH addrs AS (
          SELECT addr FROM created
          UNION SELECT wallet FROM fund UNION SELECT funder FROM fund
          UNION SELECT addr FROM sniper
        )
        SELECT a.addr, coalesce(cr.launches, 0) launches, coalesce(cr.graduations, 0) graduations,
               coalesce(sn.n, 0) snipes, sn.idf, coalesce(od.deg, 0) funded,
               epoch(cm.wallet_first_ts)::BIGINT first_seen,
               CASE WHEN sn.n > 100 THEN 'bot'
                    WHEN cr.launches > 0 AND sn.n > 0 THEN 'creator+sniper'
                    WHEN cr.launches > 0 THEN 'creator'
                    WHEN sn.n > 0 THEN 'sniper'
                    ELSE 'funder' END kind
        FROM addrs a
        LEFT JOIN created cr ON cr.addr = a.addr
        LEFT JOIN sniper sn ON sn.addr = a.addr
        LEFT JOIN outdeg od ON od.addr = a.addr
        LEFT JOIN (SELECT DISTINCT ON (creator) creator, wallet_first_ts FROM creators ORDER BY creator) cm ON cm.creator = a.addr
        WHERE a.addr NOT IN (SELECT addr FROM hubs)
    """)
    db.execute(f"""
        COPY (SELECT addr AS "addr:ID(W)", launches AS "launches:INT", graduations AS "graduations:INT",
                     snipes AS "snipes:INT", round(idf, 4) AS "idf:DOUBLE", funded AS "funded:INT",
                     first_seen AS "first_seen:INT", kind AS "kind:STRING" FROM wallets)
        TO '{out}/Wallet.csv' (HEADER)
    """)
    db.execute(f"""
        COPY (SELECT h.addr AS "addr:ID(W)", h.deg AS "degree:INT", 'unlabelled hub' AS "label:STRING",
                     coalesce(cr.launches, 0) AS "launches:INT",
                     round((SELECT avg((f.wallet IN (SELECT addr FROM created))::int) FROM fund f WHERE f.funder = h.addr), 3)
                       AS "creator_share:DOUBLE"
              FROM hubs h LEFT JOIN created cr ON cr.addr = h.addr)
        TO '{out}/Hub.csv' (HEADER)
    """)

    # ---- edges ---------------------------------------------------------------------------
    db.execute(f"""
        COPY (SELECT creator AS ":START_ID(W)", mint AS ":END_ID(Coin)", epoch(created_at)::BIGINT AS "at:INT"
              FROM coins) TO '{out}/CREATED.csv' (HEADER)
    """)
    db.execute(f"""
        COPY (SELECT funder AS ":START_ID(W)", wallet AS ":END_ID(W)", epoch(funded_at)::BIGINT AS "at:INT",
                     round(lamports / 1e9, 4) AS "sol:DOUBLE", depth::BIGINT AS "depth:INT"
              FROM fund WHERE wallet NOT IN (SELECT addr FROM hubs))
        TO '{out}/FUNDED.csv' (HEADER)
    """)
    db.execute(f"""
        COPY (SELECT wallet AS ":START_ID(W)", mint AS ":END_ID(Coin)", epoch(sniped_at)::BIGINT AS "at:INT",
                     (row_number() OVER (PARTITION BY mint ORDER BY sniped_at, wallet))::BIGINT AS "rank:INT"
              FROM snipes) TO '{out}/SNIPED.csv' (HEADER)
    """)

    # ---- handles ---------------------------------------------------------------------------
    db.execute(f"CREATE TABLE meta AS SELECT m.* FROM {src('metadata')} m JOIN coins c USING (mint)")
    db.execute(f"""
        CREATE TABLE links AS
        WITH x AS (
          SELECT mint, lower(trim(twitter)) t FROM meta WHERE twitter IS NOT NULL AND trim(twitter) <> ''
        ), xn AS (
          SELECT mint,
            CASE
              WHEN regexp_matches(t, '(x|twitter)\\.com/i/communities/([0-9]+)') THEN 'x_community'
              ELSE 'x' END platform,
            CASE
              WHEN regexp_matches(t, '(x|twitter)\\.com/i/communities/([0-9]+)')
                THEN regexp_extract(t, 'communities/([0-9]+)', 1)
              WHEN regexp_matches(t, '(x|twitter)\\.com/')
                THEN regexp_extract(t, '(?:x|twitter)\\.com/@?([a-z0-9_]+)', 1)
              ELSE regexp_extract(ltrim(t, '@'), '^([a-z0-9_]+)', 1) END handle
          FROM x
        ), tg AS (
          SELECT mint, 'telegram' platform,
            CASE WHEN regexp_matches(lower(telegram), 't(elegram)?\\.me/')
                 THEN regexp_extract(lower(telegram), 't(?:elegram)?\\.me/([a-z0-9_+]+)', 1)
                 ELSE regexp_extract(ltrim(lower(trim(telegram)), '@'), '^([a-z0-9_+]+)', 1) END handle
          FROM meta WHERE telegram IS NOT NULL AND trim(telegram) <> ''
        ), web AS (
          SELECT mint, 'site' platform,
                 regexp_extract(regexp_replace(lower(trim(website_domain)), '^www\\.', ''), '^([a-z0-9][a-z0-9.-]*[a-z0-9])', 1) handle
          FROM meta WHERE website_domain IS NOT NULL AND trim(website_domain) <> ''
        )
        SELECT DISTINCT mint, platform, handle FROM (
          SELECT * FROM xn UNION ALL SELECT * FROM tg UNION ALL SELECT * FROM web
        ) WHERE handle IS NOT NULL AND length(handle) >= 2
          AND NOT (platform = 'x' AND (handle IN ({sql_list(JUNK_X)}) OR handle IN ({sql_list(FAMOUS_X)})))
          AND NOT (platform = 'site' AND handle IN ({sql_list(GENERIC_SITES)}))
          AND NOT (platform = 'telegram' AND handle IN ('joinchat', 's', 'share', 'addstickers', 'pumpdotfun'))
    """)
    db.execute("CREATE TABLE handles AS SELECT platform || ':' || handle AS hid, platform, handle, count(*) coins FROM links GROUP BY 1, 2, 3")
    db.execute(f"""
        COPY (SELECT hid AS "hid:ID(H)", platform AS "platform:STRING", handle AS "handle:STRING", coins AS "coins:INT"
              FROM handles) TO '{out}/Handle.csv' (HEADER)
    """)
    db.execute(f"""
        COPY (SELECT mint AS ":START_ID(Coin)", platform || ':' || handle AS ":END_ID(H)", platform AS "kind:STRING"
              FROM links) TO '{out}/LINKS.csv' (HEADER)
    """)

    counts = {name: db.execute(f"SELECT count(*) FROM read_csv_auto('{out}/{name}.csv', header=true)").fetchone()[0]
              for name in ["Coin", "Wallet", "Hub", "Handle", "CREATED", "FUNDED", "SNIPED", "LINKS"]}
    stats = {
        "snapshot": snap.name, "snapshot_ts": str(snap_ts), "hub_cutoff": hub_cutoff, "counts": counts,
        "dropped_non_pump_coins": db.execute("SELECT count(*) FROM raw_coins").fetchone()[0] - counts["Coin"],
        "hub_edges": db.execute("SELECT count(*) FROM fund WHERE funder IN (SELECT addr FROM hubs)").fetchone()[0],
        "bot_snipers": db.execute("SELECT count(*) FROM sniper WHERE n > 100").fetchone()[0],
        "seconds": round(time.time() - t0, 1),
    }
    (out / "stats.json").write_text(json.dumps(stats, indent=1))
    return stats


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("snapshot", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--hub-cutoff", type=int, default=200)
    a = ap.parse_args()
    print(json.dumps(build(a.snapshot, a.out, a.hub_cutoff), indent=1))
