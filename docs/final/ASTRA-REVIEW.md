# Sniff / QuantBase — final judge review

Reviewed 18 October 2026, 19:53–20:00 IST; checkout `8279298`. Live production, not local screenshots.
Report only. No application changes, deployment, submission edits or public agent notes were made.

**Verdict:** A polished, working Track 01 entry with real persistent memory. Track 03 retrieves useful
public sources, but its broken provenance links and overstated semantic graph story weaken the case.
The submitted blog is an older, incorrectly branded article. Fix the three P1 findings before judging.

**Live coverage and the two-minute test**

Playwright/Chrome at **1440×1000 and 390×844**, normal motion: `/`, `/app`, `/memory`, the supplied session,
`/brain` (all three example questions), `/blog`, `/settings`, `/mcp`, METHU and citation interactions.

| Track | What I demonstrated | Judge assessment |
|---|---|---|
| 01 | `/app` → METHU → E citation: **7.49 s desktop / 7.33 s mobile** after clicking. Creator, 0.0091 SOL funder, 71 other creators, 72-coin ring, zero graduations; graph highlighting works. | Strong; easily under two minutes. Citation guarantees need correction. |
| 02 | [Supplied session](https://sniff.quantbase.live/memory?session=d47f8f2375a248f9a224ae33809521eb) returns six findings; new browser investigations appear in their own sessions. Repeating MCP `coin_dossier` with its returned session gives `recalled: true` and original evidence provenance in **0.32 s**. | Persistence and reuse are real. Coordination writes pass the embedded integration test, but the public METHU aggregate had **no agent notes**; the second-agent story is not demonstrated by the default page. |
| 03 | `/brain` → paper/live, research, privacy: five source sections per question; B anchors, expanded source text and keyboard node inspection work. Paper/live took **0.56 s** desktop including capture. | Retrieval is real and fast; full credit is undermined by source 404s and source-only extraction. |

MCP initialization and `tools/list` succeeded: exactly **12 tools**, comprising the nine lineage tools plus
`memory_recall`, `memory_note`, `brain_ask`. Real MCP lineage, recall and brain calls succeeded.
An ordinary browser GET `/mcp` returns **406**, as expected without the MCP Accept header; this is not a
broken protocol endpoint. Its browser visit also produced one incidental favicon 404.

**Must fix, ranked**

1. **P1 — The brain's primary proof links are dead.** `build/brain.py:41`; [example failing source](https://github.com/avasis-ai/quant-agent/blob/final/tracks/docs/PUBLIC-POLICIES.md).
   All five repository source URLs exposed by `/api/brain` use unpublished `blob/final/tracks/` and return
   **404**, including paper/live's B1. Fix `REPO_URL` to a published, preferably immutable commit; regenerate
   the corpus and reload it, retiring the old branch-based Doc/Section records so retrieval cannot retain
   stale URLs. Verify every returned source URL anonymously. Changing the Python constant alone is insufficient.

2. **P1 — “Every sentence proves itself” exceeds the citation check.** `app/agent.py:109`, `app/agent.py:92`,
   `README.md:5`, `README.md:86`, `docs/BLOG-FINAL.md:66` and `/blog`.
   An isolated probe accepts `The creator launched 999 coins.` with **no evidence**, and accepts that false
   number with a valid E1 describing one launch. Mixed funding/social wording also bypasses the intended
   topic restriction because allowed tool sets are unioned. The desktop live answer had an uncited opening sentence.
   Fix: reject uncited factual sentences, permit only explicit server-owned context/refusal text without
   citations, require support for every matched topic, and add regressions for those cases. For factual
   guarantees, use validated subject/value fields or trusted templates; otherwise describe the check honestly
   as citation-ID/tool compatibility, not verification that every claim is true. Update both blog copies.

3. **P1 — The submitted blog has the wrong team and omits two tracks.** [Submitted dev.to article](https://dev.to/quantbase/who-is-behind-this-meme-coin-building-sniff-on-a-graph-4nnc);
   `docs/SUBMISSION.md:16`, `docs/SUBMISSION.md:46`.
   Its public API reports publication on 17 October, no edit, and the byline **“By team Quant Agent”**.
   It lacks memory, company brain and the final illustrated story. Update that existing article from the
   corrected `docs/BLOG-FINAL.md`, retaining its submitted URL; verify all ten images and QuantBase attribution.
   Point the publishing checklist at `BLOG-FINAL.md`, not the older `BLOG.md`.

4. **P2 — Company questions lose their proof in the investigation workspace.** `app/static/investigate.js:149`,
   `app/static/investigate.js:151`, `app/static/investigate.js:201`.
   Open `/app?q=How%20does%20QuantBase%20handle%20paper%20vs%20live%3F`: both widths show plain, unclickable
   `[B1]`–`[B3]`, “Fixed dossier” and “Add a Claude key”, despite successful brain retrieval and an active site key.
   Handle `mode === 'brain'` explicitly: render B citations with their source sections and source links,
   use the returned brain graph, label the result “Public source excerpts”, and restrict the key banner to
   actual dossier mode. Reuse the working `/brain` presentation where practical.

5. **P2 — The blog describes semantic relationships absent from the shipped corpus.** `docs/BLOG-FINAL.md:112`,
   `app/static/blog.html:72`, `build/brain.py:274`, `build/public-brain.json`.
   `/api/brain` reports **12 source-only documents**; the bundled artifact records **zero AI requests and zero
   extracted entity relationships**. Tested live graphs contain `MENTIONS`/`PART_OF`, not the advertised
   `SUPPORTS`/`CONTRADICTS`/`DECIDED_ON` story. The capped AI builder exists, but capability is not a deployed demo.
   Fix the prose to state exactly what is loaded and which richer edges are supported capabilities. If claiming
   semantic traversal as demonstrated, load a capped, quote-validated extraction and show an actual supported path.
   Also change “falls back” at `docs/BLOG-FINAL.md:118`: `app/brain.py:39` runs full-text retrieval alongside graph retrieval.

6. **P2 — Submission docs still describe an undeployed merge.** `README.md:38`, `docs/SUBMISSION.md:24`,
   `docs/SUBMISSION.md:55`. They tell judges the graphs need loading and retain unchecked live-feature checks.
   Replace this with a dated statement of the verified live state; move setup commands under reproduction.
   Mark only completed checks. Separately confirm the actual submission form selects all three tracks and
   the intended blog URL; this review did not access that form and cannot verify its current selections.

**Nice to have**

- Give `/memory` a one-click METHU demo and a visible, explicitly unverified second-agent note. Currently a new
  visitor gets an empty page and must supply an address/session. Surface “reused from memory” in follow-ups.
- Clean `/brain` excerpts: the research answer shows literal `**`, list hyphens and cut-off paragraphs; privacy
  leads with ingestion internals. Prefer short, relevant policy paragraphs and safely format source Markdown
  while preserving exact source text in the expandable section (`app/brain.py:70`, `app/static/tracks/tracks.js:60`).
- At 390px, the memory graph is **660px wide in a 314px pane**: evidence is initially offscreen. Add Fit/zoom
  controls and reduce the tall introductory blocks; no document-level overflow was observed.
- Cold desktop load events were **9.6 s home, 8.0 s app, 10.9 s blog**; warm navigation was much faster.
  These are single-run load timings, not LCP benchmarks. Profile the waterfall; add versioned asset caching
  and responsive blog images. Gzip is already enabled; do not “fix” this by enabling it again.
- Tighten remaining claims: “eight tool calls” is eight model/tool rounds (`app/agent.py:263`, `README.md:72`);
  a web-source privacy match refuses that source, not necessarily the entire build (`build/brain.py:179`,
  `docs/BLOG-FINAL.md:122`). Make these corrections before republishing.

**The three changes most likely to raise the score**

1. Make the evidence promise credible: repair source URLs, close the citation bypasses and make B citations work in `/app`.
2. Publish the final QuantBase article at the submitted URL, with the final visuals and accurate three-track claims.
3. Provide a rehearsable 90-second route: METHU → evidence → memory reuse + attributed agent note → brain source/path.
   Link those exact states from the Tracks table; distinguish the loaded source-only graph from optional AI extraction.

**Validation and limits**

37 main browser states plus follow-up checks: no normal-page console errors, page overflow or broken loaded
images; mobile menu, E highlighting, memory node keyboard controls and B source expansion worked.
All three README screenshot URLs and ten `BLOG-FINAL.md` image URLs returned 200. Local reviewed documents
use QuantBase and make no promised-profit claims; no credential/contact-PII patterns were found in them.
Gitleaks scanned **25 commits with no leaks**. Relevant agent, MCP, privacy and real embedded-FalkorDB track
tests: **65 passed, 1 skipped** (the separately configured live-lineage test). No new public note or key was submitted.
Temporary screenshots, logs and structured observations are in `/tmp/sniff-astra-review/`.
