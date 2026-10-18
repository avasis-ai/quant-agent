# Final result

Completed on **18 October 2026, before the 21:45 IST deadline**, on branch
`final/premium-ui`. Author: **avasis-ai <abhay@avasis.ai>**. No deployment performed.

Sniff now has a complete QuantBase Ember landing page, a dedicated investigation
workspace and matching settings. The landing explains funding trails, hub dead
ends, WCC rings and shortest paths; includes the full recorded eval table and
its limitations; documents the FalkorDB features and MCP endpoint; and plainly
connects Sniff’s graph intelligence to the QuantBase dashboard. Both QuantBase
destinations, GitHub, the existing video and the published blog are linked.

The workspace puts the dossier above a wide graph and a right-hand findings
panel. Claims retain clickable `[E]` tags. Evidence highlights the relevant
path, with distinct node shapes, ember halos, typed labels, a legend, zoom,
fit, drag/touch pan and keyboard pan controls. Its deterministic layout follows
the funding direction on desktop and uses vertical ranks on phones. A text node
list provides keyboard access to the graph. Streaming steps remain visible
while running and can be expanded after completion.

All three pages share self-hosted Host Grotesk, Geist Mono and Instrument Serif,
warm reading surfaces, frosted frames and white action pills. Layouts stack on
phones. Reduced motion stops automatic traversal and spatial animation; reduced
transparency uses opaque panels. The four landing metrics have one source:
[`app/static/snapshot.json`](../../app/static/snapshot.json). The design system
and asset provenance are in [DESIGN.md](../../DESIGN.md) and [ASSETS.md](ASSETS.md).

The team name is **QuantBase** throughout the finished UI, README, submission
and local blog drafts. The README also discloses Codex’s work on this final UI.

## Routes and contracts

| Route | Final behavior |
| --- | --- |
| `/` | Full landing page |
| `/app` | Investigation workspace, including `?mint=` and `?q=` handoffs |
| `/?mint=…`, `/?q=…` | Preserves the query and redirects into `/app` |
| `/settings` | Visitor key and owner controls; existing API and tab-session storage |
| `/mcp` | Existing nine-tool streamable HTTP MCP service |
| `/api/*` | Existing request, response, header and SSE contracts retained |
| `/waitlist` | Existing configured page handoff; existing home redirect when no page is configured |

The application does not claim `/admin` or `/api/waitlist`. New local assets are
served by a FastAPI `/static` mount; the existing `/media` behavior is preserved.

## Verification

| Check | Result |
| --- | --- |
| `pytest tests -q` | **48 passed, 0 skipped**, 12.68 seconds |
| Browser acceptance | **16 groups passed** |
| Axe WCAG A/AA scans | **11 scans, 0 violations** |
| Browser JS errors / warnings | **0 unexpected errors or warnings** |
| Responsive sweep | 320, 375, 390, 414, 640, 768, 1024, 1280, 1440 and 1920px; no document overflow |
| Laptop hero | Primary action fits at 1280 × 800 |
| JavaScript syntax / Git whitespace | Passed |
| Gitleaks on assets and staged changes | No leaks found |
| Cytoscape bundle integrity | SHA-512 matches the previous UI’s pinned 3.33.1 SRI |

The full repository CSV snapshot was imported into an isolated local
**FalkorDBLite 0.10.0** database (reported graph module version `41803`), with
indexes and WCC rings rebuilt. All graph tests ran, including the independent
DuckDB comparisons, live-graph mock eval and MCP graph call. The API server used
an isolated temporary env file with no Claude key. No production database or
site configuration was changed.

Browser checks cover real searches, shared tickers, mint handoff, all four
examples, hub dead ends, citations, dossier evidence, graph navigation, sharing,
unknown coins and empty results. Negative lookups no longer draw their evidence
anchor as a recorded coin. Delayed, split SSE fixtures verify streaming and CRLF
boundaries. Browser fixtures verify rate-limit recovery and visitor/owner key
lifecycles without real AI calls. Expected fixture HTTP 400 and 429 responses
are recorded separately from browser errors.

Machine-readable evidence: [browser-results.json](browser-results.json) and
[pytest-results.txt](pytest-results.txt). The checks are reproducible with
[qa.mjs](qa.mjs).

## Screenshots

All page captures use Playwright at exactly **1440px and 390px**. The source
images were visually reviewed, including the dense social graph and phone
controls. The waitlist captures show its existing unconfigured local fallback.

| Page / state | Desktop | Phone |
| --- | --- | --- |
| Landing | [1440](shots/home-1440.png) | [390](shots/home-390.png) |
| Empty workspace | [1440](shots/app-empty-1440.png) | [390](shots/app-empty-390.png) |
| METHU investigation | [1440](shots/app-investigation-1440.png) | [390](shots/app-investigation-390.png) |
| Evidence highlight | [1440](shots/app-evidence-1440.png) | [390](shots/app-evidence-390.png) |
| Streaming steps | [1440](shots/app-streaming-1440.png) | [390](shots/app-streaming-390.png) |
| Settings | [1440](shots/settings-1440.png) | [390](shots/settings-390.png) |
| Waitlist fallback | [1440](shots/waitlist-fallback-1440.png) | [390](shots/waitlist-fallback-390.png) |

Additional desktop captures: [hero](shots/home-hero-1440.png),
[large ring](shots/app-ring-1440.png), [shared socials](shots/app-socials-1440.png),
[graduated coin](shots/app-graduated-1440.png).

## Run the checks

The local preview is at **http://127.0.0.1:8080**. With its local verification
database still running, the exact pytest target is:

```sh
FALKORDB_PORT=16379 FALKORDB_PASSWORD_FILE=/tmp/sniff-qa/falkordb-local.pw \
  .venv/bin/pytest tests -q
```

For another environment, load the graph as documented in the README and set the
matching `FALKORDB_PORT` and credentials. The temporary local password file is
outside the repository and has mode 600.

Browser tooling is kept outside the application:

```sh
npm install --prefix /tmp/sniff-ui-qa playwright@1.64.1 @axe-core/playwright@4.14.0
/tmp/sniff-ui-qa/node_modules/.bin/playwright install chromium
PLAYWRIGHT_MODULE=file:///tmp/sniff-ui-qa/node_modules/playwright/index.mjs \
AXE_MODULE=file:///tmp/sniff-ui-qa/node_modules/@axe-core/playwright/dist/index.mjs \
  node docs/final/qa.mjs
```

`CHROMIUM_PATH` optionally selects an existing Chromium executable.
`SNIFF_QA_URL` optionally selects another loopback port. The script refuses a
non-local target because it exercises settings with local browser fixtures.

## Commits

- `b4f544d` · Shared QuantBase Ember design system, local assets and licenses.
- `9e4cf4c` · Landing, evidence workspace, settings, route compatibility and tests.
- The final documentation commit contains this report, screenshots, browser
  checks, updated team attribution and the brief’s naming update.

The recorded snapshot and coverage limitations remain visible in the product.
The QuantBase integration is presented as becoming a core feature, with its
development status explicit. Deployment is left to the leader as requested.
