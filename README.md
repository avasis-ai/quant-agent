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
