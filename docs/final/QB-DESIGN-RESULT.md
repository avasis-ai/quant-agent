# QuantBase design alignment

Working checkpoint, 18 October 2026, 22:01 IST. No deployment or push.

Implemented the dashboard's Ember frame, labelled icon rail, wordmark, segmented
workspace pills, opaque panels, welcome and composer on `/app`, `/memory`,
`/brain` and `/settings`. Shared tokens, font faces and components live in
`app/static/quantbase.css`. Dashboard fonts and logo are reused directly; OFL
licenses remain local.

The landing now tells the submitted story, with the generated local WebP art,
mobile crops, a coin → creator → funder → ring SVG flow that stops at hubs,
a pause control, reduced-motion handling and a keyboard-accessible demo
lightbox. The production section and hero badge link to QuantBase and clearly
say paper trading is live while wallet trading is opening soon. The existing
three-track section, snapshot, MCP command and evaluation remain available.
Blog uses the website's floating header and reading layout. The waitlist
fallback still redirects to home.

Validation so far: the full Python suite passes **111 tests** against the local
FalkorDB, including three new anonymous shared-key integration checks. Initial
AA scans passed on all six pages at both 1440 and 390px, with no document-level
horizontal overflow. The real public settings endpoint reports the existing
site key active; no key was retrieved, changed or exposed. The server already
selects it for anonymous investigations; new mocked tests exercise Claude tool
calls, citations and the existing hourly/daily caps.

Two-pass browser screenshots and final comparison notes are being completed in
`docs/final/shots-qb/` using `qa-qb-design.mjs`. Final results follow in the next
checkpoint.
