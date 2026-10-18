# Brief: fix Astra's review (Codex). HARD DEADLINE: committed by 21:30 IST, 18 Oct

Read docs/final/ASTRA-REVIEW.md. Fix on branch final/review-fixes:
- **P1-1:** brain source URLs. REPO_URL must point to the published `main` branch (https://github.com/avasis-ai/quant-agent/blob/main/...).
  Every repo file it cites must exist on main. Make the loader retire the old Doc/Section records on reload. Give the leader the exact
  reload command (the leader runs it on the box).
- **P1-2:** citation check.
  - Reject uncited factual sentences. Allow only explicit server-owned context/refusal text without citations.
  - Require support for every matched topic (no union bypass).
  - Add regression tests for the probes in the review.
  - Then describe the check HONESTLY everywhere (README, BLOG-FINAL.md, blog.html, SUBMISSION.md): "every sentence must cite
    evidence of the matching kind; the server rejects answers that don't". Do NOT claim it verifies that every claim is true.
- **P2-4:** /app brain mode: B citations clickable, with source sections and links, the brain graph, the label "Public source
  excerpts", and the key banner only in dossier mode.
- **P2-5:** the blog and README describe exactly what is loaded: a source-only brain with MENTIONS/PART_OF; richer SUPPORTS/CONTRADICTS/
  DECIDED_ON edges are a capability of the capped AI builder, not shown live. Full-text runs alongside graph retrieval, not as a
  "fallback". A web source with a privacy match is refused (a local source fails the build).
- **P2-6:**
  - README and SUBMISSION.md state the verified live state dated 18 Oct 2026, with setup commands under "Reproduce".
  - The checklist points at BLOG-FINAL.md.
  - Tick only the completed checks.
- **Nice-to-haves, if time allows, in this order:**
  1. /memory: a one-click "See METHU" demo, plus a visible, clearly labelled second-agent note. The leader will post one real
     note via MCP after deploy; just make sure the UI shows notes with "agent note · not verified".
  2. /brain: clean excerpt formatting (no literal ** or list hyphens, no cut-off paragraphs in the preview).
  3. The memory graph fits at 390 px.
  4. "eight tool calls" → "eight model/tool rounds".
- Then regenerate app/static/blog.html from docs/BLOG-FINAL.md (use the existing builder; if it's missing, keep the same structure).
- All tests green. Commit (author avasis-ai <abhay@avasis.ai>). Finish with docs/final/FIX-RESULT.md. No deploy, no push.
