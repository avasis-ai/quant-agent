# Landing polish

Completed 18 October 2026. Working checkpoint committed at 23:27 IST, before the 23:30 checkpoint and 23:40 hard stop. No deployment or push.

- Preserved QuantBase v6's Host Grotesk, Instrument Serif italic, Geist Mono and ember palette. Refined heading sizes, tracking, balanced wrapping and section rhythm; landing prose is 18px desktop and 17px mobile at 1.6 line height. Kept “meme coin” together in the hero.
- Replaced the METHU diagram's three-phase interval with a scroll-triggered requestAnimationFrame sequence: coin pulse, eased traces to creator and funder, staggered ring branches, sparks, arrival labels, and a terminating hub branch. The hub is explicitly schematic in the accessible description. The sequence holds after 9.3 seconds, with pause, inspection controls and Replay.
- Preserved the existing SVG canvas and icons. Animation stops outside the viewport or in a hidden tab. Reduced motion shows the complete static graph; the graph also remains visible without JavaScript. Reserved the Replay button's width to avoid layout movement.

Validation:

- `.venv/bin/python -m pytest -q`: 116 passed, 10 skipped.
- `qa-polish.mjs`: 1440/390 layout, no horizontal overflow, scroll trigger, pause/resume, hold, Replay, dynamic reduced motion, no-JavaScript graph and no browser errors.
- Existing `qa-qb-motion.mjs`: hero pause/resume, reduced-motion switching, missing-image fallback and no-JavaScript links pass at both widths.
- axe WCAG 2 A/AA and 2.1 AA checks: zero violations at both widths.
- `qa-polish-performance.mjs`: 565 sampled frames per viewport, median 16.7ms, p95 at most 16.8ms, no intervals above 34ms and zero layout shift while the diagram runs. These are local headless Chromium measurements, not physical-device guarantees.
- Visual review: hero and complete/tracing diagram at both widths. Moved the creator label clear of the lower ring branch.

Screenshots are in [shots-polish](shots-polish/). Machine-readable results are in [polish-results.json](polish-results.json) and [polish-performance.json](polish-performance.json). Run the local QA scripts with `PLAYWRIGHT_MODULE` set to an installed Playwright module if it is not on the default module path; the default local app URL is `http://127.0.0.1:8098`.
