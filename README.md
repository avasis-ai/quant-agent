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
  fact cites evidence ids. Citations are checked against the evidence actually returned, and unknown ids are dropped.
- **No AI key, or the AI call fails:** a fixed dossier built from the same tools answers instead, so the
  evidence never depends on the LLM.
- **Wording:** answers describe history only and end with the base-rate line ("3.7% of … launches graduated").
  They never say buy or sell.
- **Responses:** JSON by default, or server-sent events (`step`, `evidence`, `verdict`, `done`) with
  `Accept: text/event-stream`.
- **Keys:** a visitor's own key goes in the `x-anthropic-key` header. Without one, the site's key is used,
  limited per IP and per day.

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
