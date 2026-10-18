# Blog rewrite result · 18 October 2026

Rewrote [BLOG-FINAL.md](../BLOG-FINAL.md) for readers who know databases but have never traded a meme coin. Applied Abhay's appended update in [the brief](BLOG-REWRITE-BRIEF.md#update-from-abhay-2140-ist-overrides-the-above): the title is **Who's really behind a meme coin? We built a graph agent to find out**, the opening is an illustrative human scene, and METHU appears as the worked example on Day 2.

The article has **2,265 whitespace-delimited words after front matter**, including image descriptions and the command block. Excluding image descriptions, link destinations and the fenced command block gives **2,012 words**, including the byline, headings and captions. Both counts meet the 1,800–2,400-word requirement.

All **eight** original Markdown image lines and their captions remain byte-for-byte identical, in the original order, with the same URLs. Front matter is unchanged except for the explicitly requested title update. The article keeps the hub mistake, citation limitations, map, Day 4 qualifications, negative prediction result, FalkorDB feedback and the three requested closing sections. No prohibited branding, buzzwords or em dashes appear in the article.

Regenerated [app/static/blog.html](../../app/static/blog.html) with `.venv/bin/python -m build.blog`. The generator previously retained an older hard-coded heading and metadata title; [build/blog.py](../../build/blog.py) now reads the front-matter title for the H1, browser title and Open Graph title as well as regenerating the body.

