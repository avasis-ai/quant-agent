# Brief: landing polish (Codex). HARD STOP: committed by 23:40 IST, 18 Oct (event code freeze 23:59). Small, safe changes only.

Abhay: (1) "typography can be better", (2) "the 'A coin is never just a coin.' animation can also be better" on the landing (/).

1. **Typography** (app/static/quantbase.css + home.html only):
   - Refine the type scale and rhythm to the QuantBase dashboard/site standard (~/dev/sniff-app-prod/DESIGN-V6.md, src/styles.css):
     - display headings tighter (letter-spacing ~ -0.03em, line-height ~1.02–1.08), with a deliberate Instrument Serif italic
       accent;
     - section headings with a consistent size step;
     - body at 17–18px, line-height ~1.6, measure 60–68ch, muted secondary colour at AA contrast;
     - mono labels small, uppercase, tracked.
   - Consistent vertical spacing between sections; balanced headline wrapping (text-wrap: balance); no orphans in the hero.
   - Check 1440 and 390.
2. **"A coin is never just a coin." animation:** make it beautiful and meaningful:
   - a smooth, staged reveal as it scrolls into view: the coin node pulses, then a light travels along the edge to the creator, then
     the funder, then fans out to the ring's nodes one by one, while the hub lights up as a dead end (the trail visibly stops at it).
   - Use ember glows, eased timing (no linear), subtle particle sparks along the active edge, labels fading in when each node is
     reached, and a calm loop or a hold at the end.
   - Use the existing SVG + Motion/rAF approach and the existing icons. Respect prefers-reduced-motion (a static final state).
     60fps, no layout shift.
3. Run `.venv/bin/python -m pytest -q` (green), take a Playwright check at 1440/390 (screenshots in docs/final/shots-polish/),
   commit (author avasis-ai <abhay@avasis.ai>). No deploy/push.
- Check `TZ=Asia/Kolkata date` often; commit a working state by 23:30, and finish by 23:40 no matter what.
