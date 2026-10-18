# Inline landing demo and coin-resolution fix

Completed on 18 October 2026, committed before the **23:20 IST hard stop**.
Author: **avasis-ai <abhay@avasis.ai>**. Branch: `final/qb-design`.
No deployment or push was performed.

The hero now investigates on `/`, with streamed steps, a cited answer, a compact
coin dossier and an animated evidence path. The full investigation link preserves
the selected mint and question. The rest of the landing-page story is preserved.

## Coin identity fix

- `/app?q=Subprime%20Cat` resolves Subprime Cat into the coin field and loads its
  own dossier. Names, tickers, mint addresses and questions naming a coin use a
  shared `/api/resolve` endpoint backed by the existing graph search tools.
- Exact coin names take priority over another coin's matching ticker. Longer
  questions search bounded four-word chunks so their named coin is not dropped.
  Ambiguous inline matches expose a mint picker; the chosen mint travels to `/app`.
- A fresh search cannot silently inherit METHU or another previous session coin.
  Explicit follow-ups, including “Who funded its creator?” and “And what did we
  learn?”, still reuse session evidence.
- Unknown inputs show **“Not in our snapshot (ends 14 Oct 2026)”**, with recorded
  suggestions. They do not start an AI investigation. Search outages have a
  separate retry message. The workspace clears stale results on a missing coin.

## Inline experience

The hero form and all six chips run inline. The implementation reuses `/api/ask`,
its shared-owner/visitor key handling, its existing rate limits and `SniffGraph`.
Dossier evidence IDs are prefixed separately from answer IDs to avoid collisions.
Clickable `[E#]` citations select their evidence and highlight the compact map;
all returned evidence remains inspectable below the answer.

The compact graph follows coin → creator → funder → ring, with actual relationship
arrow directions retained. Real hubs render as dead ends; missing relationships
are not invented. Ember colors, local fonts, controls and surfaces match the
existing page. Phone layouts stack the graph and answer, and reduced motion
removes the entrance and graph animation. Errors retain an already loaded dossier
and provide retry controls. Switching chips cancels the previous request.

All six chips were selected and verified against the local snapshot:

| Coin | Verified dossier | Mint |
| --- | --- | --- |
| METHU | 72-creator ring, 72 coins | `3LaVxn1Pp5gDjJZgGrpbQ8gRKj7GxgPE8cjF62Svpump` |
| Subprime Cat | 943-creator ring, 957 coins | `2f6jt6sR7CcuJ9sxWcqhXHBgE5r8kS3gXBJvaUWtpump` |
| Women in Finance | 32 other creator launches and reused socials | `95JVHQQhHAPTJDVjw37ViiEwehstLEeX61Gbf13Upump` |
| Higher | Graduated; 16-creator ring | `wV46Y351erjX7CiAyRRvzJgeWdtqpHXXBmv9LVzpump` |
| Agent Alley | Another launch in the 943-creator ring | `251ndGnv5tN45Fr4jpBtSeuvfyEZCN6Jk7K9u9pgpump` |
| Chill House Vrax | Graduated; hub-funded creator | `b1U8BazMzFbrCpD2rLmVTbiJSdHUh7mUWy3dn5Spump` |

The two additional examples came from these read-only graph queries:

```cypher
MATCH (c:Coin)<-[:CREATED]-(:Wallet)-[:IN_RING]->(r:Ring)
RETURN c.name AS name, c.symbol AS symbol, c.mint AS mint,
       r.creators AS creators, r.coins AS coins
ORDER BY r.creators DESC LIMIT 8
```

```cypher
MATCH (c:Coin) WHERE c.graduated = true
RETURN c.name AS name, c.symbol AS symbol, c.mint AS mint
ORDER BY c.created_at DESC LIMIT 6
```

## Validation

- **126 passed**, zero failures or skips in the full pytest suite, including
  real-FalkorDB tests. Regressions cover identity resolution, ticker collisions,
  long questions, absent mints, lookup errors/caps, fresh-session subject handling
  and retained follow-up behavior. [Output](inline-pytest-results.txt).
- **20 Playwright acceptance checks**, **16 accessibility scans**, zero page errors.
  All six chips run against the real local server at 1440 px; Subprime Cat, Women
  in Finance and Higher also run at 390 px. Checks cover citations, correct graph
  focus, full links, the same-session METHU → `/app?q=Subprime Cat` regression,
  absent coins without `/api/ask`, ticker/mint entry, ambiguity selection, retry
  after a simulated 429, rapid chip switching and reduced motion.
  [Script](qa-inline.mjs), [report](inline-browser-results.json),
  [log](inline-browser-log.txt).
- **Real SSE sequencing checked at both widths**: a loopback relay delays each
  unmodified `/api/ask` event by 300 ms; at least two steps are visible before
  the verdict, then the investigation completes. No event or graph data is mocked
  in this check. [Script](qa-inline-stream.mjs), [report](inline-stream-results.json).
- JavaScript syntax checks and `git diff --check` pass.

**AI validation limit:** the local preview has no configured owner key, so real
local investigations exercised the labeled graph-dossier fallback. The existing
shared-owner pytest tests use mocked Claude responses with real agent/tool and
citation processing, including hourly/daily caps. A separate browser check mocks
an agent-mode stream to verify the AI label, clickable citations and absence of
key prompts. No paid AI request was made; a live model-generated answer was not
verified in this run. Production continues to use its existing owner-key path.

Screenshots are in [shots-inline](shots-inline/), including:

- [Desktop inline dossier and graph](shots-inline/inline-subprime-cat-1440.png)
- [390 px inline dossier and graph](shots-inline/inline-subprime-cat-390.png)
- [Actual streaming steps at 390 px](shots-inline/inline-streaming-390.png)
- [Hub dead end](shots-inline/inline-chill-house-vrax-1440.png)
- [Fixed `/app?q=` at 390 px](shots-inline/app-q-subprime-390.png)
- [Unknown-coin state](shots-inline/inline-unknown-390.png)

## Reproduce locally

The local snapshot was already available on port 16379. Passwords, temporary env
files and browser packages remain outside the repository.

```bash
FALKORDB_PORT=16379 \
FALKORDB_PASSWORD_FILE=/tmp/sniff-qa/falkordb-local.pw \
SNIFF_ENV_FILE=/tmp/sniff-inline-tests.env \
  .venv/bin/python -m pytest tests -q
```

Start the local preview:

```bash
FALKORDB_PORT=16379 \
FALKORDB_PASSWORD_FILE=/tmp/sniff-qa/falkordb-local.pw \
SNIFF_ENV_FILE=/tmp/sniff-inline-preview.env \
  .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8080
```

Then run:

```bash
PLAYWRIGHT_MODULE=file:///tmp/sniff-qa/node_modules/playwright/index.mjs \
AXE_MODULE=file:///tmp/sniff-qa/node_modules/@axe-core/playwright/dist/index.mjs \
  node docs/final/qa-inline.mjs

PLAYWRIGHT_MODULE=file:///tmp/sniff-qa/node_modules/playwright/index.mjs \
  node docs/final/qa-inline-stream.mjs
```

Implementation commits:

- `82e9938` — Fix coin resolution and prevent stale session coin reuse.
- `c4b9b96` — Run graph investigations inline on the landing page; preserve
  explicit follow-ups, improve ambiguity handling and add further regressions.