Removed the old assertion that a public METHU agent note already exists. [README.md, lines 40–45](../../README.md#tracks) records four findings and **no public METHU notes**. The article retains the implemented ability to add observations and the exact qualifications: self-declared agent names, unverified notes, source-only brain and no extracted entity relationships. It describes dashboard integration as in development.

## Validation

- `.venv/bin/python -m pytest -q`: **98 passed, 10 skipped** with the default, unconfigured database connection.
- With the existing local snapshot database configured, the full suite passed: **108 passed, zero skipped**. This includes the DuckDB comparisons, scripted evaluation and isolated embedded-FalkorDB memory/brain tests. No paid model calls were made.
- A separate read-only query against that local snapshot confirmed METHU's creator had zero other launches, its payer funded 71 other creators with 71 coins and zero graduations, and the complete group had 72 creators with exactly one launch apiece. METHU itself had not graduated.
- Browser checks at **1440×1000** and **390×844** verified HTTP 200, the new H1/browser/Open Graph title, ten story headings, all eight article images decoded, the human opening before METHU, required claim qualifications, no page overflow and no browser errors. The desktop and phone hero screenshots were inspected.
- Repeated generation produces identical HTML; front-matter/image preservation checks and `git diff --check` pass.

Full-suite command, using existing local files without printing credentials:

```bash
FALKORDB_HOST=127.0.0.1 \
FALKORDB_PORT=16379 \
FALKORDB_PASSWORD_FILE=/tmp/sniff-qa/falkordb-local.pw \
SNIFF_ENV_FILE=/tmp/sniff-fix-preview.env \
  .venv/bin/python -m pytest -q
```

The query tests rewrite an expected-results JSON file with ordering-only differences; those generated differences were restored. No test fixture changes are part of this rewrite. Temporary browser evidence is in `/tmp/quant-blog-rewrite-browser.json`, `/tmp/quant-blog-rewrite-1440.png` and `/tmp/quant-blog-rewrite-390.png`.

No deployment, push, publication or production write was performed. The input brief was left as supplied.

## Factual claim inventory

The table covers factual assertions in the title/front matter, body, headings, image text and closing links. Repeated assertions share an entry. The opening feed scene is hypothetical, not a report of a particular launch or buyer. Humour, preferences and the dog/lantern metaphors are editorial language.

“Original” below means the article read at the start of this task, pinned to [commit 371f766](https://github.com/avasis-ai/quant-agent/blob/371f766/docs/BLOG-FINAL.md). Historical build timings, the trading experiment and the coming-soon story are documented results from those sources, not new benchmarks performed during this rewrite. The basic crypto definitions use the wording prescribed by the brief; “a minute”, “most” and “a few cents” are its introductory shorthand, not new market-share, fee or launch-time measurements.

| ID | Claim retained or explained | Source |
| --- | --- | --- |
| 01 | Team QuantBase built Sniff as a graph agent for WeMakeDevs × FalkorDB Graph Hacks in October 2026. | [README.md:10–11](../../README.md#sniff-by-quantbase), [agent architecture](../../README.md#the-agent). |
| 02 | The event build spans four days, 15–18 October 2026; the day headings describe that build. | [README.md:10–11](../../README.md#sniff-by-quantbase), [README.md:240–244](../../README.md#what-existed-before-the-event), Original's Day 1–4 sections. |
| 03 | A meme coin is a joke token anyone can launch in a minute. | [Brief:11–12](BLOG-REWRITE-BRIEF.md#voice), prescribed introductory definition. |
| 04 | pump.fun is the site where most of those coins launch. | [Brief:13](BLOG-REWRITE-BRIEF.md#voice), prescribed introductory definition. |
| 05 | A wallet is an account address. | [Brief:14](BLOG-REWRITE-BRIEF.md#voice). |
| 06 | Funding a wallet means sending it the few cents needed to launch. | [Brief:15](BLOG-REWRITE-BRIEF.md#voice); no claim about METHU's dollar-denominated launch cost is made. |
| 07 | Following a creator's funding payment can reveal other creators paid by the same account. | [README.md:113–114](../../README.md#why-a-graph), [fixed `siblings` query](../../app/queries.py). |
| 08 | The graph problem resembles investigating a fraud ring; a shared payer does not by itself establish fraud or common ownership. | [Brief:17](BLOG-REWRITE-BRIEF.md#voice) supplies the framing; [hub limitations](../GRAPH.md#decisions) and [historical-only policy](../../README.md#honest-limits) constrain the inference. This is a modelling analogy, not an accusation. |
| 09 | The QuantBase collector and exported source snapshot existed before the event. | [GRAPH.md:3](../GRAPH.md), [README.md:240–244](../../README.md#what-existed-before-the-event). |
| 10 | The snapshot ends on 14 October 2026 at 18:45 UTC. | [GRAPH.md:3](../GRAPH.md), [README.md:197–198](../../README.md#honest-limits). |
| 11 | The input included other launchpads and established tokens reported as new; these were excluded. | [GRAPH.md:7,17](../GRAPH.md#decisions). |
| 12 | One established coin had a false September launch date. | [GRAPH.md:17](../GRAPH.md#decisions) identifies BONK and the false 2026-09-20 date. |
| 13 | The retained graph has 632,339 coins. | [GRAPH.md:7](../GRAPH.md), [README.md:73](../../README.md#the-graph-lineage). |
| 14 | It has 424,007 Wallet nodes. | [GRAPH.md:8](../GRAPH.md), [README.md:74](../../README.md#the-graph-lineage). |
| 15 | It has about 1.5 million links. | [GRAPH.md:12](../GRAPH.md) lists the five edge counts; [README.md:79](../../README.md#the-graph-lineage) gives the exact total, 1,513,175. |
| 16 | FalkorDB's bulk load took 30 seconds. | [GRAPH.md:14](../GRAPH.md), [README.md:79](../../README.md#the-graph-lineage). Repeated later to explain the value of rebuilds. |
| 17 | Reported graph memory usage was 521 MB. | [GRAPH.md:14](../GRAPH.md), measured with `GRAPH.MEMORY USAGE`. |
| 18 | The first end-to-end query followed coin → creator → payer → other funded creators. | Original, “Day 1: the snapshot, the graph, and the hub surprise”; [README.md:113–114](../../README.md#why-a-graph). |
| 19 | That path required SQL self-joins and can be expressed as a Cypher graph pattern; Cypher is the query language used for these FalkorDB tools. | [README.md:95–97,113–114](../../README.md#why-a-graph), [app/queries.py](../../app/queries.py). |
| 20 | The initial connection queries produced unhelpful paths through exchange accounts within four hops. | Original's Day 1 account; [BLOG.md, “Surprise 1”](../BLOG.md#surprise-1-hubs-make-everything-link-to-everything). The rewrite avoids the original universal “everything” assertion. |
| 21 | Exchange withdrawal accounts appeared as funders, connecting unrelated creators. | Original's Day 1 exchange explanation; [README.md:115–116](../../README.md#why-a-graph). “A service where people buy and sell cryptocurrency” explains the term exchange. |
| 22 | The largest funder in this discussion had paid 33,747 wallets. | [GRAPH.md:18](../GRAPH.md#decisions). The article calls it exchange-like rather than asserting an authenticated exchange identity. |
| 23 | The hub rule labels wallets funding more than 200 others; 89 hubs were found. | [GRAPH.md:9,18](../GRAPH.md#decisions), [README.md:75](../../README.md#the-graph-lineage). |
| 24 | Hubs have no incoming funding links, and queries do not traverse through them. | [GRAPH.md:18](../GRAPH.md#decisions), [README.md:115–116](../../README.md#why-a-graph), [funding-trail query](../../app/queries.py). |
| 25 | A hub can remain visible as the end of a funding trail. | [GRAPH.md:18](../GRAPH.md#decisions), `funding_trail` documentation and query in [app/queries.py](../../app/queries.py). |
| 26 | The team tried classifying exchanges by the share of funded wallets that became creators. | Original's Day 1 account; [GRAPH.md:18](../GRAPH.md#decisions). |
| 27 | Creator-funder sampling made that classification unreliable; the largest funder showed 80% creators. | [GRAPH.md:18](../GRAPH.md#decisions). “We'd selected the answer with our sample” explains that documented selection bias. |
| 28 | Rings are connected components of funding and creation links, excluding hubs and requiring at least two creators. | [GRAPH.md:21](../GRAPH.md#decisions), [README.md:77,117–118](../../README.md#why-a-graph), [build/rings.py](../../build/rings.py). |
| 29 | `algo.WCC` produced 6,556 rings. | [GRAPH.md:11,21](../GRAPH.md#decisions). |
| 30 | Of 3,900 independently identified multi-creator collector groups, 3,824 fell entirely within one graph ring. | [GRAPH.md:21–23](../GRAPH.md#decisions), [README.md:117–118](../../README.md#why-a-graph). This is a comparison with the existing method, not a claim of perfect identity matching. |
| 31 | Claude selects tools and writes the investigation explanation. | [README.md:81–97](../../README.md#the-agent), [app/agent.py](../../app/agent.py). |
| 32 | Day 2's investigation interface has nine tools, including lookup, funding and shared-buyer/social queries. | [GRAPH.md:34–56](../GRAPH.md#agent-tools-day-2), [README.md:95–97](../../README.md#the-agent). Day 4 adds memory and brain capabilities; nine is not presented as the final MCP tool total. |
| 33 | The investigation tools run fixed, parameterised, read-only Cypher; the model does not generate queries. | [README.md:95–97](../../README.md#the-agent), [app/queries.py](../../app/queries.py). |
| 34 | There are up to eight model/tool rounds, with multiple calls possible in one round. | [README.md:85](../../README.md#the-agent), `MAX_TOOL_TURNS` and the model loop in [app/agent.py](../../app/agent.py). |
| 35 | Evidence IDs such as E1/E2 name the nodes and edges behind tool results. | [README.md:98](../../README.md#the-agent), `Evidence` in [app/tools.py](../../app/tools.py). |
| 36 | Factual model sentences need valid citations from a compatible evidence kind; the server removes sentences that fail. | [README.md:99–106](../../README.md#the-agent), `check_citations` in [app/agent.py](../../app/agent.py), uncited-sentence regressions in [tests/test_agent.py:125–139](../../tests/test_agent.py). |
| 37 | Explicit server-owned context and refusal text are exceptions to that citation requirement. | [README.md:105–106](../../README.md#the-agent), [tests/test_agent.py:161–166](../../tests/test_agent.py). |
| 38 | Unknown IDs and incompatible citations are removed. | [README.md:99–103](../../README.md#the-agent), [tests/test_agent.py:104–121](../../tests/test_agent.py). |
| 39 | A sentence combining funding and social-account claims requires both evidence kinds. | [README.md:100–101](../../README.md#the-agent), mixed-topic regressions in [tests/test_agent.py:142–149](../../tests/test_agent.py). |
| 40 | The server adds its computed context line after checking model text. | [README.md:105–109](../../README.md#the-agent), `_verdict` in [app/agent.py](../../app/agent.py). |
| 41 | Citation checks establish sourcing/tool compatibility, not claim truth, correct subjects or numeric agreement; a false launch count can pass with a real compatible ID. | [README.md:102–104](../../README.md#the-agent), [tests/test_agent.py:152–158](../../tests/test_agent.py), which explicitly accepts “999 coins” with a real compatible E1. |
| 42 | No key or an AI-call failure leads to a fixed summary built from the same tools and server-owned templates. | [README.md:107](../../README.md#the-agent), `dossier` and `_dossier_text` in [app/agent.py](../../app/agent.py). |
| 43 | The team investigated METHU on Day 2 that evening. | Original, “Day 2: an agent that has to show its receipts”. This is the documented builder anecdote. |
| 44 | METHU's creator had launched exactly one coin. | [README.md:29–30](../../README.md#sniff-by-quantbase), Original's METHU account; independently confirmed against the existing local snapshot during this task. |
| 45 | Its payer funded 71 other creators; each of all 72 creators launched one coin, giving 72 coins. | [README.md:29–30](../../README.md#sniff-by-quantbase), Original's METHU account; independent local `coin_dossier`, `siblings` and per-creator aggregate checks. |
| 46 | None of the 72 coins had graduated in this snapshot. | [README.md:29–30](../../README.md#sniff-by-quantbase), Original; independent local read-only check. The cutoff is stated beside the result. |
| 47 | “Graduated” means raising enough to move to a real trading pool, a rare outcome in this data. | [Brief:16](BLOG-REWRITE-BRIEF.md#voice); [GRAPH.md:61](../GRAPH.md#agent-tools-day-2) reports 23,605 of 632,339 launches, or 3.7%. The research sample of 23,408 is a separate documented subset. |
| 48 | The evaluation set contains 30 questions, including six requiring refusal or no evidence. | [EVAL.md:3–7](../EVAL.md), [tests/eval/questions.jsonl](../../tests/eval/questions.jsonl). |
| 49 | The scripted run passed all 30 and tests tools/citation/scoring plumbing, not Claude's judgement. | [EVAL.md:21–24,40–42](../EVAL.md#results-snapshot-20261014t1845z-2026-10-17). |
| 50 | Ten live-site questions passed tool, citation and no-advice checks. | [EVAL.md:21–27](../EVAL.md#results-snapshot-20261014t1845z-2026-10-17). Its notes explain the scorer correction and rescoring; no larger live-model evaluation is claimed. |
| 51 | Only five live answers met the five-sentence target; the implementation now caps factual answers at five sentences plus the closing line. | [EVAL.md:35–37](../EVAL.md#results-snapshot-20261014t1845z-2026-10-17), [README.md:178–179](../../README.md#eval), `cap_claims` in [app/agent.py](../../app/agent.py). |
| 52 | Day 3 added the answer-side graph map; investigations stream their steps. | Original's Day 3 section; [README.md:156–157](../../README.md#api), [app/static/investigate.js](../../app/static/investigate.js). |
| 53 | Selecting an E citation highlights the nodes/edges behind it and dims the rest. | [README.md:90](../../README.md#the-agent), `highlight` in [app/static/graph.js](../../app/static/graph.js), citation selection in [app/static/investigate.js](../../app/static/investigate.js); [recorded live review](ASTRA-REVIEW.md). |
| 54 | Exchange-like hubs have dashed outlines in the map. | Hub styling in [app/static/graph.js:37–39](../../app/static/graph.js). Prose says “outlines”; the preserved schematic captions still describe their illustrated dashed boxes. |
| 55 | The coin card reads graph data without needing AI. | [README.md:164](../../README.md#api), `/api/dossier` in [app/main.py](../../app/main.py). |
| 56 | The investigation interface works on a phone. | [README.md's phone screenshot](../../README.md#sniff-by-quantbase), [recorded 390px live review](ASTRA-REVIEW.md). This rewrite's browser checks cover the blog, not a new full investigation review. |
| 57 | MCP lets an agent client call Sniff's investigation tools; the shown HTTP registration command points to `/mcp`. | [README.md:130–152](../../README.md#use-sniff-from-your-own-agent-mcp). |
| 58 | The final day added separate FalkorDB `memory` and `brain` graphs for saved investigations and public company documents. | Original's Day 4 section, [GRAPH.md:63–65](../GRAPH.md#memory-and-company-brain-tracks-02-and-03). |
| 59 | The public METHU memory view had four findings. | [README.md:40–45](../../README.md#tracks), [dated read-only production record](fix-live-state.json), finding count at lines 35–39. No new production fetch was performed here. |
| 60 | Follow-ups reuse recent results from the same session. | [GRAPH.md:86–92](../GRAPH.md#memory-model-and-recall), [README.md:37,148–149](../../README.md#use-sniff-from-your-own-agent-mcp). |
| 61 | Other agents can recall findings across sessions over MCP and add observations. | [GRAPH.md:90–97](../GRAPH.md#memory-model-and-recall), [README.md:148–152](../../README.md#use-sniff-from-your-own-agent-mcp), real isolated coordination test in [tests/test_tracks_falkor.py](../../tests/test_tracks_falkor.py). |
| 62 | Each saved finding retains its source tool and timestamp. | [GRAPH.md:86–92](../GRAPH.md#memory-model-and-recall), [README.md:37](../../README.md#tracks). |
| 63 | Agent names are self-declared and notes remain unverified; a note does not become verified lineage evidence. | [GRAPH.md:92–97](../GRAPH.md#memory-model-and-recall), [README.md:150–152](../../README.md#use-sniff-from-your-own-agent-mcp). |
| 64 | The loaded company brain contains 12 public documents. | [GRAPH.md:136–141](../GRAPH.md#company-knowledge-extraction-and-citations), [README.md:42–44](../../README.md#tracks), [dated production record](fix-live-state.json). |
| 65 | `/brain` answers the paper/live example with B citations that open their source sections. | [README.md:161–162](../../README.md#api), [GRAPH.md:145–149](../GRAPH.md#company-knowledge-extraction-and-citations), [recorded live review](ASTRA-REVIEW.md). |
| 66 | Paper trading uses play money; live trading uses real money. | [PUBLIC-POLICIES.md:9–14](../PUBLIC-POLICIES.md#paper-and-live-are-separate). This definition does not claim live execution is available. |
| 67 | Brain retrieval combines graph lookup and full-text search. | [GRAPH.md:143–149](../GRAPH.md#company-knowledge-extraction-and-citations), [README.md:38](../../README.md#tracks), [app/brain.py](../../app/brain.py). |
| 68 | The demonstrated brain is source-only, connecting documents, sections and named product/policy anchors; it has no extracted entity-to-entity relationships. | [GRAPH.md:136–141](../GRAPH.md#company-knowledge-extraction-and-citations), [README.md:38,42–44](../../README.md#tracks). |
| 69 | Reloading changed sources retires old sections. | [GRAPH.md:151–155](../GRAPH.md#company-knowledge-extraction-and-citations), corpus replacement regressions in [tests/test_tracks_falkor.py](../../tests/test_tracks_falkor.py). |
| 70 | Graph documentation covers privacy checks and an optional richer builder. | [GRAPH.md:103–141](../GRAPH.md#company-knowledge-extraction-and-citations). |
| 71 | The optional AI builder supports richer edges such as SUPPORTS; the live source-only brain uses MENTIONS/PART_OF. | [GRAPH.md:136–141](../GRAPH.md#company-knowledge-extraction-and-citations), [README.md:38,42–44](../../README.md#tracks). This also sources the preserved Day 4 caption. |
| 72 | The team runs trading research on the same data. | [README.md:192–196](../../README.md#honest-limits), Original's prediction section. |
| 73 | The prediction test used 23,408 graduated coins. | [README.md:192–195](../../README.md#honest-limits), [BLOG.md:107–109](../BLOG.md#the-honest-part-it-explains-it-doesnt-predict), Original. |
| 74 | Predictors used information available at graduation: payer/creator counts, two-hop funding, reused socials and shared early buyers. | [README.md:192–194](../../README.md#honest-limits), [BLOG.md:107–109](../BLOG.md#the-honest-part-it-explains-it-doesnt-predict). |
| 75 | The test trained on older coins and evaluated the newest third. | [BLOG.md:107–109](../BLOG.md#the-honest-part-it-explains-it-doesnt-predict), Original. |
| 76 | In isolation, reuse of another creator's coin's social account was associated with 18 percentage points lower one-hour survival. | [README.md:194](../../README.md#honest-limits), [BLOG.md:111–114](../BLOG.md#the-honest-part-it-explains-it-doesnt-predict). It is described as an association, not a causal effect. |
| 77 | In this experiment, graph signals added no measurable predictive value once early trading data was included; AUC changed within ±0.01. | [README.md:194–195](../../README.md#honest-limits), [PUBLIC-POLICIES.md:18–24](../PUBLIC-POLICIES.md#history-and-research-claims). “How well the model ranks outcomes” is a plain-language explanation of AUC, not an additional result. No universal market conclusion is claimed. |
| 78 | Sniff's policy is to describe history, avoid trading recommendations/safe-or-scam labels/profit promises, and close answers with “History, not a prediction.” | [EVAL.md:14–16](../EVAL.md), [README.md:8,108–109,190–201](../../README.md#honest-limits), `SYSTEM` and `base_line` in [app/agent.py](../../app/agent.py). This describes product policy rather than a proof of flawless future model behaviour. |
| 79 | The team used FalkorDB 6.0.2 and rebuilt the graph while adjusting rules. | [GRAPH.md:25](../GRAPH.md#verified-on-falkordb-602-call-dbmsprocedures), Original's FalkorDB section. |
| 80 | Range indexes cover node keys; full-text search indexes coin names and symbols. | [README.md:123–125](../../README.md#falkordb-features-used), [build/indexes.py](../../build/indexes.py). |
| 81 | WCC took 2.9 seconds. | [GRAPH.md:14](../GRAPH.md). |
| 82 | `algo.SPpaths` finds connections with hubs and platform-sized handles excluded. | [README.md:119,126](../../README.md#why-a-graph), [GRAPH.md:20](../GRAPH.md#decisions), `connect` in [app/queries.py](../../app/queries.py). |
| 83 | Investigation queries use `GRAPH.RO_QUERY` and per-query timeouts. | [README.md:127](../../README.md#falkordb-features-used), [app/graph.py](../../app/graph.py). |
| 84 | Procedure names differed across docs; verified 6.0.2 names include `algo.WCC`, `algo.BFS`, `algo.pageRank`, `algo.labelPropagation`, `algo.SPpaths`; the team checked `CALL dbms.procedures()`. | [GRAPH.md:25–28](../GRAPH.md#verified-on-falkordb-602-call-dbmsprocedures), Original's documented feedback. The report preserves the observation for that version. |
| 85 | The documented three-argument `db.idx.fulltext.createNodeIndex` failed; `CREATE FULLTEXT INDEX FOR (c:Coin) ON (c.name, c.symbol)` worked. | [GRAPH.md:29](../GRAPH.md#verified-on-falkordb-602-call-dbmsprocedures). |
| 86 | `WITH` projections needed `AS` aliases. | [GRAPH.md:30](../GRAPH.md#verified-on-falkordb-602-call-dbmsprocedures). |
| 87 | Query timeouts could not exceed `TIMEOUT_MAX`, recorded as 15 seconds by default. | [GRAPH.md:31](../GRAPH.md#verified-on-falkordb-602-call-dbmsprocedures), Original's timeout bullet. |
| 88 | `sum()` returned floats, so tool code cast counts to integers. | [GRAPH.md:59](../GRAPH.md#agent-tools-day-2), [app/tools.py](../../app/tools.py). |
| 89 | Backslash coin names broke the bulk loader's default escaping; the build used `-x none`. | [GRAPH.md:32,50](../GRAPH.md#verified-on-falkordb-602-call-dbmsprocedures), [README.md:123](../../README.md#falkordb-features-used). |
| 90 | A generated per-version procedure reference, working full-text syntax first and lone-escape loader warnings are the team's requested documentation improvements. | Original's FalkorDB feedback paragraph. These are suggestions/preferences, not claims of existing features. |
| 91 | QuantBase lets users try strategies with play money; graph integration is being built, with the homepage describing it as in development. | Original, “Where this goes next”; [PUBLIC-POLICIES.md:9–14](../PUBLIC-POLICIES.md#paper-and-live-are-separate), [README.md:235–236](../../README.md#premium-interface). No completed integration or available live execution is claimed. |
| 92 | The Sniff demo is live at `sniff.quantbase.live`. | [README.md:15–19,40–45](../../README.md#sniff-by-quantbase), [recorded production check](fix-live-state.json). This task did not deploy it. |
| 93 | The pre-event coming-soon page had a pixel dog sniffing a coin on a 3.2-second loop. | Original, “From a pixel dog to a product”; [video review's 14 October coming-soon account](critique/video-report.md). The exact loop duration is retained from the original article, not remeasured here. |
| 94 | Four days later the product could trace the METHU payer, expose sources on a map and let another session recall findings. | Claims 02, 44–46, 53, 60–63 above; [README.md's three tracks](../../README.md#tracks). This is a closing recap, not a separate benchmark. |
| 95 | Users can paste a coin address or choose the METHU example. | [README.md:3,29–30,166](../../README.md#sniff-by-quantbase), METHU example controls in [app/static/app.html](../../app/static/app.html). |
| 96 | The final links identify the Sniff app, HTTP MCP endpoint, QuantBase site and source repository. | [README.md's link table](../../README.md#sniff-by-quantbase), [MCP instructions](../../README.md#use-sniff-from-your-own-agent-mcp), Original's “Try it”. |

## Preserved images and captions

Each image line and caption was compared with the original article as an exact ordered string, including punctuation and URL. The table makes explicit which words describe artwork rather than measurements.

| Image | Caption/description claims and source |
| --- | --- |
| `01-hero.jpg` | Dog, ridge and glowing trails describe [the illustration](../blog/01-hero.jpg). “Every coin leaves a trail” is a metaphor for the funding/creation graph, not a claim of complete funding coverage. |
| `02-graph-schema.png` | The illustration describes five node labels and five link types, sourced by [README.md's graph schema](../../README.md#the-graph-lineage) and [GRAPH.md's node/edge counts](../GRAPH.md). The SQL/Cypher caption uses claim 19. |
| `03-hub-dead-end.png` | The seven pictured groups and dashed box describe [the schematic](../blog/03-hub-dead-end.png), not a measured seven-group dataset. The dead-end rule uses claims 23–25. |
| `04-agent-loop.png` | The tool/model/checker/fallback diagram and caption use claims 31–42. The words “matching evidence kinds” retain the limitation that citations do not establish truth. |
| `05-methu-evidence.jpg` | The screenshot/caption's payer, 71 other creators and zero graduations use claims 44–46; E4 selection uses claim 53. The blurred addresses are an attribute of [the supplied screenshot](../blog/05-methu-evidence.jpg). |
| `06-memory-brain.png` | The memory path uses [GRAPH.md:70–97](../GRAPH.md#memory-model-and-recall). Brain `MENTIONS`/`PART_OF` and optional `SUPPORTS`, plus unverified notes, use claims 63, 68 and 71. The caption explicitly distinguishes the illustration's optional edges from the live source-only corpus. |
| `07-lantern.jpg` | The dog, lantern, path and fog describe [the illustration](../blog/07-lantern.jpg). The caption is the history/prediction metaphor corresponding to claims 77–78. |
| `10-close.jpg` | Dog, valley and pixel-art sky describe [the illustration](../blog/10-close.jpg). The caption reprises the documented coming-soon/build story and historical-only policy in claims 78, 93–94. |
