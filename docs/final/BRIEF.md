# Brief: the final premium Sniff site for Graph Hacks (Codex). HARD DEADLINE: done and committed by 21:45 IST, 18 Oct

This repo is "Sniff by Quant Agent", our WeMakeDevs × FalkorDB Graph Hacks entry (Track 01), live at https://sniff.quantbase.live
(FastAPI app in app/, static UI in app/static/, FalkorDB graph `lineage`). Read README.md, docs/GRAPH.md and app/static/app.html first.
Abhay: the current Sniff page "looks a bit sloppy and compact". Rebuild the UI as a premium platform and make clear to the
hackathon reviewers that this is a serious product: the graph intelligence is becoming a core feature of the QuantBase dashboard.

## Design
- Use the new QuantBase design language. Inspirations and tokens: ~/dev/sniff-app-prod/DESIGN-V5.md,
  ~/dev/sniff-app-astra/DESIGN-V6.md and ~/dev/sniff-app-astra/docs/astra/inspiration-*.png (if present; Astra is producing
  them now), ~/dev/sniff-app/docs/refs/palette-v5-*.{jpg,png}, and the live https://quantbase.live (warm ember palette
  #161316 / #453027 / #FF6D29 / #BABABA / white, Host Grotesk + an Instrument Serif italic accent, a white pill = the action,
  frosted glass, generous space).
- Premium graph visual quality: restyle the Cytoscape map (node shapes by type, ember accents, soft glow on the evidence
  path, smooth animated layout, crisp labels, a legend, zoom/pan controls, hubs drawn as dead ends) so it looks like a
  product, not a demo.

## Pages and sections (keep every existing route working: /, /app, /settings, /mcp, /api/*, /waitlist; never claim /admin or
## /api/waitlist)
1. **Home (/):** a full premium landing for Sniff.
   - Hero: "Sniff any coin before you buy", an ask box straight into the app, and an animated graph visual.
   - "How the graph works": funders → creators → coins, hubs as dead ends, WCC rings, shortest paths. Use real numbers
     from the graph (632,339 coins, 424,007 wallets, 6,556 rings, 1.5M links); keep them in one place.
   - A FalkorDB section: what we use (the bulk loader, range + full-text indexes, algo.WCC, algo.SPpaths, read-only
     queries with timeouts) and the MCP endpoint.
   - **"Part of QuantBase" section:** Sniff's graph intelligence ships inside the QuantBase dashboard
     (https://quantbase.live, the app at https://app.quantbase.live) where Sniff is the trading agent. Link both. Say it
     plainly: we're building a serious product, and this hackathon graph is becoming one of its core features.
   - Results: the eval table from docs/EVAL.md. Honest limits. Links: GitHub repo, video, blog.
2. **App (/app):** the investigation experience re-laid out:
   - a wide graph canvas plus a right-hand evidence panel (the answer with [E] tags), a dossier summary on top, steps
     streaming;
   - not cramped: a proper desktop layout, and stacked on mobile.
   - Keep the API contract and the behaviour the same.
3. **/settings:** restyle to match.

## Rules
- Write fresh code. All tests must pass: run them (pytest; see README for how).
- No secrets. Don't deploy (the leader deploys).
- Commit to branch final/premium-ui in logical commits (author avasis-ai <abhay@avasis.ai>).
- Take Playwright screenshots of every page at 1440 and 390 into docs/final/shots/ (run the app locally against fixtures
  or the live API read-only).
- Finish with docs/final/RESULT.md.

## UPDATE (18 Oct ~19:00 IST): the TEAM NAME IS NOW "QuantBase" (changed on the hackathon page). Everywhere you would write "Quant Agent" or "by Quant Agent", write "QuantBase" / "by QuantBase" (including the video credits: "Built by QuantBase on FalkorDB").
