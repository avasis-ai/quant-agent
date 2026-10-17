# Sniff, by Quant Agent

**Sniff any coin before you buy.** Paste a pump.fun meme coin and Sniff tells you who made it, who paid the
wallet that made it, what else those people launched, and how those coins ended. It walks a FalkorDB graph of
632,339 pump.fun launches and 424,007 wallets. Claude writes the answer, and every sentence in it links to the
part of the graph that proves it. Sniff shows history, not predictions.

Entry for WeMakeDevs × FalkorDB **Graph Hacks: Context for AI Agents**, Track 01 (Agents That Act on Connected
Data). Team **Quant Agent**. Built during the event window, Oct 15–18, 2026 (IST).

| | |
|---|---|
| **App** | https://sniff.quantbase.live |
| **Demo video** | https://youtu.be/YMQKpynEsI0 |
| **Blog post** | https://dev.to/quantbase/who-is-behind-this-meme-coin-building-sniff-on-a-graph-4nnc |
| **Bring your own Claude key** | https://sniff.quantbase.live/settings |
| **MCP endpoint (9 graph tools)** | `https://sniff.quantbase.live/mcp` |

| Ask | Evidence on the map | Phone |
|---|---|---|
| ![Live steps](docs/shots/02-streaming-steps.jpg) | ![Evidence highlight](docs/shots/04-evidence-highlight.jpg) | ![Mobile](docs/shots/06-mobile-answer.png) |

Try the **METHU** example: one wallet paid 72 brand-new creators, each launched exactly one coin, and none of
the 72 coins graduated.

## How it works

### The graph (`lineage`)

```mermaid
graph LR
  W[Wallet] -- CREATED --> C[Coin]
  W2[Wallet] -- FUNDED --> W
  H[Hub<br/>exchange-like, dead end] -- FUNDED --> W
  S[Wallet<br/>early buyer] -- SNIPED --> C
  C -- LINKS --> X[Handle<br/>X, Telegram, website]
  W -- IN_RING --> R[Ring]
```

| Node | Count | What it is |
|---|---|---|
| Coin | 632,339 | a pump.fun launch (other launchpads dropped) |
| Wallet | 424,007 | creators, their funders, early buyers |
| Hub | 89 | wallets that funded more than 200 others (exchanges, big farms) |
| Handle | 33,009 | a social account or website domain used on a coin |
| Ring | 6,556 | wallets and coins joined by funding and creation (≥ 2 creators) |

1,089,444 nodes and 1,513,175 relationships load in 30 s with the FalkorDB bulk loader (521 MB in memory).

### The agent

```mermaid
graph TD
  Q[Question or coin] --> L[Claude Sonnet 5.5<br/>up to 8 tool calls]
  L -- tool call --> T[9 read-only tools<br/>fixed Cypher on FalkorDB]
  T -- rows + evidence ids E1, E2… --> L
  L --> V[Answer, 2–5 sentences,<br/>each citing an E id]
  V --> K[Citation check<br/>unknown or off-topic ids removed]
  K --> U[App: answer + map that lights up each E id]
  T -. no key or AI error .-> D[Fixed dossier from the same tools]
  D --> U
```

- **Tools** (`app/tools.py`): `search_coins`, `coin_dossier`, `funding_trail`, `siblings`, `shared_snipers`,
  `shared_handles`, `ring`, `connect`, `top_operators`. Each one is a fixed, parameterised, read-only Cypher
  query (`app/queries.py`); the model never writes Cypher.
- **Evidence ids:** every tool result carries ids (`E1`, `E2`, …) naming the nodes and edges behind it.
- **Checked citations:** a sentence may only cite an id that a tool really returned, and only from a tool that
  can show that kind of claim (a sentence about socials must cite `shared_handles`). Anything else is removed,
  and a sentence left with no valid citation is dropped. A tool that finds nothing returns a "none found" id,
  so "no other coin reuses its socials" is cited too.
- **No key, or the AI is down:** a fixed dossier built from the same tools answers instead. The facts never
  depend on the model.
- **Wording:** answers describe history only and end with the base rate: 3.7% of the launches in this graph
  graduated.

### Why a graph

- **Money moves in hops.** "Who paid the wallet that made this coin, and who else did they pay?" is a 2–3 hop
  walk. In SQL it's a pile of self-joins; in Cypher it's one pattern.
- **Hubs are dead ends.** An exchange funds thousands of wallets, so walking through it links everyone to
  everyone. Hubs are their own label with no incoming funding edges, and no query walks through them.
- **Rings** come from `algo.WCC` over funding and creation edges. 3,824 of the 3,900 multi-creator clusters
  that our collector found by other means fall entirely inside one ring.
- **"How are these two connected?"** is `algo.SPpaths`, with hubs and platform-sized handles filtered out.

### FalkorDB features used

- `falkordb-bulk-insert` (bulk loader 1.2.0) with `--enforce-schema`, `--id-type STRING` and `-x none`.
- Range indexes on `Coin.mint`, `Coin.created_at`, `Wallet.addr`, `Hub.addr`, `Handle.hid`, `Handle.handle`,
  `Ring.rid`, and a full-text index on coin name and symbol (`db.idx.fulltext.queryNodes`).
