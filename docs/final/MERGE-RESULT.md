# Final merge result · Sniff by QuantBase

Completed on **18 October 2026, before the 21:15 IST hard deadline**, on
`final/merged`. Commit author: **avasis-ai <abhay@avasis.ai>**.
No deployment, push, production database change or paid AI call was performed.

## Integrated result

Merged `final/tracks` at **955bb82** into the premium UI lineage headed by
**097c25b**. The two conflicts were in `README.md` and `docs/SUBMISSION.md`;
both retain the three-track descriptions and the QuantBase attribution.
The Ember design system from **b4f544d** remains the shared source of truth.

| Track | Integrated behavior |
| --- | --- |
| 01 · Agents acting on connected data | `/app` investigates the lineage graph, streams steps, displays the dossier and highlights cited evidence. The nine lineage tools remain available. |
| 02 · Agent memory and coordination | `/memory` recalls public coin/wallet findings or an anonymous session graph. Original tool provenance, observation times, session replay, privacy checks and attributed agent notes are preserved. MCP exposes `memory_recall` and `memory_note`. |
| 03 · Company brain | `/brain` retrieves public source sections through graph neighbourhoods and full-text search, with checked `[B#]` citations and inspectable source nodes. MCP exposes `brain_ask`. |

All **12 MCP tools**, the public corpus, builders, privacy gate, integration
tests, final blog draft and ten blog images are included in the merge.
The corpus remains explicitly **source-only**: 12 reviewed public documents,
92 sections, and no claim that AI extraction ran during this merge.

## UI and integration fixes

- Memory and Brain now use the shared Ember tokens, self-hosted Host Grotesk
  and Geist Mono, white action pills, warm panels, focus treatment and responsive
  workbench layout. Their forms, graph selection, provenance and citations work.
- Blog uses the same branding and navigation, a split introduction and a narrow
  reading column. `/blog` now has an explicit route; `/blog-assets` serves only
  the committed image directory. All ten images load locally. The complete
  story and `docs/BLOG-FINAL.md` are preserved.
- Memory, Brain and Blog appear in the navigation and footer throughout the
  site. A native mobile menu keeps every destination reachable at narrow widths.
- The home page has **“Three tracks, one product”**, with a plain sentence and
  working link for each track, plus the memory/brain MCP names. The project line
  and footers identify all three tracks; developer copy describes 12 tools.
- The connection map is capped at **1.2×**, fits again after layout using final
  label bounds, and leaves padding around the whole graph. METHU opens at
  **120% desktop / 83% phone**; the larger shared-social example fits at about
  **79% / 40%**. Fit, zoom, evidence selection and keyboard controls still work.
- A real browser check found the research example returning no Brain sources:
  the full-text fallback used literal `OR`. It now uses the RediSearch union
  operator `|`, with a real-FalkorDB regression covering unmatched question
  words and a match found only through full-text search. The syntax is documented
  in the [Redis query syntax reference](https://redis.io/docs/latest/develop/interact/search-and-query/advanced-concepts/query_syntax/).
- New track results reset the inspector and scroll position; unrelated edge
  labels stay quiet until selection. Closing search suggestions now cancels
  pending searches so they cannot reopen over example buttons after submission.
- The team is **QuantBase** in the README, LICENSE, submission, blog drafts,
  pages and historical brief text. Exact old-name search returns no matches.
  GitHub repository names and URLs are preserved.

## Verification

| Check | Result |
| --- | --- |
| Full Python suite | **86 passed, 0 skipped**, 35.65 seconds |
| Browser acceptance | **22 groups passed** |
| WCAG A/AA checks | **18 Axe scans, 0 violations** |
| Browser JavaScript / unexpected console errors | **0** |
| Responsive sweep | All six pages at 320, 375, 390, 414, 640, 768, 1024, 1280, 1440 and 1920px; no document overflow |
| Normal-motion map regression | Four real graph/viewport combinations; final bounds fit with padding and evidence zoom stays at or below 1.2× |
| Screenshots | **32 fresh captures**, including every page at 1440 and 390px; visually reviewed |
| Python compilation, JavaScript syntax, deployment-script syntax | Passed |
| Git whitespace and merge-conflict checks | Passed |
| Gitleaks on staged changes, with redacted output | No leaks found |

Tests used the existing isolated local lineage snapshot at port 16379 and
separate embedded FalkorDB graphs for memory/brain integration tests. The
committed public corpus was loaded into the local preview database. Real
lineage investigations supplied the memory screenshots; no coin evidence was
invented. The local API used a temporary env file without a Claude key.
Settings and delayed/error stream cases use explicitly labelled browser
fixtures. Expected HTTP 400/429 responses are listed separately from errors.

Evidence: [Python results](pytest-results-merged.txt),
[browser results](browser-results-merged.json),
[normal-motion viewport measurements](viewport-results-merged.json).

## Screenshots

| Page / state | 1440px | 390px |
| --- | --- | --- |
| Home, including all three tracks | [Desktop](shots-merged/home-1440.png) | [Phone](shots-merged/home-390.png) |
| Investigation workspace | [Desktop](shots-merged/app-investigation-1440.png) | [Phone](shots-merged/app-investigation-390.png) |
| Evidence selected | [Desktop](shots-merged/app-evidence-1440.png) | [Phone](shots-merged/app-evidence-390.png) |
| Memory · public findings | [Desktop](shots-merged/memory-1440.png) | [Phone](shots-merged/memory-390.png) |
| Memory · session graph | [Desktop](shots-merged/memory-session-1440.png) | [Phone](shots-merged/memory-session-390.png) |
| Company brain · cited answer | [Desktop](shots-merged/brain-1440.png) | [Phone](shots-merged/brain-390.png) |
| Blog · all images loaded | [Desktop](shots-merged/blog-1440.png) | [Phone](shots-merged/blog-390.png) |
| Settings | [Desktop](shots-merged/settings-1440.png) | [Phone](shots-merged/settings-390.png) |
| Existing waitlist fallback | [Desktop](shots-merged/waitlist-fallback-1440.png) | [Phone](shots-merged/waitlist-fallback-390.png) |

The directory also contains empty workspace/memory/brain states, streaming
states, desktop ring/social/graduated examples, hero crops and the mobile menu.
The waitlist captures show its existing unconfigured local redirect to home.

## Reproduce locally

With the local lineage database running and the public brain corpus loaded:

```sh
FALKORDB_PORT=16379 \
FALKORDB_PASSWORD_FILE=/tmp/sniff-qa/falkordb-local.pw \
SNIFF_ENV_FILE=/tmp/sniff-merge-qa/app.env \
  .venv/bin/pytest tests -q

PLAYWRIGHT_MODULE=file:///tmp/sniff-qa/node_modules/playwright/index.mjs \
AXE_MODULE=file:///tmp/sniff-qa/node_modules/@axe-core/playwright/dist/index.mjs \
  node docs/final/qa-merged.mjs

PLAYWRIGHT_MODULE=file:///tmp/sniff-qa/node_modules/playwright/index.mjs \
  node docs/final/qa-viewport.mjs
```

Both browser scripts target loopback only; `SNIFF_QA_URL` can select another
local port. The primary browser script supports `CHROMIUM_PATH` and waits for
fonts and images before captures. Tooling and local credentials remain outside
the repository. Follow [GRAPH.md](../GRAPH.md) for a different database setup.

Deployment and loading the new graphs on the live site remain a separate leader
operation, as required by the merge brief. This result is committed locally.
