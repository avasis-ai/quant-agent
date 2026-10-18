# Brief: inline live demo on the landing + the "always METHU" bug (Codex). HARD STOP: committed by 23:20 IST (event code freeze 23:59)

## Bug (P0)
The hero form submits to /app?q=<text>. /app puts q into the "Your question" field while the coin field defaults to "METHU", so
ANY search investigates METHU. Repro: https://sniff.quantbase.live/app?q=Subprime%20Cat → shows the METHU dossier.
Fix:
- Use the existing search/resolve API (e.g. the coin search used by the coin field) to decide whether q is a coin (a name, ticker or
  mint) or a question. Put a coin in the coin field; for a question that names a coin, resolve it too.
- Never default to METHU when the user typed something; METHU stays only as a suggestion chip.
- If the coin isn't found: a clear "not in our snapshot (ends 14 Oct 2026)" state with suggestions.
- Add regression tests.

## Inline demo on / (Abhay: "I thought it would be inline, not like a dashboard")
- The hero ask box runs the investigation RIGHT ON THE LANDING PAGE, below the hero, without navigating:
  - stream the steps;
  - show the AI-written answer with clickable [E#] citations;
  - show a compact coin dossier strip;
  - show a compact animated graph of the evidence path, in the hero's visual language: coin → creator → funder → ring, hub as a dead
    end.
- Reuse the existing /api/ask streaming endpoint and the existing graph rendering code, with the shared owner key (no key prompts
  when the owner key is active) and the existing rate limits.
- Suggestion chips under the box run inline too: METHU, Subprime Cat, Women in Finance, Higher, plus 2 more interesting real coins
  from the graph. Pick them via the existing queries (e.g. a big ring and a graduated coin), and verify that each returns a good
  dossier.
- An "Open full investigation →" link goes to /app with the right coin + question prefilled (fixed per the bug above).
- It must look premium, matching the page (the QuantBase Ember tokens already in quantbase.css), and work at 390 px. Reduced motion
  respected.
- Keep everything else unchanged.
- Test: run pytest (green), and with Playwright against a local server, check 3 different coins inline plus the /app?q= fix.
  Screenshots go to docs/final/shots-inline/.
- Commit as you go (author avasis-ai <abhay@avasis.ai>) and write docs/final/INLINE-DEMO-RESULT.md. No deploy, no push.
- Check `TZ=Asia/Kolkata date` often. If short on time, ship the BUG FIX first (commit), then the inline demo.
