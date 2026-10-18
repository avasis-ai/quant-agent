# Tracks result: Sniff, team QuantBase

Branch: `final/tracks`. Deadline: 18 October 2026, 22:00 IST. No deployment, remote graph mutation,
form submission or paid AI call was performed. The leader owns integration and deployment.

## Implemented

| Track | Result |
|---|---|
| 01: Agents That Act on Connected Data | The nine existing lineage tools and E citation checks remain working. Their results now feed investigation memory. |
| 02: Agent Memory and Coordination | Separate indexed `memory` graph; timestamped Session → Question → Evidence → Coin/Wallet paths; exact same-session tool replay; original tool provenance and observation times; mint-free follow-ups; anonymous cross-session aggregates; attributed agent notes with evidence links; `/memory` graph viewer. |
| 03: Company Brain | Separate indexed `brain` graph; allowlisted public-source ingestion; typed products, features, policies, decisions, findings and metrics; capped AI extraction through the existing client; entity neighbourhood paths plus full-text retrieval; exact source sections and checked B citations; `/brain` question and graph viewer. |

MCP now exposes 12 tools: the nine lineage tools, `memory_recall`, `memory_note`, and `brain_ask`.
MCP lineage calls return a random `session_id` for follow-ups. Recalled findings hydrate their original
nodes, edges and source tool into local E evidence; agent notes remain unverified and cannot become
lineage evidence. Note provenance is a self-declared agent label, not an authenticated identity.

The API/browser uses a random HttpOnly session cookie. Visitor question text, keys, headers and network
addresses are never saved to the memory graph. Question nodes contain public tool intent instead.
Reusing a record does not reset its original observation time or extend the one-hour freshness window.
Memory outages and privacy refusals are reported rather than silently claimed as successful writes.

The public brain builder is rerunnable and refuses non-allowlisted sources, symlinks, secret/PII
matches, ungrounded extraction output and invalid citation attribution. Changed source sections are
deactivated and stale semantic relationships removed. Every model-extracted name and quote must occur
in the original section; relationship quotes must include both endpoints. The model never writes Cypher.

## Data and extraction honesty

- `build/public-brain.json` contains **12 accepted public documents and 92 sections**, fetched and
  scanned during this task. It includes the allowlisted README/GRAPH/EVAL/BLOG, public policy summaries,
  and the public site's paper/live, safety, pricing, FAQ and selected docs.
- The full plans, privacy and terms articles were **refused** because they contain email addresses.
  The public policy summaries cite the originals without copying contact details. No contact values
  appear in the saved audit. No internal handover, infrastructure notes or authenticated data were read.
- The committed fallback corpus is explicitly **source-only**: literal, grounded anchors, with no claim
  that live AI extraction happened. All six requested entity types are present alongside Doc and Section.
- Default AI extraction uses `ai.client_for` and the cheap Haiku entry in `ai.CHEAP`, with no expensive
  fallback or retry. Defaults cap 12 requests, 60,000 reserved input tokens, 12,000 output tokens and a
  $0.60 reservation ceiling at conservative $5/$25 per-million rates. The configured owner key was
  unavailable locally, so this path was tested with a fake client and grounded-output/budget tests.
- Runtime brain answers are source excerpts and need no AI key. Semantic relationships are extracted
  by the capped AI build; source-only builds still provide meaningful entity/section/document paths.
- Local memory and browser QA used explicitly synthetic test fixtures, not claims of live coin findings.
  The leader's optional METHU seed command reads the real demo `lineage` graph and invents no evidence.

## Verification

`uv pip install --python .venv/bin/python -r requirements-dev.txt falkordblite==0.10.0`

`.venv/bin/python -m pytest tests` → **73 passed, 10 skipped**.

The real Cypher integration tests used FalkorDBLite's embedded **FalkorDB 4.18.3** on this Mac. They cover
writes, indexed reads and graph paths, exact replay, E id remapping, unchanged freshness timestamps,
same-second follow-up ordering, session isolation, anonymous aggregates, privacy refusal before writes,
visitor-question removal from search evidence, two-agent MCP coordination, source-only and AI build
modes, source updates, and E/B citation contracts.
The production 6.0.2 instance was not contacted. The ten skipped pre-existing tests need the original
large lineage snapshot/CSV build or a reachable lineage graph.

Playwright checked both pages at desktop (1440), tablet (768) and mobile (390) widths against the real
embedded brain and memory graphs. Forms, source links, graph-node mouse/keyboard selection, validation,
agent-note display and overflow checks passed, with no JavaScript errors. JavaScript syntax, Python
compilation, shell syntax, complete-corpus privacy validation and `git diff --check` passed.

The staged change was scanned with Gitleaks using redacted output; no secrets were found.

## Leader handoff

Exact deploy, capped extraction, fallback load, real METHU seed, tunnel and verification commands are in
[GRAPH.md](../GRAPH.md#leader-only-demo-box-commands-not-run-by-this-task). `deploy/deploy.sh` now ships
the public docs and fallback corpus needed by the builder. Do not infer that the live site already has
these graphs: the leader must deploy and load them, then check `/api/brain`, `/memory`, `/brain` and MCP.

README and submission notes now describe all three tracks and use the QuantBase team name. Existing
app/settings UI files were not edited; the new pages, styles, scripts and API router are isolated to
limit integration conflicts with `final/premium-ui`. Parallel blog commits already present in the
worktree were preserved.
