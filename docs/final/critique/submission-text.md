# Title
Sniff: who's behind a meme coin

# Description (as submitted)
Thousands of meme coins launch on pump.fun every day, and a buyer can't see who is behind one: whether the creator has launched and abandoned dozens of coins before, or whether one wallet quietly funded a whole farm of creators. The answer is always two or three hops away, so it is a graph problem.

Sniff is a research agent with FalkorDB as its whole context layer, built across all three tracks:

• Acts on connected data (Track 01): the agent chooses among graph tools over MCP (multi-hop funding trails, algo.WCC funding rings, algo.SPpaths for "how are these two connected?") on 632k coins and 424k wallets. Every sentence must cite graph evidence of the matching kind, or the server rejects the answer, and the map lights up the path behind it.

• Memory and coordination (Track 02): a persistent memory graph (Session → Question → Evidence → Coin/Wallet) lets follow-ups reuse earlier findings across sessions with their original provenance, and other agents share state through memory_recall and memory_note, leaving signed, timestamped notes on the same coin.

• Company brain (Track 03): QuantBase's public docs become Doc → Section → Product/Feature/Policy/Decision nodes. brain_ask answers with [B#] sources traced to the exact section, and re-ingesting a changed source retires its stale sections.

All 12 tools sit on one MCP endpoint. Sniff shows history, not predictions or advice, and it is becoming the research agent inside QuantBase (quantbase.live), our meme-trading product.

# "How did you use FalkorDB" and feedback answers: see the live form text in ../SUBMISSION.md, or the same content in the brief.
