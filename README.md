# Sniff, by Quant Agent

Sniff any coin before you buy.

Entry for WeMakeDevs × FalkorDB **Graph Hacks: Context for AI Agents** (Track 01, Agents That Act on Connected Data).
All code in this repository is written during the event window (Oct 15–18, 2026 IST).

## Ask Sniff (Day 2)

`POST /api/ask {"question": "...", "mint": "<optional coin address>"}` investigates a coin.

- **Tools** (`app/tools.py`): `search_coins`, `coin_dossier`, `funding_trail`, `siblings`, `shared_snipers`,
  `shared_handles`, `ring`, `connect`, `top_operators`. Each is a fixed read-only Cypher query on FalkorDB.
- **Evidence:** every tool result carries evidence ids (`E1`, `E2`, …). Each item lists the tool, its arguments,
  a one-line summary, and the nodes and edges to highlight, keyed `coin:<mint>`, `wallet:<addr>`, `hub:<addr>`,
  `handle:<hid>` or `ring:<rid>`.
- **Agent** (`app/agent.py`): Claude plans the tool calls (up to 8), then writes a short verdict where each
  fact cites evidence ids. Citations are checked against the evidence actually returned and against the claim:
  a sentence about socials may only cite `shared_handles` evidence, early buyers `shared_snipers`, and so on.
  Unknown or mismatched ids are dropped, and a sentence left with no valid citation is dropped. A tool that
  finds nothing still returns a "none found" evidence id, so "no other coin reuses its socials" can be cited.
- **No AI key, or the AI call fails:** a fixed dossier built from the same tools answers instead, so the
  evidence never depends on the LLM.
- **Wording:** answers describe history only and end with the base-rate line ("3.7% of … launches graduated").
  They never say buy or sell.
- **Responses:** JSON by default, or server-sent events (`step`, `evidence`, `verdict`, `done`) with
  `Accept: text/event-stream`.
- **Keys:** a visitor's own key goes in the `x-anthropic-key` header. Without one, the site's key is used,
  limited per IP and per day.

## Use Sniff from your own agent (MCP)

The same 9 read-only graph tools are served over MCP (streamable HTTP) at `https://sniff.quantbase.live/mcp`.
No AI key is needed: every tool is a plain graph read, rate-limited per IP.

Claude Code:

```bash
claude mcp add --transport http sniff https://sniff.quantbase.live/mcp
```

Claude Desktop (Settings → Connectors → Add custom connector), or any client that takes a JSON config:

```json
{ "mcpServers": { "sniff": { "type": "http", "url": "https://sniff.quantbase.live/mcp" } } }
```

Then ask: "Use sniff to check who is behind <mint>". Every result carries evidence ids to cite.

## Eval

`tests/eval/questions.jsonl` holds 30 questions: the 8 graph questions, coin search, and 6 that must be refused
or answered with "no evidence" (price predictions, "is it safe", unknown coins). `python -m tests.eval.run_eval`
scores tool choice, citation validity and the history-not-advice policy, with a scripted Claude in CI and live
against the site (`--live https://sniff.quantbase.live --only-live`). Results: `docs/EVAL.md`.

Tests: `pytest tests` (unit tests use a fake graph and a fake Claude; the query tests need the live graph, see `docs/GRAPH.md`).

## The app (Day 3)

Live at **https://sniff.quantbase.live/app** (the landing page's "Try it" link).

- **Search** a coin by name, ticker or address, or tap an example: METHU (one payer behind 72 one-coin
  creators), Subprime Cat (the biggest funding ring), Women in Finance (socials reused across coins),
  Higher (a graduate).
- **The coin card** shows the fixed facts straight from the graph, with no AI involved: who made it, what
  else they made, who paid them, who else that payer funded, the funding ring, and reused socials
  (`GET /api/dossier?mint=`).
- **Sniff's answer** streams each graph check as it runs (`POST /api/ask` as server-sent events), then the
  written answer. Every `[E#]` tag in it is a piece of evidence returned by a tool.
- **The map** (Cytoscape.js 3.33.1) draws that evidence. Tapping an `[E#]` tag lights up exactly the
  nodes and edges it rests on. Graduated coins are green, coins that died are dashed, and exchange-like
  hubs are grey squares that end a trail.
- It works at 375 px wide, and with no AI key it falls back to the fixed summary.
- Links can be shared: `/app?mint=<address>`.

Screenshots are in `docs/shots/`.
