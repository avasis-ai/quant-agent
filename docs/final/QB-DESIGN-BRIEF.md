# Brief: sniff.quantbase.live must look like QuantBase (Codex). HARD STOP: committed by 23:15 IST, 18 Oct (event code freeze 23:59)

Abhay: "for sniff.quantbase.live use the same design system as the main website and dashboard, what you have built looks so slop".
Make every page of this app (/, /app, /memory, /brain, /blog, /settings, waitlist fallback) look like it belongs to QuantBase.

## Source of truth (copy the system, don't reinvent it)
- **Dashboard (primary):** ~/dev/sniff-app-prod.
  - DESIGN-V6.md and src/styles.css: the tokens, type scale, radii, glass, frame, components.
  - The look: docs/astra/final/*.png (e.g. 1440-chat.png: a warm ember frame, a left rail, a centred welcome, white pill
    actions, the Paper/Research/Live pill style, the credits pill, the composer).
  - Fonts: src/fonts or the CSS @font-face. Self-host the same files here (copy them into app/static/fonts), OFL only.
- **Website:** https://quantbase.live (source ~/dev/quant-release/site: static/ CSS + landing_sniff.py). Use its header/footer
  pattern, the hero type, section rhythm and the ember background.
- Port the exact colour tokens, fonts (Host Grotesk, Geist Mono, Instrument Serif accent), spacing, radii, borders, shadows,
  buttons, inputs, pills, cards and motion into one shared app/static CSS file, and apply it everywhere.

## Layout direction
- /app, /memory, /brain: the DASHBOARD shell (a frosted ember frame, a left icon rail with Investigate / Memory / Brain / Blog /
  Settings, a top bar with the QuantBase wordmark "quantbase.live | Sniff" like the dashboard's "quantbase.live | Ask Sniff",
  status pill), with content in dashboard-style panels. The graph canvases get the dashboard's panel treatment and calm density.
- /: the WEBSITE look (quantbase.live hero/sections/footer), keeping the current content and the "three tracks" section.
- /blog: the website's reading layout.
- Use the QuantBase logo/wordmark from the website/dashboard (copy the SVG), not a separate "sniff" logo treatment.
  "Sniff by QuantBase" is fine as the product label.

## Rules
- Behaviour, routes, API calls, citations/evidence UI, accessibility and every test stay the same.
- Run `.venv/bin/python -m pytest -q` (all green).
- No new runtime dependencies; no external font CDNs.
- 390 px with no horizontal scroll. AA contrast. Reduced motion respected.
- Take Playwright screenshots of every page at 1440 and 390 into docs/final/shots-qb/, compare them side by side with
  sniff-app-prod docs/astra/final/1440-chat.png and quantbase.live, and fix the differences. Two passes.
- Commit (author avasis-ai <abhay@avasis.ai>) and write docs/final/QB-DESIGN-RESULT.md. No deploy, no push.
- If time runs short, prioritise /app, then /, then /memory and /brain, then the rest, and COMMIT working states as you go
  (every 20 min) so something good exists at 23:15.

## UPDATE from Abhay (21:50 IST): the landing (/) is a SHOWCASE that tells the story we submitted
- Rebuild / as a neat, beautiful storytelling page in the quantbase.live website style, following the blog's arc ("Who's really
  behind a meme coin? We built a graph agent to find out"):
  1. hero (the question, an ask box into /app, the video https://youtu.be/fz89p-YZS6o as a play button/lightbox);
  2. a new coin, an unfamiliar creator;
  3. follow the payment (METHU: one funder, 71 other creators, 72 coins, none graduated in our snapshot);
  4. the hub lesson (exchange-like wallets became dead ends);
  5. every sentence must cite evidence (checks sourcing, not truth);
  6. memory shared between agents;
  7. the company brain;
  8. the honest twist (it explains, it doesn't predict);
  9. three tracks, one product (QuantBase);
  10. try it / links.
  Short plain copy, big visuals, scroll reveals (respect reduced motion).
- Images: a second worker is generating them into app/static/img/story/ (01-new-coin, 02-trail, 03-ring, 04-hub, 05-memory,
  06-brain .webp, plus -m.webp mobile crops for 01–03), ready ~22:40 IST. Use them with width/height set and lazy loading. Build the
  page so it still looks good if one is missing (a gradient placeholder), and wire the real files in when they appear.
- Commit and push the page into the tests' snapshot (if any) only if the tests need it.

## UPDATE 2 from Abhay (21:52 IST), the HERO and the live demo (highest priority after the shell)
- **Hero animation:** a beautiful animated graph flow. A coin node lights up, a trail travels to its creator, then to the funder, then
  fans out to the ring of other creators/coins, and a hub stops the trail.
  - Use SVG + CSS/JS (the existing Motion library if bundled, else vanilla rAF), smooth easing, looping calmly.
  - Respect reduced motion.
  - Pair it with custom crafted SVG icons in the dashboard's line style (coin, wallet/creator, funder, hub, evidence, memory,
    brain), used in the hero legend and the story sections.
- **Background:** a beautiful image behind the hero: app/static/img/story/00-hero-bg.webp (being generated now, ~22:30). Darken it
  with an ember gradient so the text stays AA. Fall back to the gradient if it's missing.
- **Headline:** replace "Sniff any coin before you buy" (Abhay: sounds a bit bad). Make it subtle and about what the product does
  (investigate). Pick the best of e.g.:
  - "Investigate who's behind any meme coin."
  - "Trace a coin back to the wallets behind it."
  - "Follow the money behind a meme coin."
  The sub-line explains the graph agent in one plain sentence. The hero visual must match the headline (the animation literally
  traces coin → creator → funder → ring).
- **The live demo must WORK with the real site key:**
  - Visitors get the real AI-written investigation on /app without adding their own key.
  - Use the server's existing site-key path, its caps/rate limits and no key exposure (check app/ai.py / settings / the "site key
    Active" status). If it's already wired, make sure the UI defaults to it and doesn't show "Add a Claude key" when the site key is
    active.
  - Test end to end locally with fixtures/mocks; never print or commit a key.
- **A clear section (and a hero badge):** "The full production version of this agent is live in QuantBase", linking
  https://quantbase.live and https://app.quantbase.live. Honest copy to use:
  > "QuantBase began as a research platform for manual algorithmic trading. We've rebuilt it around Sniff as an autonomous meme-coin
  > trading platform: Sniff researches, tests and runs your rules inside the limits you set. Paper trading is live today; live
  > trading on your own wallet is opening soon."
  Do NOT claim users can trade live today, and no profit claims.
