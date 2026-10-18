# Brief: merge and polish the final Sniff site (Codex). HARD DEADLINE: committed by 21:15 IST, 18 Oct

You are on branch final/merged (= final/premium-ui: the new premium UI). Merge branch final/tracks into it (Tracks 02/03:
app/memory.py, brain.py, privacy.py, knowledge_graph.py, track_routes.py, app/static/tracks/*, /memory, /brain, the MCP tools,
plus docs/BLOG-FINAL.md, app/static/blog.html, docs/blog/*). Resolve the conflicts carefully: keep BOTH features, with the new UI
winning on look.

Then:
1. **Restyle /memory, /brain and /blog** to the new design system (the shared QuantBase Ember tokens from b4f544d). They must
   look like the same product as / and /app. Keep their behaviour and tests.
2. **Navigation:** add Memory, Brain and Blog to the site nav/footer. On the home page add a clear "Three tracks, one product"
   section:
   - Track 01: agents acting on the lineage graph (/app);
   - Track 02: agent memory and coordination (/memory, memory_recall/memory_note over MCP);
   - Track 03: the company brain (/brain, brain_ask).
   Each gets one plain sentence and a link. Replace "Track 01 · Agents that act on connected data" in the footer with all
   three tracks.
3. **Map zoom bug:** the connection map in /app opens at 250% with giant labels (docs/final/shots/app-evidence-1440.png). It
   should fit the whole graph on load (fit with padding, a sensible max zoom ~1.2) and keep labels at readable sizes.
4. **Team name** is **QuantBase** everywhere: README, LICENSE copyright line, docs/SUBMISSION.md, docs/BLOG.md, app pages.
   Use the current team name throughout tracked text (git grep). Do not change the GitHub repo name.
5. Run the full test suite (all green), take fresh screenshots of every page at 1440 and 390 into docs/final/shots-merged/,
   and fix anything ugly.
6. Commit (author avasis-ai <abhay@avasis.ai>), and finish with docs/final/MERGE-RESULT.md.
- No deploy, no push, no secrets.
