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
