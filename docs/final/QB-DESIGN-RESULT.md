# Sniff now uses QuantBase’s Ember system

Completed locally on 18 October 2026, before the 23:15 IST hard stop.
No deployment or push. First working checkpoint: `e088b5b` at 22:01 IST.

## What changed

`app/static/quantbase.css` now owns the shared QuantBase tokens, local font
faces, controls and page treatments. It ports the source dashboard’s canvas,
cocoa glass, opaque reading surfaces, warm text, ember states, white actions,
spacing, radii, shadows and motion. Host Grotesk and Geist Mono are byte-identical
to `sniff-app-prod/public/fonts`; all three font families remain self-hosted with
OFL licenses. The QuantBase mark replaces the separate large Sniff wordmark.

`/app`, `/memory`, `/brain` and `/settings` use the dashboard frame, 80px icon
rail, `quantbase.live | Sniff` top bar, segmented graph-workspace pills and
labelled status. The desktop frame stays visible while its reading pane scrolls.
Phone navigation has five labelled destinations. The initial investigation
action clears that navigation at 390×844. Cytoscape’s text and meaningful
strokes now resolve the same CSS tokens as the rest of the interface.

`/` follows the submitted story: an unfamiliar coin, METHU’s funding trail,
72 creators and coins, the hub lesson, citations, agent memory, the company
brain, the honest research limitation, and three tracks in one product.
Generated local WebP illustrations include mobile crops and explicit dimensions;
lazy loading and gradient fallbacks preserve the layout. The hero traces
coin → creator → funder → ring, then stops at an exchange-like hub. It has
pause/resume and a complete static reduced-motion state. The demo opens in a
keyboard-accessible lightbox, stops on dismissal and restores focus. Without
JavaScript its ordinary YouTube link still works.

The hero badge and production section link QuantBase and its dashboard. The
copy explicitly says paper trading is live and live trading on a user’s own
wallet is opening soon. Existing snapshot metrics, evaluation caveats, MCP
command, three-track content and investigation links remain available.

`/blog` keeps its existing article and all eight local figures, now with the
website header, footer and reading scale. Website footers follow the source
brand/three-column/risk-note structure. The unconfigured `/waitlist` route
keeps its existing redirect to the redesigned home page.

## Shared Claude key

The existing server already selects its shared key for anonymous visitors,
while preserving visitor-key overrides and hourly/daily limits. No production
key, AI client selection or cap was changed.

A read-only request to the public production settings endpoint reported
`owner.active: true` and `claude-sonnet-5-5`. No key was retrieved or exposed.
The local end-to-end tests use a mock Claude client, the actual server’s key
selection, tool execution, citation validation and SSE route. The browser check
sends no visitor key, receives “Written by Claude from graph evidence”, selects
its `[E1]` citation and sees “Using Sniff’s shared key” in settings. It confirms
that the active-key path does not show “Add a Claude key”. No paid production
AI request was made for this verification.

## Validation

- **111 passed, no skips** against the local FalkorDB using
  `.venv/bin/python -m pytest -q`. This includes all original tests and three
  new shared-key checks: anonymous Claude/SSE/citations, hourly cap, daily cap.
  [Saved output](qb-pytest-results.txt).
- **Two completed browser passes:** 22 acceptance groups and 18 AA scans per
  pass, with zero browser errors and zero accessibility violations.
  [Pass 1](qb-browser-pass-1.json), [final pass 2](qb-browser-pass-2.json).
- **Every page at 1440 and 390**, including the waitlist fallback; empty and
  populated graph states, streaming, evidence selection, memory provenance,
  source citations, settings and mobile navigation are captured.
- **Responsive sweep:** 320, 375, 390, 414, 640, 768, 1024, 1280, 1440 and
  1920px checked without document-level horizontal scrolling. The mobile menu
  stays within the viewport; the main action clears bottom navigation.
- **Motion/fallback checks:** pause/resume, switching reduced motion while the
  page is open, failed-image fallback and no-JavaScript video links pass at both
  sizes. [Results](qb-motion-results.json).
- **Shared-key browser checks:** anonymous answer, no visitor-key header,
  interactive citation and active settings pass at both sizes.
  [Results](qb-shared-key-results.json).
