# Review fixes · Sniff by QuantBase

Completed on **18 October 2026**, before the **21:30 IST** commit deadline, on
`final/review-fixes`. Commit author: **avasis-ai <abhay@avasis.ai>**.
No deployment, push, production database write, paid AI request, dev.to edit,
submission-form change or public agent note was made.

## Required fixes

| Brief item | Completed result |
| --- | --- |
| P1-1 · Brain provenance | `REPO_URL` points to published `main`. Preparation fetches the actual published repository text, rather than labelling working-tree drafts as published sources. Missing repository files fail preparation. The regenerated artifact has **12 documents, 93 sections, zero AI requests and zero extracted entity relationships**. All 12 source URLs, including all five repository files, returned anonymous HTTP 200. |
| P1-1 · Reload migration | The loader retires all old Doc/Section records, including changed URLs and removed documents, removes previous entity relationships, and activates the reviewed corpus. Both graph and full-text retrieval exclude inactive sections; status excludes retired documents. Reruns and old `final/tracks` records are covered by real-FalkorDB regressions. An incomplete artifact is refused before retirement or other writes. |
| P1-2 · Citation check | Uncited model sentences are dropped, including uncited openings, lowercase continuations, quoted sentences, paragraphs and list items. Every matched topic needs compatible evidence; funding cannot bypass the socials requirement. Only the server adds uncited context/refusal text, including its computed base rate. |
| P1-2 · Honest contract | README, `BLOG-FINAL.md`, generated `blog.html` and submission docs say: **every sentence must cite evidence of the matching kind; the server rejects answers that don't**. They explicitly explain that E checks validate citation IDs/tool compatibility, not subjects, numbers or claim truth. A regression records the actual limitation: “999 coins” still passes with a real compatible coin-dossier ID. B excerpts must also match their own source section. |
| P2-4 · `/app` brain mode | B citations open and focus the matching source, expand its original section, and highlight its graph evidence. Source URLs, headings and fetch dates are visible. The complete returned brain graph is rendered with source labels and typed edges. The answer says **Public source excerpts**; the Claude-key banner is restricted to dossier mode. |
| P2-5 · Loaded graph and privacy | README and blog distinguish the loaded source-only `MENTIONS`/`PART_OF` graph from the capped AI builder's optional `SUPPORTS`/`CONTRADICTS`/`DECIDED_ON` capability. Full-text runs alongside graph retrieval. A local/repository privacy match fails the build; a web match refuses that whole source, with required-source failures stopping preparation. |
| P2-6 · Submission state | README and submission docs record the verified live state dated **18 October 2026**, with setup under **Reproduce**. The publishing source is **`BLOG-FINAL.md`**. Completed live checks and local coordination checks are distinguished from unchecked leader actions. |

The final blog was regenerated with **`python -m build.blog`**. The new dependency-free
builder retains the existing page structure, site navigation, image dimensions and all ten images.
A second regeneration produced identical bytes.

## Nice-to-haves completed

- `/memory` has **See METHU**, which opens the real aggregate in one click, and a visible
  **Second-agent notes** section. Real returned notes display **agent note · not verified**,
  self-declared attribution, timestamp and evidence references. Empty views say no note is recorded.
- `/brain` displays clean excerpt text, without literal bold/list markup, and chooses complete
  paragraphs/list items without cutting their qualifications off. Original Markdown remains available
  in the expanded source section. Privacy questions prefer the relevant public policy summaries.
- Memory graphs fit their pane at **390 px**, with Fit and zoom controls and keyboard inspection.
- The agent prompt, README and final blog say **eight model/tool rounds**; a round can call several tools.

## Verified live state and leader handoff

The earlier [production review](ASTRA-REVIEW.md) demonstrated all three tracks, exactly 12 MCP tools,
real persistent session reuse and the three brain examples. This task's
[read-only production checks](fix-live-state.json) confirmed the home is HTTP 200, the site key is
Active, METHU has **four aggregate findings and zero public agent notes**, and the brain has
**12 source-only documents**. Production still had the old source URLs at verification time.
The fixes above are locally validated and require the leader's deployment and reload.

After deploying this branch's code and `build/public-brain.json`, run this exact command **on the box**:

```bash
cd /opt/lineage/app/src
export FALKORDB_PASSWORD_FILE=/opt/lineage/env/falkordb.env
/opt/lineage/app/.venv/bin/python -m build.brain --load build/public-brain.json
```

Expected result: `{"loaded": {"documents": 12, "sections": 93}}`.
`--load` makes no network or AI calls. It replaces only the active brain corpus; existing memory remains.
Retired records remain inactive for history, and the retired URLs disappear from retrieval and status.
The artifact's repository sections are the published `main` text fetched during preparation.

Afterward, verify `/api/brain` and all three `/brain` examples, including anonymous access to each
returned source URL. The leader should also post one real second-agent observation through MCP,
update the existing dev.to URL from `BLOG-FINAL.md`, and confirm all three tracks in the submitted form.
Those production/publication actions remain unchecked in [SUBMISSION.md](../SUBMISSION.md).

## Validation and reproduction

- **108 passed, zero skipped** across the full Python suite, including the local lineage snapshot,
  independent DuckDB query checks, agent/MCP/privacy tests and isolated real-FalkorDB migration tests.
  [Test output](fix-pytest-results.txt).
- **22 broader browser checks** passed, including lineage examples, streaming, settings, navigation,
  images and a **320–1920 px** responsive sweep. No browser errors; 18 accessibility scans had no violations.
  [Broad browser report](fix-broad-browser-results.json).
- **9 targeted checks** passed at **1440×1000 and 390×844**, with normal motion: full brain graph in
  `/app`, clickable B sources, mode changes, local second-agent MCP note, one-click METHU, graph fitting,
  all brain examples and corrected blog content. No console errors; 12 accessibility scans had no violations.
  The QA note was written only to the loopback database. [Script](qa-fixes.mjs), [report](fix-browser-results.json).
- **12/12 source URLs** returned anonymous HTTP 200. [URL evidence](fix-source-urls.json).
- Blog regeneration is deterministic; JavaScript syntax checks and `git diff --check` pass.

The local lineage database was already running on port 16379. Credentials and browser packages remain
outside the repository. Reproduce the Python run with:

```bash
FALKORDB_PORT=16379 \
FALKORDB_PASSWORD_FILE=/tmp/sniff-qa/falkordb-local.pw \
SNIFF_ENV_FILE=/tmp/sniff-fix-preview.env \
  .venv/bin/python -m pytest tests -q
```

With the local app on port 8080 and the regenerated corpus loaded:

```bash
PLAYWRIGHT_MODULE=file:///tmp/sniff-qa/node_modules/playwright/index.mjs \
AXE_MODULE=file:///tmp/sniff-qa/node_modules/@axe-core/playwright/dist/index.mjs \
  node docs/final/qa-fixes.mjs
```

Screenshots: [/app brain · desktop](shots-fixes/app-brain-1440.png),
[/app brain · phone](shots-fixes/app-brain-390.png),
[memory · phone](shots-fixes/memory-390.png), [brain · phone](shots-fixes/brain-390.png).
