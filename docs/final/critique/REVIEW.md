**Sniff submission critique · 18 October 2026**

**Verdict: solid engineering, uneven selling. Overall: 7/10 as presented.** This does not read as fully robotic. The failed hub experiment, METHU discovery and negative prediction result sound like builders explaining work they did. The form sounds like a compressed architecture document; parts of the blog and video sound like a polished launch template. You have a better project than the first minute of the pitch reveals. A tired judge may remember “meme trading, dog, big numbers” before remembering the actual graph insight.

I checked the supplied [form](submission-text.md), [published blog](https://dev.to/quantbase/sniff-four-days-one-graph-and-an-honest-answer-about-meme-coins-47af), [live site](https://sniff.quantbase.live), public APIs and selected implementation details. Video assessment uses the **107.4-second revised cut** described in [video-report.md](video-report.md) and [video-frames.jpg](video-frames.jpg), including its added memory/brain scene. I did not watch or hear the upload; voice scores concern the script, not delivery or authorship. The published blog matches the supplied source apart from its animated hero and added video embed.

**1. Scores out of 10. Higher voice scores mean more human.**

| Material | Human voice | Showcasing power | Framing/story | Judging fit | Overall |
|---|---:|---:|---:|---:|---:|
| Form | 6 | 7 | 6 | 8 | 7 |
| Blog | 7.5 | 8 | 7 | 8 | 7.5 |
| Video script + sampled frames | 7 | 6.5 | 5.5 | 6.5 | 6.5 |
| Submission together | 7 | 7.5 | 6.5 | 7.5 | 7 |

- **Form:** The problem is clear and all three tracks are named. But algorithm names, schema arrows and MCP method names compete with the reason to care. The current description is already 1,498 characters; spend that space on one finding and observable behavior. “Always” and “signed” make the language less defensible.
- **Blog / best-blog lens:** The hub mistake, failed creator-share heuristic, useful FalkorDB feedback and negative research result are the strongest material. Those are lessons another builder can use. At roughly 3,300 words, with DEV estimating 14 minutes, it asks too much before delivering METHU. Day 4 switches into audit-report prose; the trading-speed detour starts a second story. “We could have hidden that result” asks for moral credit the result already earns. Keep the candor, remove that sentence. A credible best-blog contender after editing, but the current draft dilutes its best passages.
- **Video:** The dog gives it personality and the visual identity is consistent. The sampled frames suggest an attractive promo, but UI evidence is small beside cinematic imagery. The first answer appears around 34 seconds; the explanatory graph sequence starts around 65 seconds. Memory and brain arrive at 85–98 seconds. That order makes the tracks feel appended. The QuantBase race occupies attention that should go to the investigation. Some app shots are design images or still screenshots, so they demonstrate appearance more than a completed interaction.

**Fit to the actual [track focus lists](https://www.wemakedevs.org/hackathons/falkordb):** These are focus areas, not a requirement to implement every bullet. The site publishes no detailed best-blog scoring rubric.

- **Track 01: 9/10.** Strong multi-hop investigation, algorithms exposed as tools, MCP access and inspectable results. Show the agent choosing its next tool from a finding, then the citation highlight. Its demonstrated action is investigation; the trading race does not establish graph-driven execution.
- **Track 02: 7/10.** Persistent findings, session recall and a visible second-agent note support the entry. It does not demonstrate the full memory taxonomy, high-concurrency behavior or tenant isolation. Raw conversation text is deliberately not stored. Say “persistent investigation memory,” not “persistent conversation history.”
- **Track 03: 5.5/10.** Source attribution and refresh behavior fit. The current corpus is public docs/pages, with no demonstrated ticket/chat ingestion, ownership/expertise relationships or extracted entity-to-entity decision paths. This is the narrowest track; presenting all three as equally mature weakens the strongest one.

**Claim corrections before polishing:** “Any coin” exceeds a snapshot ending **14 October, 18:45 UTC**. Funding links identify wallets, not people or proven common ownership. Citation checks validate IDs and tool compatibility, not numbers, subjects or truth. Agent labels are self-declared, not authenticated signatures. Automatic exact-result reuse is within the same session and a one-hour freshness window; cross-session recall aggregates findings. The web agent calls shared tools directly; external agents access them through MCP ([agent](../../../app/agent.py), [memory](../../../app/memory.py), [MCP](../../../app/mcp.py)). The video’s “became the agent inside QuantBase” also sounds more complete than the live homepage’s “becoming a core feature” and “In development.”

**2. Five weak sentences, with exact replacements.**

1. **Form:** “The answer is always two or three hops away, so it is a graph problem.” **Replace:** “A creator's wallet can look new even when its funder has paid dozens of other creators.” This gives a reason to follow the graph without promising an answer every time.
2. **Form:** “Acts on connected data (Track 01): the agent chooses among graph tools over MCP (multi-hop funding trails, algo.WCC funding rings, algo.SPpaths for "how are these two connected?") on 632k coins and 424k wallets.” **Replace:** “Sniff follows funding trails, groups connected launches and finds paths between wallets. Other agents can use the same tools over MCP.” Put the scale in its own sentence.
3. **Form:** “Memory and coordination (Track 02): a persistent memory graph (Session → Question → Evidence → Coin/Wallet) lets follow-ups reuse earlier findings across sessions with their original provenance, and other agents share state through memory_recall and memory_note, leaving signed, timestamped notes on the same coin.” **Replace:** “Sniff saves findings with their sources and timestamps. Other agents can read findings across sessions and leave dated notes under self-declared names.” This fixes both density and the implication of verified signatures.
4. **Blog:** “The loaded `brain` is a **source-only corpus of 12 public documents**, with zero AI requests and zero extracted entity-to-entity relationships.” **Replace:** “We loaded 12 public QuantBase documents. Sniff finds the relevant passages and links you to their sources. We have not loaded relationships between the named products, policies and decisions.” Lead with what someone can do, then state the limit.
5. **Blog:** “Whatever the graph knows has already shown up in the price.” **Replace:** “In this test, the graph features added no measurable predictive value once we included the first minutes of trading.” Your experiment supports the narrower finding, not a universal explanation of markets.

**3. What is undersold, and where to put it.**

- **The METHU reveal:** One creator, one launch; follow its funder and find 71 other creators. Put this in the **first paragraph of the form, the blog opening, and the first 10 seconds of a future video**. Show the citation and highlighted graph together. The [live dossier](https://sniff.quantbase.live/api/dossier?mint=3LaVxn1Pp5gDjJZgGrpbQ8gRKj7GxgPE8cjF62Svpump) confirms the 72-coin result.
- **Knowing when to stop:** The hub rule prevents a shared exchange-like wallet from making unrelated creators look coordinated. Put one sentence **immediately after the METHU demonstration**, with the existing before/after hub diagram. Keep “exchange-like”: the threshold is a heuristic, not an exchange identity check.
- **Enforcement beyond prompting:** Show a model sentence disappearing because its citation is missing or incompatible, followed by a retained sentence whose evidence opens. Put this **at the start of Day 2 and directly after the video’s citation click**. Label it citation validation; do not call it proof of truth. This is a proposed demonstration, not something I observed in the uploaded video.
- **Real scale and relevant speed:** Pair 632,339 launches / 424,007 wallets / ~1.5M links with one readable result. Put **30-second bulk load beside the graph schema**, and the recorded **4.4–8.4-second answers across 10 live questions** beside the investigation demo ([recorded evaluation](../../EVAL.md)). The 1.08-second race measures notification plus order sending, not graph investigation or confirmed execution; the illustrative human timeline is not a controlled comparison.
- **An observable agent handoff:** The [live METHU memory page](https://sniff.quantbase.live/memory?entity=coin:3LaVxn1Pp5gDjJZgGrpbQ8gRKj7GxgPE8cjF62Svpump) now shows four findings and one `quantbase-research-agent` note. Put that note **beside the original finding in Day 4 and the Track 02 video scene**. Its label is self-declared, its status unverified, and it has no linked evidence IDs. It demonstrates a shared record, not an authenticated autonomous trading handoff.
- **A useful company answer and a useful negative finding:** Open the **paper/live example first in Day 4**, then explain the graph. It returns source excerpts saying live trading is opening soon. Put the prediction test **immediately after the core investigation story**, before broader QuantBase context. That finding explains the product boundary better than repeated “honest” slogans. The [brain status](https://sniff.quantbase.live/api/brain) confirms 12 documents and 93 sections; the loaded corpus remains source-only.

**4. Rewritten form description. Paste only the text inside the block; under 1,500 characters.**

```text
METHU's creator had launched just one coin. Its funder had paid 71 other creators, each with one launch. None of those 72 coins had graduated to a trading pool in our snapshot. Sniff lets you follow that trail and inspect the evidence.

Built by QuantBase, Sniff uses FalkorDB across three tracks:

01 · Connected data: The agent chooses graph tools to trace funding, group related launches and find paths between wallets. These tools also work over MCP. It covers 632,339 coins, 424,007 wallets and about 1.5M links. It stops at exchange-like hubs to avoid linking unrelated creators. Click a citation to inspect its graph evidence. The server drops model sentences without valid, compatible citations; this checks sourcing, not truth.

02 · Memory and coordination: Sniff saves findings with their sources and timestamps. Follow-ups in the same session reuse recent results; other agents can recall findings across sessions and add notes under self-declared names. A second agent's METHU note is visible on /memory.

03 · Company brain: Ask about QuantBase products and policies across 12 public documents. Answers quote the relevant sections with [B#] source links. Reloading changed sources retires stale sections.

All 12 tools share one MCP endpoint. The coin snapshot ends on 14 October 2026, 18:45 UTC. Sniff shows recorded history; it does not predict prices or recommend trades.
```

**5. Top three blog edits: exact replacement text.** Apply the sentence corrections above too.

**Edit 1: Change the opening heading to “One creator, 72 connected launches”. Replace the first two sections, through “We called it Sniff”, with these paragraphs:**

> METHU's creator had launched one coin. That looked like a first attempt until we followed the payment that funded the wallet: the same payer had funded 71 other creators. Each had launched one coin. None of those 72 coins had graduated to a trading pool in our snapshot.
>
> During Graph Hacks, we built Sniff around history our QuantBase collector had already recorded. You can ask about a coin, follow its connections and inspect the evidence. The FalkorDB graph contains 632,339 pump.fun launches and 424,007 wallets, recorded through 14 October 2026, 18:45 UTC.
>
> The hard part was deciding which connections meant anything. One exchange-like wallet had funded 33,747 wallets in our data. If we let the agent walk through it, unrelated creators looked connected. That mistake shaped the rest of the build.

**Edit 2: Replace Day 4’s prose before its illustration with these paragraphs; retain the illustration’s existing live-versus-optional caption:**

> We added two more FalkorDB graphs on the last day: one for saved investigations, one for QuantBase's public documents.
>
> On /memory, you can see four METHU findings and a dated note under the name quantbase-research-agent. Follow-ups reuse recent results from the same session. Other agents can read findings across sessions through MCP and add observations. Each finding keeps its source tool and timestamp. Agent names are self-declared, and notes remain unverified.
>
> For the company brain, we loaded 12 public documents. Ask “How does QuantBase handle paper vs live?” on /brain, then open a [B#] citation to read the source section. We combine graph lookup with full-text search. Today's graph connects documents, sections and named products or policies; it contains no extracted relationships between entities. Reloading changed sources retires old sections. Our [graph documentation](https://github.com/avasis-ai/quant-agent/blob/main/docs/GRAPH.md) covers the privacy checks and optional richer builder.

**Edit 3: Replace the entire “The bigger product: Sniff inside QuantBase” section, including its two images and race comparison, with this paragraph:**

> We're building this research into QuantBase, where users can try trading strategies with play money. The graph demo is live at [sniff.quantbase.live](https://sniff.quantbase.live); the homepage still describes the dashboard integration as in development. Try METHU, inspect its evidence, then open the memory page to see the findings another agent can use.

**Change the title: yes.** “Four days” is generic hackathon framing; “honest” asks readers to accept your self-description. “One graph” also obscures the three-graph implementation. Three options, strongest first:

1. **METHU had one creator. Its funder had paid 71 more.**
2. **Building Sniff: 632,339 meme coins, with evidence you can inspect**
3. **What a graph of 632,339 meme coins could tell us, and what it couldn't**

**6. Video: human script, with ad-like repetition and claims to narrow. Future cut only.** The pixel-dog line is warm; keep it. The long spoken number list and repeated “proof” promises are the stiffest parts. “Every answer comes with its proof” also exceeds the actual citation checker. Move the METHU reveal ahead of the timeline, give the result enough screen space to read, and demonstrate one memory recall and one source click. These are editorial recommendations from the script and sampled frames; I cannot assess pronunciation, voice naturalness, music balance or continuous motion.

1. **S04, 34.4 s:** “Ask about any coin, and the agent walks the graph. Every sentence carries an evidence tag, and the map lights up to show you where it came from.” **Replace:** “Choose a coin from our snapshot. Sniff follows its funding trail, and you can open the graph behind each cited finding.”
2. **S05, 44.2 s:** “Today, Sniff became the agent inside QuantBase. A person checking a new coin by hand takes about a minute. Sniff hears a graduation in about a second, and sends in seventy-six milliseconds.” **Replace:** “We tried ten questions on the live site. Each answer took about four to eight seconds. Click a citation to inspect the graph behind a finding.” This uses the recorded research benchmark; it is not a new measurement or latency guarantee.
3. **S07, 65.0 s:** “Here's how the graph works. Funders pay creators. Creators launch coins. When one wallet funds dozens of creators, that's a ring. Exchanges are hubs, so the trail stops there, and Sniff tells you so. Every claim has proof. History, not a prediction.” **Replace:** “METHU's creator had launched one coin. Its funder had paid 71 other creators. None of those 72 coins had graduated in our snapshot. We stop at exchange-like hubs, where a shared funder tells us too little.”