- **Normal-motion graph checks:** all four coin/viewport combinations fit
  within the graph and retain the existing zoom cap and evidence transitions.
  [Results](qb-viewport-results.json).
- JavaScript syntax checks and `git diff --check` pass. No runtime dependency
  or external font CDN was introduced. Existing Python tests and snapshots
  were preserved; ordering-only artifacts from the graph test were restored.

## Visual comparisons

[Pass 1 side by side](shots-qb/comparison-pass-1.jpg) compared the dashboard and
landing against `sniff-app-prod/docs/astra/final/1440-chat.png` and a Playwright
capture of quantbase.live. The second pass keeps the frame on screen, aligns
the welcome/composer vertically, unifies canvas colours, fixes the phone menu,
and brings the primary phone action above navigation.

[Final side by side](shots-qb/comparison-pass-2.jpg),
[phone comparison](shots-qb/comparison-mobile.jpg),
[workspace contact sheet](shots-qb/workspace-contact-sheet.jpg).

| Page | 1440 | 390 |
| --- | --- | --- |
| Home | [Screenshot](shots-qb/pass-2/home-1440.png) | [Screenshot](shots-qb/pass-2/home-390.png) |
| Investigate, welcome | [Screenshot](shots-qb/pass-2/app-empty-1440.png) | [Screenshot](shots-qb/pass-2/app-empty-390.png) |
| Investigate, real graph | [Screenshot](shots-qb/pass-2/app-investigation-1440.png) | [Screenshot](shots-qb/pass-2/app-investigation-390.png) |
| Shared Claude key, mock client | [Screenshot](shots-qb/pass-2/app-shared-key-1440.png) | [Screenshot](shots-qb/pass-2/app-shared-key-390.png) |
| Memory | [Screenshot](shots-qb/pass-2/memory-1440.png) | [Screenshot](shots-qb/pass-2/memory-390.png) |
| Brain | [Screenshot](shots-qb/pass-2/brain-1440.png) | [Screenshot](shots-qb/pass-2/brain-390.png) |
| Blog | [Screenshot](shots-qb/pass-2/blog-1440.png) | [Screenshot](shots-qb/pass-2/blog-390.png) |
| Settings | [Screenshot](shots-qb/pass-2/settings-1440.png) | [Screenshot](shots-qb/pass-2/settings-390.png) |
| Waitlist fallback | [Screenshot](shots-qb/pass-2/waitlist-fallback-1440.png) | [Screenshot](shots-qb/pass-2/waitlist-fallback-390.png) |

## Reproduce

Use the existing local graph setup, with its password file kept outside the
repository. The standard local app runs on port 8080 with a fresh fixture env
file and no shared key. Browser packages are development-only tools under
`/tmp/sniff-qa`; they were not added to runtime requirements.

```sh
FALKORDB_PORT=16379 \
FALKORDB_PASSWORD_FILE=/tmp/sniff-qa/falkordb-local.pw \
SNIFF_ENV_FILE=/tmp/sniff-qa/app.env \
  .venv/bin/python -m pytest -q

QB_QA_PASS=pass-2 \
PLAYWRIGHT_MODULE=file:///tmp/sniff-qa/node_modules/playwright/index.mjs \
AXE_MODULE=file:///tmp/sniff-qa/node_modules/@axe-core/playwright/dist/index.mjs \
  node docs/final/qa-qb-design.mjs

PLAYWRIGHT_MODULE=file:///tmp/sniff-qa/node_modules/playwright/index.mjs \
  node docs/final/qa-qb-motion.mjs
```

For the browser shared-key fixture, start this separate loopback-only server,
which uses a deliberately fake Claude client and never calls Anthropic:

```sh
FALKORDB_PORT=16379 \
FALKORDB_PASSWORD_FILE=/tmp/sniff-qa/falkordb-local.pw \
SNIFF_ENV_FILE=/tmp/sniff-qa/app.env \
  .venv/bin/python docs/final/qa-qb-shared-key-server.py

PLAYWRIGHT_MODULE=file:///tmp/sniff-qa/node_modules/playwright/index.mjs \
  node docs/final/qa-qb-shared-key.mjs
```

The source brief’s concurrent user edits remain untouched and unstaged.
