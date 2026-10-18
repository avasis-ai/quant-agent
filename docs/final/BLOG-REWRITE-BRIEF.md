# Brief: make the blog simple, human and gripping (Codex). HARD DEADLINE: committed by 22:30 IST, 18 Oct

Rewrite docs/BLOG-FINAL.md (our Graph Hacks best-blog entry, team QuantBase) so ANYONE can follow it, including a database
engineer who has never bought a meme coin, and enjoy reading it. Abhay: "write it like you are speaking to a human, not an AI bot."
The readers and judges are FalkorDB / graph-database developers.

## Voice
- A builder telling a friend what happened: short sentences, concrete moments, "we", a little humour where it's natural.
- No buzzwords ("leverage", "seamless", "robust", "powerful", "unlock", "delve", "in today's world"), no listy marketing tone, no
  em-dash chains, no rhetorical-question spam.
- Explain every crypto term the first time, in one plain clause:
  - meme coin: a joke token anyone can launch in a minute;
  - pump.fun: the site where most of them launch;
  - wallet: an account address;
  - funding a wallet: sending it the few cents it needs to launch;
  - "graduated": raised enough to move to a real trading pool, a rare outcome.
  Use the fraud/sybil-ring framing: to a graph, this is a fraud-ring problem.

## Keep (true facts only; check them against the current text, docs/GRAPH.md, docs/EVAL.md, README.md)
- The METHU opening (one creator; the funder paid 71 other creators; 72 coins, none graduated in our snapshot, which ends 14 Oct 2026
  18:45 UTC).
- The supernode/hub mistake and fix (33,747 wallets).
- The 30-second bulk load and the numbers (632,339 coins, 424,007 wallets, ~1.5M links).
- Evidence ids and the server rejecting uncited sentences ("checks sourcing, not truth").
- The map.
- Day 4 memory + company brain, exactly as currently worded on claims (self-declared agent names, notes unverified, source-only brain,
  no extracted entity relationships).
- The prediction twist (in this test the graph added no measurable predictive value once the first minutes of trading were
  included).
- The FalkorDB section (likes + honest doc feedback, the part DB people value most).
- "Where this goes next", "From a pixel dog to a product", "Try it".
- All the image lines and captions (same URLs). The front matter stays, and the title stays "METHU had one creator. Its funder
  had paid 71 more."

## Shape
- 1,800–2,400 words.
- Headings that read like a story. Each section opens with a moment, not a summary.
- Move or trim anything that slows the story.
- No profit claims, nothing new that isn't true, no "Quant Agent".

## Then
1. Regenerate app/static/blog.html with `.venv/bin/python -m build.blog`.
2. Run the tests (`.venv/bin/python -m pytest -q`) and commit (author avasis-ai <abhay@avasis.ai>).
3. Write docs/final/BLOG-REWRITE-RESULT.md listing every factual claim and its source.
No deploy, no push.

## UPDATE from Abhay (21:40 IST), overrides the above
- The title is now: "Who's really behind a meme coin? We built a graph agent to find out" (set it in the front matter).
- DON'T open cold on METHU; it feels random. Open with a relatable human scene/question anyone gets (a new coin appears, everyone
  piles in, nobody knows who made it, and the clues are a few hops away). Introduce METHU later, as the worked example of what Sniff
  found (around Day 2/3 or right after the problem section).