- `algo.WCC` for rings and `algo.SPpaths` for `connect`.
- Read-only queries (`GRAPH.RO_QUERY`) with per-query timeouts. FalkorDB caps them at `TIMEOUT_MAX`, 15 s.
- FalkorDB 6.0.2 details that differ from the docs are in [`docs/GRAPH.md`](docs/GRAPH.md).

## Use Sniff from your own agent (MCP)

The same 9 tools are served over MCP (streamable HTTP). No AI key is needed: every tool is a plain graph read,
rate-limited per IP.

```bash
claude mcp add --transport http sniff https://sniff.quantbase.live/mcp
```

Any client that takes a JSON config:

```json
{ "mcpServers": { "sniff": { "type": "http", "url": "https://sniff.quantbase.live/mcp" } } }
```

Then ask: "Use sniff to check who is behind `<mint>`." Every result carries evidence ids to cite.

## API

- `POST /api/ask {"question": "...", "mint": "<optional>"}`: JSON, or server-sent events (`step`, `evidence`,
  `verdict`, `done`) with `Accept: text/event-stream`.
- `GET /api/dossier?mint=`: the fixed coin card, no AI.
- `GET /api/search?q=`: coin search by name, ticker or address.
- Share a coin: `/app?mint=<address>`.

## Eval

30 questions in `tests/eval/questions.jsonl`: the graph questions, coin search, and 6 that must be refused or
answered with "no evidence" (price calls, "is it safe", unknown coins). Full method in [`docs/EVAL.md`](docs/EVAL.md).

| Run | Questions | Right tools | Valid citations | No advice |
|---|---|---|---|---|
| Scripted Claude on the live graph (CI) | 30 | 30 | 30 | 30 |
| Live on the site, Claude Sonnet 5.5 | 10 | 10 | 10 | 10 |

Only 5 of the 10 live answers kept to 5 sentences, so answers are now capped at 5 cited sentences plus the
closing line.

## Your key

- **Visitors** can paste their own Claude key on `/settings`. It stays in that browser tab (sessionStorage),
  travels with each question in the `x-anthropic-key` header, and is never stored or logged by the server.
- **The site key** is set by the owner behind an admin passcode (stored as a scrypt hash). It is checked with
  one tiny call before it's saved, kept in a `chmod 600` env file, and only ever shown as `…last4`.
- Every log line masks anything shaped like a key. Without a key of their own, visitors share the site key with
  per-IP and daily limits.

## Honest limits

- **Explains, doesn't predict.** We tested the graph's signals (operator size, two-hop funding, reused socials,
  shared early buyers) against how 23,408 graduated coins did afterwards, using only what was known before each
  graduation. On their own they line up with outcomes (a reused social: −18 points in one-hour survival), but
  they add nothing once a coin's first minutes of trading are known (AUC change within ±0.01). Sniff tells you
  who is behind a coin and what their other coins did. It can't tell you what this one will do.
- **A snapshot.** The graph is built from data recorded up to 2026-10-14 18:45 UTC. Coins launched after that
  aren't in it yet.
- **Coverage.** Many creators have no recorded funder, so "no funder found" can mean we didn't see it, not that
  there wasn't one. Early-buyer data starts on Oct 8.
- Nothing here is financial advice.

## Run it yourself

```bash
pip install -r requirements.txt
# FalkorDB 6.x on localhost:6379 (docker run -p 6379:6379 falkordb/falkordb:latest)
python build/transform.py <snapshot-dir> build/out/<stamp>        # 8 s
falkordb-bulk-insert lineage --enforce-schema --id-type STRING -x none \
  -N Coin Coin.csv -N Wallet Wallet.csv -N Hub Hub.csv -N Handle Handle.csv \
  -R CREATED CREATED.csv -R FUNDED FUNDED.csv -R SNIPED SNIPED.csv -R LINKS LINKS.csv   # 30 s
python -m build.indexes && python -m build.rings                  # indexes, then WCC rings
uvicorn app.main:app --port 8080
pytest tests                                                      # live-graph tests need FALKORDB_PORT / FALKORDB_PASSWORD_FILE
```

Details and the snapshot's columns are in [`docs/GRAPH.md`](docs/GRAPH.md).

## What existed before the event

The QuantBase data collector, which records public pump.fun data, and the snapshot exported from it. Every
line in this repository (the graph build, queries, agent, app, MCP server, tests and docs) was written
between Oct 15 and Oct 18, 2026.

## AI assistance (disclosure)

Per rule 11: this project was built with AI coding assistants. Most of the code, tests and docs were
written by Claude Code (Anthropic) working under the team's direction. The team chose the problem and
the product, supplied the data from our own pump.fun collector, decided the graph model and its rules
(hubs as dead ends, the 200-wallet cutoff, sniper rarity weighting), set the claims policy ("history,
not a prediction"), and reviewed the work, including checking every core query against independent
DuckDB ground truth (`tests/test_queries.py`). The commit history shows the work as it happened during
the event. At runtime, Sniff's answers are written by Claude from the graph's evidence, as described above.

## License

MIT. See [LICENSE](LICENSE).
