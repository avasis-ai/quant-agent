---
title: "Sniff: four days, one graph, and an honest answer about meme coins"
published: false
description: "How team QuantBase built Sniff on FalkorDB: a graph of 632,339 pump.fun launches, an agent with citation checks, and the test that told us what Sniff can't do."
tags: falkordb, graphdatabase, ai, agents
cover_image: https://raw.githubusercontent.com/avasis-ai/quant-agent/main/docs/blog/01-hero.jpg
---

*By team QuantBase, for WeMakeDevs × FalkorDB Graph Hacks, October 2026*

![A small brown dog on a dark ridge, nose to the ground, following glowing threads that link hundreds of coins across a valley](https://raw.githubusercontent.com/avasis-ai/quant-agent/main/docs/blog/01-hero.jpg)
*Every coin leaves a trail. The trick is knowing which threads to follow.*

## A coin graduates. You have seconds.

It's late. A pump.fun coin you've never heard of has just "graduated": it filled its bonding curve and moved to a real trading pool. The chart is climbing. A chat window is full of rocket emojis. Your thumb is over the buy button.

You have one real question, and it isn't "will it go up?" Nobody can answer that honestly. The question is: **who is behind this?** Who made it, and what happened to the last things they made?

You click the creator's wallet. It's brand new. One coin, this one. It looks clean.

It almost never is that simple. And by the time you've found out why, the moment has passed.

## The problem: the truth is two hops away

On the day we wrote this, our recorder saw **24,606 new pump.fun coins in 24 hours**. That's normal: about 25,000 a day, and only a few in every hundred ever graduate.

The wallet that launches a coin is usually made for that one launch. It tells you nothing. The story lives one or two steps further out:

- **Who paid that wallet** the few cents of SOL it needed to launch?
- **Who else did that payer fund**, and what did *those* wallets launch?
- Did the coin reuse a **Twitter account** from another coin? Did the **same early buyers** show up at the start of other launches?

Every one of those questions is a path: wallet to wallet to coin to outcome. We had months of this data in Postgres, recorded by our own QuantBase collector since September. Every question we asked of it turned into a tower of self-joins that took minutes and still missed things.

Paths are what graph databases are for. So for Graph Hacks, we gave ourselves four days to put that history into FalkorDB and build an agent on top of it. We called it **Sniff**.

## Day 1: the snapshot, the graph, and the hub surprise

We took one snapshot from the collector and kept only true pump.fun launches. (Older rows held other launchpads and even some long-established tokens that had been "reported as new". One famous coin showed a fake launch date in September. Out it went.)

What was left: **632,339 coins, 424,007 wallets, and about 1.5 million relationships.** The FalkorDB bulk loader took them in **30 seconds**. The graph used 521 MB of memory.

![The lineage graph schema: Wallet CREATED Coin, Wallet FUNDED Wallet, Wallet SNIPED Coin, Coin LINKS Handle, Wallet IN_RING Ring, with Hub as a dashed dead end](https://raw.githubusercontent.com/avasis-ai/quant-agent/main/docs/blog/02-graph-schema.png)
*The `lineage` graph. Five kinds of thing, five kinds of link. The questions that had been painful in SQL became one Cypher pattern each.*

The first query we ran end to end was the one we'd wanted for weeks: start at a coin, walk back to the creator, back to whoever paid them, and out to everyone else that payer funded. It came back instantly.

Then we asked how two random coins were connected, and the graph said: **everything is connected to everything, within four hops.**

True. And useless.

The cause was exchanges. When a creator withdraws SOL from an exchange, the exchange's hot wallet shows up as their "funder". One such wallet had funded 33,747 of the wallets we knew about. Walk through it and every stranger becomes your neighbour.

We call these wallets **hubs**: any wallet that funded more than 200 others. There were 89. We gave them their own label, cut their incoming funding edges, and made a hard rule: **no query walks through a hub.** A trail that reaches one stops and says so: "this came from an exchange-like wallet, which tells us nothing about who is behind it."

![Before and after: on the left, one glowing hub connects seven groups of wallets; on the right, the hub is a dashed box and every trail stops at it, leaving the groups separate](https://raw.githubusercontent.com/avasis-ai/quant-agent/main/docs/blog/03-hub-dead-end.png)
*Day 1's biggest lesson. A hub is a bridge to nowhere, so we turned it into a wall.*

We tried to be cleverer, telling exchanges apart from big launch farms by what share of their wallets went on to make coins. It didn't work: our funding data only covered wallets that had made coins, so even the biggest exchange looked 80% "creator". We kept the simple rule, wrote down why, and moved on.

With hubs out of the way, `algo.WCC` found **6,556 rings**: groups of wallets and coins joined by funding and creation. We checked them against the clusters our collector had found by other means. 3,824 of its 3,900 multi-creator clusters fell entirely inside a single ring. The graph and the old method agreed.

## Day 2: an agent that has to show its receipts

An AI model writing about wallets and money is exactly where you don't want made-up facts. So we built the agent around one rule for factual answer text: **every sentence must cite evidence of the matching kind; the server rejects answers that don't**. Only explicit server-owned context and refusal text may appear without citations.

Claude gets nine tools: coin lookup, funding trail, sibling creators, shared early buyers, shared socials, rings, shortest connection, top operators, and search. Each tool is a fixed, read-only Cypher query. The model picks which ones to call over at most **eight model/tool rounds**, and writes the answer. One round may contain several tool calls. It never writes Cypher itself.

Every tool result carries **evidence ids**: E1, E2, and so on, each naming the exact nodes and edges behind it. The answer must end each factual sentence with an ID from a compatible tool. Then a citation checker reads the answer before anyone sees it:

- An id the tools never returned is removed.
- An id from the wrong kind of tool is removed. A sentence about reused socials can't cite only the funding tool.
- Every matched topic must have compatible evidence. Funding plus socials needs citations of both kinds; one cannot bypass the other.
- A factual sentence with no valid id, including one that was uncited from the start, is **deleted**. The server adds its own computed context line afterward.

This checks citation IDs and tool compatibility. It does **not** verify that every claim is true, that a number matches a result, or that a claim names the right subject. For example, a made-up launch count can still pass with a real coin-dossier ID. Readers can inspect the linked evidence; the checker does not replace that judgment.

![The agent loop: a question goes to Claude, which calls nine read-only tools, drafts an answer with evidence ids, passes a citation check, and reaches the app; a fixed dossier is the fallback](https://raw.githubusercontent.com/avasis-ai/quant-agent/main/docs/blog/04-agent-loop.png)
*The model chooses the tools and the words. The checker enforces citation IDs and matching evidence kinds; the map lets you inspect the evidence.*

If there's no AI key, or the AI call fails, the same tools produce a fixed summary instead. That summary uses server-owned templates rather than model-written prose.

That evening we asked about a coin called **METHU**. Its creator had launched exactly one coin, which on its own looks like a first-timer. One hop back told a different story. The wallet that paid METHU's creator 0.009 SOL had paid **71 other brand-new wallets**. Each launched exactly one coin. **None of the 72 coins graduated.**

That was the moment the project made sense to us. The creator alone looks clean; the payer is the story. And you only see it when the data is shaped like the question.

We scored the agent on 30 questions, six of which it should refuse ("will this pump?", "is it safe?", addresses that aren't pump.fun coins). On the live site, all 10 questions we spent real calls on picked the right tools, cited valid evidence and stayed within the no-advice rule. What failed was length: half the answers ran past five sentences. Now they're capped at five.

## Day 3: a map that lights up the proof

A citation is only useful if you can check it. So on Day 3 we built the part people actually see: paste a coin, watch Sniff's steps stream in ("checking who made the coin and who paid them", "checking who else the same payer funded"), and read the answer next to a map of the graph.

Tap **E4** in the answer and the map dims everything except the wallets and coins that sentence stands on.

![The Sniff app on METHU: the coin card on the left shows one payer who also paid 71 other creators, none graduated; on the right the map highlights the payer and the 71 other creators for evidence E4](https://raw.githubusercontent.com/avasis-ai/quant-agent/main/docs/blog/05-methu-evidence.jpg)
*METHU, with evidence E4 selected: one payer, 71 other creators, 0 graduations. (Wallet addresses blurred for this post.)*

Exchange-like wallets show as dashed boxes, so you can see where a trail stops and why. The coin card on the left needs no AI at all. It's the same graph, read directly. It works on a phone too, and the same nine tools are served over MCP, so any agent can use Sniff:

```bash
claude mcp add --transport http sniff https://sniff.quantbase.live/mcp
```

## Day 4: memory, and a company brain

On the last day we added two more graphs beside `lineage`, in the same FalkorDB instance. Track 01 was the agent acting on connected data. These two are Tracks 02 and 03.

**Memory (Track 02).** Sniff used to forget everything the moment an answer was done. Now every investigation leaves a small trail in a graph called `memory`: a session asked a question, the question found evidence, and the evidence is about a coin or a wallet. The session is a random 32-character id, never a person, and the privacy gate checks every write.

The useful part is what happens next. Before Sniff calls a tool, it checks whether this session already made the same call, using a `call_key` index on the evidence. If it did, Sniff reuses the answer instead of hitting the big graph again. A follow-up like "and who funded that wallet?" starts from what it already knows.

Memory is also how agents work together. `memory_recall` and `memory_note` sit on the same MCP endpoint as the investigation tools. Another agent, for example the QuantBase trading agent, can ask "what has anyone found about this coin?" Sniff answers with every session's evidence about that coin, anonymised and with timestamps. That agent can then attach its own note with its name on it. The two agents never chat: they coordinate through the graph, and every note says who wrote it. The `/memory` page draws that trail for any coin or session.

**Company brain (Track 03).** The loaded `brain` is a **source-only corpus of 12 public documents**, with zero AI requests and zero extracted entity-to-entity relationships. Public repository docs and quantbase.live pages become sections with literal anchors for products, features, policies, decisions, findings and metrics. The live graph connects them through **`MENTIONS` and `PART_OF`**. This is source retrieval, not a demonstrated semantic decision graph.

The optional AI builder uses the existing cheap-model client with explicit request, token and cost caps. It can add `SUPPORTS`, `CONTRADICTS` and `DECIDED_ON` edges only when names and supporting quotes occur in the source. Those richer edges are a builder capability; they are **not shown in the loaded live corpus**.

Ask "how does QuantBase handle paper vs live?" on `/brain`, or through `brain_ask`, and it runs graph retrieval alongside FalkorDB full-text retrieval:

- it finds literal entity anchors matching the question;
- the query permits up to two typed entity hops when extracted relationships exist; the current source-only corpus has none;
- it retrieves the exact sections mentioning those entities;
- full-text search runs on every question alongside the graph query, and both result sets are ranked together.

Answers quote source excerpts with **[B#]** citations. Each excerpt must occur in its own cited section; this verifies attribution, not whether the public source is true. The expanded section preserves the original source text. Repository links point at published `main`; reloading the reviewed corpus retires old documents and sections, including records under the previous branch URLs.

The privacy gate runs before loading. It checks for emails, API keys, AWS ids, private keys, seed phrases and wallet key arrays, and never prints matched values. A privacy match in a local/repository source fails the build. A web source with a match is refused in full; other accepted sources can still be loaded. The build fails if a required web source is missing or refused.

![Two small graphs: on the left, Session ASKED Question FOUND Evidence ABOUT Coin or Wallet, with a Note from another agent; on the right, Doc, Section, Decision and Finding linked by PART_OF, MENTIONS and SUPPORTS](https://raw.githubusercontent.com/avasis-ai/quant-agent/main/docs/blog/06-memory-brain.png)
*Day 4 architecture: the live brain uses MENTIONS/PART_OF; SUPPORTS in this illustration is an optional AI-builder capability. Agent notes are attributed observations, labelled "agent note · not verified".*

## The twist: it explains, it doesn't predict

We also run trading research on this same data, so we had to ask the uncomfortable question: **do these graph signals predict which coins do well after graduating?**

We built the features only from what was known at the moment each coin graduated: how many other creators the payer funded, two-hop funding, reused socials, shared early buyers. We tested them on 23,408 graduated coins, training on the older ones and testing on the newest third.

On their own, the signals mean something. Coins whose social account had already been used on another creator's coin were **18 points less likely** to still be alive an hour later.

But once you add what anyone can already see in a coin's first couple of minutes of trading, the graph adds **nothing measurable**. The change in predictive accuracy was within ±0.01. Whatever the graph knows has already shown up in the price.

![A small dog carrying a lantern on a mountain path at dusk; the light shows the footprints and coins behind it clearly while the path ahead disappears into fog](https://raw.githubusercontent.com/avasis-ai/quant-agent/main/docs/blog/07-lantern.jpg)
*Sniff can light up where a coin came from. It can't see through the fog ahead, and it doesn't pretend to.*

We could have hidden that result. It would have been easy to ship a "risk score" and let people believe it. But this is a product people use next to their own money, and a confident wrong answer about money does real harm.

So Sniff never says "safe" or "scam", and it never says buy or sell. It tells you who is behind a coin and what their other coins did, with receipts, and every answer ends the same way: *history, not a prediction.* We think that's the honest version of this product, and the useful one. Knowing that a payer funded 72 launches and none of them graduated won't tell you the future. It does tell you what you're looking at.

## The bigger product: Sniff inside QuantBase

Sniff started as a hackathon entry. By the end of the week it had become the agent inside **QuantBase** ([quantbase.live](https://quantbase.live)), where people describe a strategy in plain words, Sniff turns it into a rule, and they test it on real history before anything else.

The first thing you meet there is **paper mode**. We describe it as *incognito, for money*: a chat with play money where you can try anything, and nothing in it can touch a wallet. Every paper result is labelled paper.

![The quantbase.live paper mode section: "Paper mode is incognito, for money," beside a painting of a dog on a jetty watching paper boats carry glowing coins](https://raw.githubusercontent.com/avasis-ai/quant-agent/main/docs/blog/09-paper-mode.jpg)
*Paper first. Try the idea with play money, see it lose or win on paper, then decide.*

The second thing is **the race**. When a coin graduates, a person has to notice it, open it, check it and tap. We show that as a typical, illustrative minute: about 55 seconds. Then we run Sniff on the same clock using numbers we measured on our own systems: **about 1 second** to hear a graduation on chain (across 1,371 graduations), and a **76 ms median** to sign and send an order (across 92 sends). About 1.08 seconds in all.

![The quantbase.live race: "A coin graduates. Watch the clock." A price curve over 60 seconds, with a person's steps marked first](https://raw.githubusercontent.com/avasis-ai/quant-agent/main/docs/blog/08-race.jpg)
*The race on quantbase.live. The person's timeline is an illustration; Sniff's times are measured.*

Speed only helps a good rule. It can't fix a bad one, and most meme coins still lose, so the site says that too.

And the graph is a core feature, not a side project. Step two of "how Sniff decides" on quantbase.live is *checks who made it*: the creator's past coins, their wallet, who funded them. That is exactly the question this graph was built to answer.

## What FalkorDB made possible

We used FalkorDB 6.0.2, and these were the parts that mattered:

- **The bulk loader** (`falkordb-bulk-insert`). 1.09 million nodes and 1.5 million edges in 30 seconds made it cheap to rebuild the graph whenever we changed a rule, and we changed rules a lot on Day 1.
- **Range indexes** on coin, wallet, hub, handle and ring keys, plus a **full-text index** on coin names and symbols for search.
- **`algo.WCC`** for rings, in 2.9 seconds over the whole graph.
- **`algo.SPpaths`** for "how are these two connected?", with hubs and platform-sized handles filtered out.
- **Read-only queries** (`GRAPH.RO_QUERY`) with per-query timeouts, so a curious agent can't write to the graph or run forever.
- **MCP**, so the same tools work from Claude, from our own agent, or from yours.

A few things in the docs didn't match the running server. Here's what we hit, so you don't have to:

- **Procedure names** differ between doc pages. On 6.0.2 they're `algo.WCC`, `algo.BFS`, `algo.pageRank`, `algo.labelPropagation`, `algo.SPpaths`. `CALL dbms.procedures()` is the source of truth.
- **Full-text index:** the documented `db.idx.fulltext.createNodeIndex('Coin','name','symbol')` is refused. `CREATE FULLTEXT INDEX FOR (c:Coin) ON (c.name, c.symbol)` works.
- **`WITH` projections** need an `AS` alias.
- **Timeouts** can't go above the server's `TIMEOUT_MAX` (15 s by default).
- **`sum()`** comes back as a float, so we cast counts to integers.
- **The bulk loader's** default escape character is a backslash, and some meme coins are literally named `\`. Pass `-x none`.

Our feedback, kindly meant: one generated reference page for procedure names per version would have saved us an hour; the full-text docs should lead with the `CREATE FULLTEXT INDEX` syntax; and the bulk loader could warn when a field is a lone escape character instead of failing mid-load. None of these slowed us down for long, and the speed of the core made up for all of it.

## From a pixel dog to a product

The day before the event began, sniff.quantbase.live was a coming-soon page with one thing on it: a small animated pixel dog, sniffing a coin, on a 3.2-second loop.

Four days later, behind that dog there is a graph of 632,339 launches, an agent whose factual sentences need citations of the matching kind, a map that highlights that evidence, and a test we ran on ourselves that told us what not to promise. And the dog has a job: it's the agent inside QuantBase.

![A small dog sitting on a cliff at sunrise, looking over a valley with a lit town, while ember sparks draw a pixel-art dog in the sky](https://raw.githubusercontent.com/avasis-ai/quant-agent/main/docs/blog/10-close.jpg)
*From a pixel dog on a coming-soon page to a product. History, not a prediction.*

## Try it

- **App:** [sniff.quantbase.live](https://sniff.quantbase.live). Try the METHU example.
- **Your own agent:** `claude mcp add --transport http sniff https://sniff.quantbase.live/mcp`
- **QuantBase:** [quantbase.live](https://quantbase.live)
- **Code:** [github.com/avasis-ai/quant-agent](https://github.com/avasis-ai/quant-agent)

Built in four days by team QuantBase, on FalkorDB, Claude and a lot of pump.fun history. Nothing here is financial advice.
