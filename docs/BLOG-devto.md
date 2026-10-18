*By team QuantBase, for WeMakeDevs × FalkorDB Graph Hacks, October 2026*

More than ten thousand meme coins launch on pump.fun every day. Almost all of them die within hours. When a new one shows up on your screen, the question people actually ask isn't "will it go up?", because nobody can answer that honestly. It's simpler: **who made this, and what happened to the last things they made?**

That question is hard to answer by hand. The wallet that launched the coin is usually brand new. The real trail runs through whoever paid that wallet to launch it, and through whoever else that payer has paid. That takes two or three hops of "who sent money to whom", across hundreds of thousands of wallets.

So we built **Sniff**: paste a coin, and an AI agent walks a graph of on-chain history and answers in a few plain sentences. Every sentence links to the exact part of the graph that proves it.

Try it: https://sniff.quantbase.live

{% embed https://youtu.be/fz89p-YZS6o %}

![Sniff's answer, with each claim's evidence highlighted on the map](https://raw.githubusercontent.com/avasis-ai/quant-agent/main/docs/shots/04-evidence-highlight.jpg)

## Why a graph

We already had the raw material. Our QuantBase collector records public pump.fun data: launches, the wallet behind each one, who funded those wallets, the wallets that bought in the first seconds, and the social links each coin lists. Before the event it lived in Postgres tables, and every question we asked of it turned into a tower of self-joins.

The questions are all shaped like paths:

- Who paid the creator? → Who else did that wallet pay? → What did *they* launch? → Did any of it graduate?
- Do these two coins share a funder, an early buyer, or a Twitter account?
- Which wallets form one connected group of launchers?

In FalkorDB each of these is a single Cypher pattern. We loaded 632,339 pump.fun launches, 424,007 wallets and about 1.5 million relationships (CREATED, FUNDED, SNIPED, LINKS) with the bulk loader in **30 seconds**. The questions that had been painful became one-liners. Rings of connected launchers come from `algo.WCC`, and "how are these two connected?" comes from `algo.SPpaths`.

## Surprise 1: hubs make everything link to everything

The first version of the graph said every coin was connected to every other coin within four hops, which is true and useless. The reason was exchanges. When a creator withdraws SOL from an exchange, the exchange's hot wallet shows up as their "funder", and that one wallet funds tens of thousands of creators.

We call these wallets **hubs**: any wallet that funded more than 200 others. There were 89 of them. They get their own label, keep a note of how many wallets they funded, and **no query is allowed to walk through them**. A funding trail that reaches a hub stops there and says "this came from an exchange-like wallet, which tells us nothing about who is behind it."

We tried to be cleverer and tell exchanges apart from big launch farms by what share of their wallets went on to create coins. It didn't work, because our funding data only covers wallets that created coins. The biggest hub funded 33,747 wallets and 80% of them were creators, simply because those were the only wallets we had looked up. So we kept the simple rule, wrote down why, and moved on.

## Surprise 2: the docs and the database disagreed

FalkorDB 6.0.2 was a pleasure to work with, but a few things in the docs didn't match the running server. Here's what we hit, so you don't have to:

- **Procedure names:** they differ between pages. On 6.0.2 they are `algo.WCC`, `algo.BFS`, `algo.pageRank`,
`algo.labelPropagation` and `algo.SPpaths`. `CALL dbms.procedures()` is the source of truth; check it first.
- **Full-text index:** the three-argument `db.idx.fulltext.createNodeIndex('Coin','name','symbol')` from the
docs is refused. `CREATE FULLTEXT INDEX FOR (c:Coin) ON (c.name, c.symbol)` works.
- **`WITH`:** projections need an `AS` alias.
- **Timeouts:** a query timeout can't go above the server's `TIMEOUT_MAX` (15 s by default).
- **Bulk loader:** its default escape character is a backslash, and meme coins are sometimes literally named
`\`. Pass `-x none` and let your CSV writer double quotes instead.

None of these took long once we knew, and they're all written down in the repo.

## Surprise 3: one payer, 72 creators, zero graduations

The first time the whole thing ran end to end, we asked about a coin called METHU. Its creator wallet had launched exactly one coin, which on its own looks like a first-time creator. One hop back told a different story.

The wallet that paid METHU's creator, 0.009 SOL, had paid **71 other brand-new wallets**. Each launched exactly one coin. **None of the 72 coins graduated.** In the graph it's one funder with 72 spokes, each ending in a dead coin.

That's the whole idea of Sniff in one picture. The creator alone looks clean; the payer is the story. And you can only see it if the data is shaped like the question.

## An agent whose citations are checked

The agent is Claude with nine tools, each a fixed, read-only Cypher query: coin lookup, funding trail, sibling creators, shared early buyers, shared socials, rings, shortest connection, top operators, and search. Claude decides which tools to call, up to eight, and writes the answer. It never writes Cypher itself.

Every tool result carries **evidence ids**: E1, E2 and so on. The answer has to end each sentence with the id that proves it. Then we check:

- A cited id has to be one a tool really returned.
- It has to come from a tool that can show that kind of claim. A sentence about reused socials can't cite
the funding tool.
- A sentence left with no valid citation is deleted. A shorter answer beats an unsupported one.

In the app, tapping a citation lights up exactly those wallets and coins on the map. If there's no AI key, or the AI call fails, the same tools produce a fixed summary instead, so the facts never depend on the model.

We scored it on 30 questions, including six it should refuse ("will this pump?", "is it safe?", made-up addresses). On the live site all 10 questions we spent real calls on picked the right tools, cited valid evidence and stayed within the no-advice rule. What failed was length: half the answers ran past five sentences, so answers are now capped at five.

## The honest part: it explains, it doesn't predict

We also run trading research on the same data, so we asked the uncomfortable question: do these graph signals help predict which coins do well after graduating?

We built the features strictly as they would have been known at the moment each coin graduated: how many other creators the funder paid, two-hop funding, reused socials, shared early buyers. Then we tested them on 23,408 graduated coins, training on the older ones and testing on the newest third.

On their own, the signals mean something. Coins whose social account had been used on another creator's coin were 18 points less likely to still be alive an hour later. But once you add what anyone can already see in a coin's first couple of minutes of trading, the graph adds **nothing measurable**: the change in predictive accuracy was within ±0.01. Whatever the graph knows has already shown up in the price.

So Sniff doesn't say "safe" or "scam", and it never says buy or sell. It tells you who is behind a coin and what their other coins did, with receipts, and ends every answer with the same line: *history, not a prediction.* We think that's the honest version of this product, and the useful one.

## Try it

- **App:** https://sniff.quantbase.live (try the METHU example).
- **Your own agent:** `claude mcp add --transport http sniff https://sniff.quantbase.live/mcp`
- **Code:** https://github.com/avasis-ai/quant-agent

Built in four days on FalkorDB, Claude and a lot of pump.fun history.
