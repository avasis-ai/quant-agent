# Brief: make Sniff qualify for ALL THREE Graph Hacks tracks, honestly (Codex). HARD DEADLINE: committed by 22:00 IST, 18 Oct

Repo: Sniff (team **QuantBase**), the FalkorDB entry. It currently covers Track 01, "Agents That Act on Connected Data" (graph
`lineage`, agent tools, MCP). Read README.md, docs/GRAPH.md, app/ (agent.py, tools.py, mcp.py, queries.py, graph.py).
Add real, working FalkorDB-backed features for the other two tracks. A parallel worker is restyling the UI on branch
final/premium-ui, so keep your UI to new, small, self-contained pages/components and touch existing UI files minimally.

## Track 02: Agent Memory and Coordination (graph `memory`)
- Every investigation (/api/ask and the MCP tools) writes a memory subgraph:
  - (:Session)-[:ASKED]->(:Question)-[:FOUND]->(:Evidence {id, tool, summary})-[:ABOUT]->(:Coin|:Wallet ref by
    mint/addr), with timestamps.
  - Store no PII. Visitors are session ids only.
- **Recall:** the agent gets `memory_recall(entity|session)` (what did we already learn about this coin or wallet, and
  when) and uses it before re-querying. Follow-ups in the same session reuse the evidence.
- **Coordination:** multiple agents share it. The MCP endpoint exposes memory_recall + memory_note, so another agent (e.g.
  the QuantBase trading agent) can read Sniff's findings and add its own (:Note {by, text}), with provenance, so two
  agents coordinate through the graph. Also add a cross-session "what others found about this coin" view
  (aggregate, anonymised).
- A UI page /memory: the memory graph for a coin or session, visualised.

## Track 03: Company Brain (graph `brain`)
- Build a knowledge graph of QuantBase's own PUBLIC knowledge:
  - this repo's docs (README, GRAPH, EVAL, BLOG);
  - the public site pages of https://quantbase.live (fetch them: docs, pricing, FAQ);
  - the claims/legal policy summaries;
  - the honest research findings already published in the blog.
- Nodes: Doc, Section, Decision, Finding, Metric, Product, Feature, Policy. Edges: MENTIONS, SUPPORTS, CONTRADICTS,
  PART_OF, DECIDED_ON.
- Extract with the existing AI client (ai.client_for; a cheap model; cap the cost). Re-runnable script
  build/brain.py.
- **Privacy:** ingest ONLY public sources. Run a secret/PII scan (keys, wallet private keys, emails, IPs, AWS ids) and
  refuse to load anything that matches. No internal HANDOVER or infra notes.
- The agent gets `brain_ask` (graph retrieval: entity + neighbourhood + the source section, cited as [B#] evidence like
  the [E#] ids). A /brain page lets you ask "how does QuantBase handle paper vs live?" and see the answer, its sources
  and the graph.

## Both tracks
- Tests for writes/reads, privacy refusal, and the citation contract.
- Use FalkorDB features meaningfully: indexes, Cypher paths, algo where natural.
- Load the graphs on the demo box via the existing deploy/build docs. Write the exact commands in docs/GRAPH.md; the
  LEADER runs the deploy. Locally, use a FalkorDB docker if available, or the SSH tunnel method in docs/GRAPH.md
  (needs the leader). Otherwise test against an in-memory fake + unit tests.
- Update README: a "Tracks" section explaining how Sniff satisfies 01, 02 and 03, with links to /app, /memory, /brain and
  the MCP tools.
- Team name: **QuantBase** (not "Quant Agent") everywhere you touch.
- No secrets. Commit to branch final/tracks (author avasis-ai <abhay@avasis.ai>). Finish with docs/final/TRACKS-RESULT.md.
  Don't deploy.
