---
title: "Who's really behind a meme coin? We built a graph agent to find out"
published: false
description: "How team QuantBase built Sniff on FalkorDB: a graph of 632,339 pump.fun launches, an agent with citation checks, and the test that told us what Sniff can't do."
tags: falkordb, graphdatabase, ai, agents
cover_image: https://raw.githubusercontent.com/avasis-ai/quant-agent/main/docs/blog/01-hero.jpg
---

*By team QuantBase, for WeMakeDevs × FalkorDB Graph Hacks, October 2026*

![A small brown dog on a dark ridge, nose to the ground, following glowing threads that link hundreds of coins across a valley](https://raw.githubusercontent.com/avasis-ai/quant-agent/main/docs/blog/01-hero.jpg)
*Every coin leaves a trail. The trick is knowing which threads to follow.*

## A new coin, an unfamiliar creator

A new coin appears in your feed. People are buying it. You can see a name and a price, but you have no idea who made it. Before putting money in, you'd like to know who you're dealing with.

Meme coins are joke tokens anyone can launch in a minute. On pump.fun, the site where most of them launch, you can start by checking the creator's wallet, an account address. Funding a wallet means sending it the few cents it needs to launch. Follow that payment and you might find other creators the same payer funded.

We built Sniff during Graph Hacks to follow those connections. To a graph, this is a fraud-ring problem: accounts that look unrelated can share a payer. A shared payment is a lead to inspect, not proof of fraud or common ownership. You don't need to trade these coins to recognise the database problem.

## Day 1: we loaded the graph, then connected too much

We started with a snapshot from our QuantBase collector, which existed before the event. It ends on **14 October 2026 at 18:45 UTC**. First we had to remove other launch sites and old tokens that someone had reported as new. One established coin had a fake September launch date. It didn't belong in a launch history.

We kept **632,339 coins, 424,007 wallets and about 1.5 million links**. FalkorDB's bulk loader took **30 seconds** to load them. The graph used 521 MB of memory.

![The lineage graph schema: Wallet CREATED Coin, Wallet FUNDED Wallet, Wallet SNIPED Coin, Coin LINKS Handle, Wallet IN_RING Ring, with Hub as a dashed dead end](https://raw.githubusercontent.com/avasis-ai/quant-agent/main/docs/blog/02-graph-schema.png)
*The `lineage` graph. Five kinds of thing, five kinds of link. The questions that had been painful in SQL became one Cypher pattern each.*

Our first query followed the path we'd been trying to untangle with SQL joins: coin, creator, payer, other creators paid by that payer. In Cypher, FalkorDB's graph query language, we could write that path as one pattern.

Then we tried connecting random coins. Our first version kept finding paths within four hops. We'd built an excellent way to discover exchanges.

An exchange, a service where people buy and sell cryptocurrency, sends withdrawals from shared accounts. Those accounts appear as funders in our data. One had paid **33,747 wallets**. Walking through it made strangers look like collaborators.

We labelled wallets that funded more than 200 others **hubs**. There were 89. We removed their incoming funding links and stopped queries from walking through them. You can see that a payment came from an exchange-like wallet; you can't use it as a bridge to thousands of other creators.

![Before and after: on the left, one glowing hub connects seven groups of wallets; on the right, the hub is a dashed box and every trail stops at it, leaving the groups separate](https://raw.githubusercontent.com/avasis-ai/quant-agent/main/docs/blog/03-hub-dead-end.png)
*Day 1's biggest lesson. A hub is a bridge to nowhere, so we turned it into a wall.*

We tried distinguishing exchanges from groups launching lots of coins by the share of funded wallets that became creators. Our funding data covered creators' funders, so even the biggest hub showed 80% creators. We'd selected the answer with our sample. We kept the 200-wallet rule and documented the limit.

With hubs excluded, `algo.WCC`, the connected-components procedure, found **6,556 rings**: groups joined by funding and coin creation, with at least two creators. Of 3,900 multi-creator groups our collector had found by other means, 3,824 fell inside a single graph ring. That gave us a check against an existing method.

## Day 2: we made Claude cite its sources

We asked Claude to explain a coin's history. Then we had to decide how much of its answer we could let through.

We gave it nine tools for looking up coins, following payments and finding shared connections, including early buyers and social accounts. Each runs fixed, read-only Cypher. Claude chooses tools and writes prose; it never writes the database query. It gets up to eight model/tool rounds, with several calls allowed in a round.

The tools return **evidence IDs**, labels such as E1 and E2 that identify the nodes and links behind a result. Every factual sentence must cite evidence of the matching kind. **The server rejects sentences that don't.** Explicit server-owned context and refusal text are exceptions.

An invented ID gets removed. So does a citation from the wrong tool: a payment result cannot support a claim about a reused social account. A sentence covering both topics needs both kinds of evidence. After those checks, the server deletes factual sentences with no valid citation and adds its own computed context line.

This **checks sourcing, not truth**. A made-up launch count can pass if Claude attaches a valid coin-lookup ID. The checker doesn't establish that a number matches the result or that the sentence names the right subject. You still need to inspect the evidence.

![The agent loop: a question goes to Claude, which calls nine read-only tools, drafts an answer with evidence ids, passes a citation check, and reaches the app; a fixed dossier is the fallback](https://raw.githubusercontent.com/avasis-ai/quant-agent/main/docs/blog/04-agent-loop.png)
*The model chooses the tools and the words. The checker enforces citation IDs and matching evidence kinds; the map lets you inspect the evidence.*

Without an AI key, or if the call fails, server templates produce a fixed summary from the same tools.

That evening we tried a coin called **METHU**. Its creator had launched one coin. We followed the payment to that creator and found that the payer had funded **71 other creators**. Each had launched one coin. Across those 72 coins, none had "graduated": raised enough to move to a real trading pool, a rare outcome in our data. That's what we found in our snapshot, which ends on 14 October 2026 at 18:45 UTC.

Looking at METHU's creator alone, we'd have missed the other 71. We wanted someone reading that answer to be able to check the same path.

We prepared 30 evaluation questions, including six requiring refusal or "no evidence". The scripted run passed all 30; it tested the plumbing, not Claude's judgement. We tried 10 questions on the live site. All ten answers used the expected tools, valid citations and no trading advice. Only five stayed within five sentences. We added a five-sentence cap, plus the closing line.

## Day 3: tap E4 and follow the payment yourself

Paste a coin into Sniff and you see the investigation steps arrive: checking who made it, who paid them, who else that payer funded. On Day 3 we put a map beside the answer.

Tap **E4** and the map dims the other nodes, leaving the wallets and coins behind that evidence highlighted. You can follow the connection yourself without reading a query result table.

![The Sniff app on METHU: the coin card on the left shows one payer who also paid 71 other creators, none graduated; on the right the map highlights the payer and the 71 other creators for evidence E4](https://raw.githubusercontent.com/avasis-ai/quant-agent/main/docs/blog/05-methu-evidence.jpg)
*METHU, with evidence E4 selected: one payer, 71 other creators, 0 graduations. (Wallet addresses blurred for this post.)*

Exchange-like wallets have dashed outlines where trails stop. The coin card reads the graph without AI, and the interface works on a phone. We expose the nine investigation tools over MCP, a protocol agents use to call tools. Connect your own client with:

```bash
claude mcp add --transport http sniff https://sniff.quantbase.live/mcp
```

## Day 4: memory, and a company brain

Ask a follow-up about the same coin and we shouldn't have to start from scratch. On the last day, we added two FalkorDB graphs: saved investigations in `memory`, and QuantBase's public documents in `brain`.

On [/memory](https://sniff.quantbase.live/memory?entity=coin:3LaVxn1Pp5gDjJZgGrpbQ8gRKj7GxgPE8cjF62Svpump), you can see four METHU findings. Follow-ups reuse recent results from the same session. Other agents can read findings across sessions through MCP and add observations. Each finding keeps its source tool and timestamp. Agent names are self-declared, and notes remain unverified.

For the company brain, we loaded 12 public documents. Ask "How does QuantBase handle paper vs live?" on [/brain](https://sniff.quantbase.live/brain), then open a [B#] citation to read the source section. Paper trading means trying a strategy with play money; live trading uses real money. We combine graph lookup with full-text search. Today's source-only graph connects documents, sections and named products or policies; it contains no extracted relationships between entities. Reloading changed sources retires old sections. Our [graph documentation](https://github.com/avasis-ai/quant-agent/blob/main/docs/GRAPH.md) covers the privacy checks and the optional richer builder.

![Two small graphs: on the left, Session ASKED Question FOUND Evidence ABOUT Coin or Wallet, with a Note from another agent; on the right, Doc, Section, Decision and Finding linked by PART_OF, MENTIONS and SUPPORTS](https://raw.githubusercontent.com/avasis-ai/quant-agent/main/docs/blog/06-memory-brain.png)
*Day 4 architecture: the live brain uses MENTIONS/PART_OF; SUPPORTS in this illustration is an optional AI-builder capability. Agent notes are attributed observations, labelled "agent note · not verified".*

## Then we tested whether the graph could predict anything

We took 23,408 graduated coins and tried predicting how they did afterwards. We run trading research on this data too, and needed to know whether these connections helped.

We used only information available at graduation: the payer's other creators, payments two steps back, reused social accounts and shared early buyers. We trained on older coins and tested on the newest third.

In isolation, we found associations. Coins reusing a social account from another creator's coin were 18 percentage points less likely to be alive an hour later.

Then we included the first minutes of trading. **In this test, the graph added no measurable predictive value.** The change in AUC, a measure of how well the model ranks outcomes, stayed within ±0.01. We couldn't turn the connections we'd found into a demonstrated improvement over those early trading signals.

![A small dog carrying a lantern on a mountain path at dusk; the light shows the footprints and coins behind it clearly while the path ahead disappears into fog](https://raw.githubusercontent.com/avasis-ai/quant-agent/main/docs/blog/07-lantern.jpg)
*Sniff can light up where a coin came from. It can't see through the fog ahead, and it doesn't pretend to.*

That result set the boundary for Sniff. We describe recorded history and show the evidence. We don't recommend buying or selling, label coins "safe" or "scam", or promise a return. Answers close with *history, not a prediction*.

METHU's 72 connected launches remain worth examining. You can check their history without treating it as a forecast for the next coin.

## What we liked in FalkorDB, and where we tripped

Changing the hub rule meant rebuilding the graph. With a 30-second bulk load, we could afford to try again. That was our favourite part of working with FalkorDB 6.0.2.

We used range indexes for node keys and a full-text index for coin names and symbols. `algo.WCC` found the rings in 2.9 seconds. For connections between two things, we used `algo.SPpaths`, filtering out hubs and social handles shared across platform-sized groups. `GRAPH.RO_QUERY` kept investigation queries read-only, with per-query timeouts.

We also lost time following documentation that didn't match our running server. Procedure names varied between pages. On 6.0.2, the names included `algo.WCC`, `algo.BFS`, `algo.pageRank`, `algo.labelPropagation` and `algo.SPpaths`. We checked them with `CALL dbms.procedures()`.

The documented `db.idx.fulltext.createNodeIndex('Coin','name','symbol')` failed. `CREATE FULLTEXT INDEX FOR (c:Coin) ON (c.name, c.symbol)` worked. `WITH` projections needed `AS` aliases. Query timeouts couldn't exceed the server's `TIMEOUT_MAX`, 15 seconds by default. `sum()` returned floats, so we cast counts to integers.

And some coin names were a backslash. The bulk loader uses that as its default escape character, so we had to pass `-x none`. Of course a database import for joke coins would break on a joke-sized name.

We'd love a generated procedure reference per version, full-text docs that lead with the working `CREATE` syntax, and a loader warning for lone escape characters. Those changes would have saved us time. The fast rebuilds let us keep experimenting through the rough edges.

## Where this goes next

Open METHU, select a citation, then visit memory. You can follow a finding from a payment through to something another agent can reuse.

We're building this research into QuantBase, where users can try trading strategies with play money. The demo is live at [sniff.quantbase.live](https://sniff.quantbase.live); the homepage still describes the dashboard integration as in development.

## From a pixel dog to a product

The day before the event began, sniff.quantbase.live was a coming-soon page with one thing on it: a small animated pixel dog, sniffing a coin, on a 3.2-second loop.

Four days later, you can follow a payer across 72 launches, check the agent's sources on a map and carry findings into another session. We also have a prediction test that gave us a reason to narrow our claims. We're taking that work into QuantBase, with the dog still out front.

![A small dog sitting on a cliff at sunrise, looking over a valley with a lit town, while ember sparks draw a pixel-art dog in the sky](https://raw.githubusercontent.com/avasis-ai/quant-agent/main/docs/blog/10-close.jpg)
*From a pixel dog on a coming-soon page to a product. History, not a prediction.*

## Try it

Paste METHU's address into the app, or choose its example, and follow the payer:

- **App:** [sniff.quantbase.live](https://sniff.quantbase.live). Try the METHU example.
- **Your own agent:** `claude mcp add --transport http sniff https://sniff.quantbase.live/mcp`
- **QuantBase:** [quantbase.live](https://quantbase.live)
- **Code:** [github.com/avasis-ai/quant-agent](https://github.com/avasis-ai/quant-agent)

Built in four days by team QuantBase, on FalkorDB, Claude and a lot of pump.fun history. Nothing here is financial advice.
