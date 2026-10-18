# Submission checklist (for Abhay)

Submission deadline: **18 October 2026, 23:59 IST**. Review-fix commit deadline: **21:30 IST**.

## Pre-filled form fields

| Field | Value |
|---|---|
| Project name | Sniff |
| Team | QuantBase (code F92P7R) |
| Tracks | 01: Agents That Act on Connected Data; 02: Agent Memory and Coordination; 03: Company Brain |
| Repository | https://github.com/avasis-ai/quant-agent |
| Live demo | https://sniff.quantbase.live |
| MCP endpoint | https://sniff.quantbase.live/mcp |
| Video | https://youtu.be/fz89p-YZS6o |
| Blog post | https://dev.to/quantbase/sniff-four-days-one-graph-and-an-honest-answer-about-meme-coins-47af |

**Updated short description (≤ 300 characters):**

> Sniff investigates meme-coin operators through FalkorDB lineage, remembers findings across agent sessions,
> and answers QuantBase product and policy questions from a public company graph. Every answer links to its
> graph evidence or source section. History, not a prediction.

**Verified live state — 18 October 2026.** All three tracks are deployed. The final production review
verified METHU, persistent session replay (`recalled: true`), 12 MCP tools and the three brain examples.
Read-only checks on 18 October confirmed the site key is Active, four aggregate METHU findings,
no public METHU agent notes, and a 12-document source-only brain. The loaded brain uses `MENTIONS` and
`PART_OF`, with zero AI requests and no extracted entity-to-entity relationships. The capped AI builder
supports richer `SUPPORTS`/`CONTRADICTS`/`DECIDED_ON` relationships as an optional capability.
Graph retrieval and full-text retrieval run alongside each other.

Citation contract for factual answer text: **every sentence must cite evidence of the matching kind;
the server rejects answers that don't**. Unknown IDs, uncited sentences and missing topic coverage are
rejected. This checks citation-ID/tool compatibility, not whether every claim is true or whether a
number matches its evidence. B citations additionally bind literal excerpts to their own source.
Only explicit server-owned context/refusal text is allowed without citations.

The production source links still use the old branch until the leader deploys these fixes and reloads
the regenerated corpus. The fixes are on `final/review-fixes`; exact handoff and validation are in
[FIX-RESULT.md](final/FIX-RESULT.md). The earlier production evidence is in
[ASTRA-REVIEW.md](final/ASTRA-REVIEW.md). This task does not deploy, push, update dev.to, change the
submission form, or post a public agent note.

**Tech used:** FalkorDB 6.0.2 (bulk loader, range and full-text indexes, `algo.WCC`, `algo.SPpaths`,
read-only queries with timeouts), Claude Sonnet 5.5 with tool use, MCP (streamable HTTP), Python, FastAPI,
Cytoscape.js, DuckDB (data prep and test ground truth), AWS EC2 and Caddy.

## Leader actions

1. Deploy the reviewed fixes, then run the source-only reload under **Reproduce** below. Verify the
   returned source URLs anonymously and confirm no retired branch URLs remain in `/api/brain` or answers.
2. From a second agent, recall the real METHU findings over MCP and post one real attributed observation.
   The memory UI labels notes **agent note · not verified**. No synthetic note is preloaded.
3. Update the **existing** [submitted dev.to article](https://dev.to/quantbase/sniff-four-days-one-graph-and-an-honest-answer-about-meme-coins-47af)
   from **[BLOG-FINAL.md](BLOG-FINAL.md)**, retaining its URL. Verify QuantBase attribution and all ten images.
   `docs/BLOG.md` is the older article and is not the publishing source.
4. Confirm the submitted form selects **all three tracks** and keeps the intended video and blog URLs.
   This task has not inspected the form.
5. After judging, follow the existing infrastructure teardown notes.

## Reproduce

Local setup, corpus preparation, tests and app commands are in [README.md](../README.md#reproduce).
The regenerated artifact uses published `main` repository content, not working-tree drafts.
A local/repository privacy match fails the build; a web-source privacy match refuses that whole source.
A missing/refused required web source fails the build.

After deploying the reviewed code and `build/public-brain.json`, run **on the box**:

```bash
cd /opt/lineage/app/src
export FALKORDB_PASSWORD_FILE=/opt/lineage/env/falkordb.env
/opt/lineage/app/.venv/bin/python -m build.brain --load build/public-brain.json
```

The loader retires old Doc/Section records, including changed URLs and removed documents, before
activating the new corpus. No AI call or fresh network fetch is made by `--load`. Memory is already live;
this reload does not change the memory graph.

## Check before submitting

- [x] Production home and METHU investigation work (18 October live review).
- [x] `/settings` reports an Active site key (18 October read-only check).
- [x] MCP initialization and `tools/list` return exactly 12 tools (18 October live review).
- [x] `/memory` recalls real METHU findings and repeated MCP calls reuse persistent evidence.
- [x] Two-agent MCP note coordination passes the isolated real-FalkorDB integration test.
- [x] `/brain` returns paper/live, research and privacy source sections and graph results (18 October live review).
- [x] README screenshot URLs and all ten final blog image URLs return 200 (18 October live review).
- [ ] Leader deploys these fixes and reloads the regenerated corpus; production source URLs are verified afterward.
- [ ] A second agent posts a real METHU note over MCP; the production page shows its attribution and unverified label.
- [ ] Existing dev.to article is updated from `BLOG-FINAL.md`, with QuantBase attribution and all ten images.
- [ ] Submitted form is checked for all three tracks and the intended blog URL.
- [ ] README diagrams are visually checked on GitHub after publishing these fixes.
- [x] Video link worked logged out at the earlier submission check.

**Submitted 17 October 2026, 13:48 IST; video link updated 13:57 IST.**
