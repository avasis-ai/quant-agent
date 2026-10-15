# The `lineage` graph (Day 1, 2026-10-15)

Built from snapshot `20261014T1845Z` (public on-chain and market data recorded by the QuantBase collector, which existed before the event).

| | count |
|---|---|
| Coin | 632,339 (pump.fun launches only; 276,606 other rows dropped) |
| Wallet | 424,007 |
| Hub | 89 (funders of more than 200 wallets) |
| Handle | 33,009 |
| Ring | 6,556 |
| CREATED / FUNDED / SNIPED / LINKS / IN_RING | 632,339 / 307,948 / 431,155 / 141,733 / 51,402 |

The bulk load takes 30 s, the transform 8 s and WCC 2.9 s. `GRAPH.MEMORY USAGE` reports 521 MB.

## Decisions
- **pump.fun only:** a mint must end in `pump` or have its create seen on the pump.fun program. Older collector rows hold other launchpads and existing tokens "reported as new". BONK was one: its record shows a fake 2026-09-20 launch.
- **Hub cut at 200 funded wallets.** Creator share can't tell an exchange from a farm here, because the funder data only covers creators' funders: the largest funder (33,747 wallets) shows 80% creators. Hubs keep their edges plus a `creator_share`, but no query walks through them, and they have no incoming FUNDED edges.
- **Snipers:** each sniper wallet gets an idf weight, `ln(coins sniped / coins this wallet sniped)`. The 603 wallets with more than 100 snipes are `kind = bot` and are ignored by shared-sniper links.
- **Handles:** lowercased; x.com URLs reduced to the handle; X communities kept as their own platform; junk, famous and generic-site stoplists applied. Handles on more than 200 coins count as platforms in `connect`.
- **Rings:** `algo.WCC` over Wallet+Coin with FUNDED+CREATED (hubs excluded), keeping components with at least 2 creators. **Check against the collector's clusters:**
  - 3,824 of the 3,900 multi-creator collector clusters fall entirely inside one ring;
  - 443 rings merge several collector clusters (the most is 669).

## Verified on FalkorDB 6.0.2 (`CALL dbms.procedures()`)
- **Procedure names:**
  - `algo.WCC`, `algo.BFS` (upper case);
  - `algo.pageRank`, `algo.labelPropagation`, `algo.betweenness`, `algo.SPpaths`, `algo.SSpaths`, `algo.HarmonicCentrality`, `algo.MSF`, `algo.maxFlow`.
- **Full-text index:** the docs' 3-argument `db.idx.fulltext.createNodeIndex('Coin','name','symbol')` is refused. Use `CREATE FULLTEXT INDEX FOR (c:Coin) ON (c.name, c.symbol)`.
- **`WITH` projections** need `AS` aliases.
- **Query timeout:** may not exceed `TIMEOUT_MAX` (15 s).
- **Bulk loader:** its default escape character `\` breaks on coin names like `\`, so pass `-x none` (DuckDB doubles quotes instead).

## Core queries (`app/queries.py`), each checked against DuckDB in `tests/test_queries.py`
1. `coin_dossier`
2. `funding_trail`
3. `siblings`
4. `shared_snipers`
5. `shared_handles`
6. `ring` (checked with a Python union-find)
7. `connect` (checked with a Python BFS)
8. `top_operators`

The expected counts are in `tests/expected_20261014T1845Z.json`.

## Rebuild
```bash
python build/transform.py <snapshot> build/out/<stamp>
rsync build/out/<stamp>/ box:/opt/lineage/build/<stamp>/
falkordb-bulk-insert lineage --enforce-schema --id-type STRING -x none -N Coin Coin.csv -N Wallet Wallet.csv -N Hub Hub.csv -N Handle Handle.csv -R CREATED CREATED.csv -R FUNDED FUNDED.csv -R SNIPED SNIPED.csv -R LINKS LINKS.csv
python -m build.indexes && python -m build.rings
```
