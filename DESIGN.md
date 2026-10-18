# Sniff · QuantBase Ember

Sniff is a graph investigation product for pump.fun and the QuantBase Graph Hacks
submission. It shares the established QuantBase design system, rather than a
separate Sniff identity. Recorded history and evidence remain distinct from
predictions, agent notes and illustrated explanations.

Design dials: variance 5, motion 3, density 4. The source brand fixes the
palette and frame; motion explains graph traversal, and the application keeps
room for evidence. The redesign retires the separate large Sniff wordmark and
unframed workbench while preserving navigation, forms and evidence controls.

## Source of truth

The shared implementation is `app/static/quantbase.css`, loaded last on every
page. Its named tokens, local font faces, frame, rail, buttons, inputs, pills,
opaque panels and motion come from `~/dev/sniff-app-prod/DESIGN-V6.md` and
`src/styles.css`. The visual shell follows `docs/astra/final/1440-chat.png`.
Website chrome, hero type and section rhythm follow
`~/dev/quant-release/site/static/ember.css` and the main QuantBase website.
Existing `tokens.css` names remain as compatibility defaults for the older
page sheets; the shared QuantBase sheet maps them onto the canonical tokens.

Ground #161316, cocoa #453027, reading surface #191719, raised #211E20,
secondary raised #292527 and #332D2E, input well #171416. Text #FAF8F6,
#E2DDDA, #BDB5B1 and #ABA29D. Ember #FF6D29; readable ember #FFAA80;
control edge #81756F; focus #FFAE85. White actions use #FAF8F6 on #211A17.
Positive #91C9A5, negative #F28C84 and warning #E8C17C retain semantic uses.

Host Grotesk supplies text, navigation and display. Geist Mono supplies
addresses, compact labels and data. Instrument Serif italic is the website's
limited display accent. All fonts are self-hosted, with OFL licenses beside
them. Host Grotesk and Geist Mono are byte-identical to the dashboard assets.
The QuantBase mark and line icons are reused from that dashboard; the custom
graph glyph set extends the same 24px grid and 1.5px stroke.

## Layout and components

`/app`, `/memory`, `/brain` and `/settings` use the cocoa glass frame with a
12px desktop inset, 80px rail and 64px header. The top bar reads
`quantbase.live | Sniff` and links the three graph workspaces using the source
segmented pill treatment. Status text says “Read-only research”; it does not
invent balances, credits or connection health. The five rail destinations
have persistent labels and current-page semantics. On phones they form a
fixed bottom navigation with 44px or larger targets.

The welcome and composer use a 740px measure. Display is 48/52 desktop and
34/37 phone; workspace titles 32/38 and 28/34. Body is 14/22; supporting text
13/20. Data uses tabular figures. Cards have 14px corners; controls 10px;
composer 18px; frame 24px. Glass belongs to the frame. Graphs, findings and
source details sit on quiet, opaque reading surfaces. Existing evidence tags,
keyboard graph controls, streaming steps and citation source views retain
their contracts.

`/` is a showcase of the submitted build: investigate a coin, trace its payment,
inspect METHU's ring, learn why hubs stop traversal, inspect citations, reuse
agent memory, ask the company brain, then see the honest research limitation
and the three tracks. The existing snapshot, evaluation and MCP content stays
available. The full production agent section links QuantBase and its dashboard,
clearly distinguishing live paper trading from forthcoming wallet trading.

Website pages use a 1080px reading frame, floating pill header and generous
footer. The blog keeps its narrow 720px reading column and all eight local
figures. The unconfigured waitlist still redirects to the home page.

## Motion, media and accessibility

The hero uses a ten-second SVG trace: coin, creator, funder, ring, then a hub
that ends the trail. Pause is explicit; background tabs pause the loop.
Reduced motion shows the complete static path. Story reveals use a short
opacity/16px entrance and progressive enhancement; content is visible without
JavaScript. Reduced transparency replaces glass with opaque cocoa surfaces.

Story images are local WebP illustrations, with explicit dimensions, lazy
loading and mobile crops where supplied. Their figures keep a gradient and
simple graph fallback if an image fails. The hero background has a dark ember
overlay. Illustrations explain the narrative; they are not literal graph data.
The demo lightbox creates its YouTube player only after activation, supports
Escape and close, clears playback on close and restores trigger focus. Its
ordinary link remains usable without JavaScript.

Preserve all routes, query fields, API payloads, key selection, caps, memory
provenance and evidence validation. No runtime package, font CDN, deployment
or push is part of this redesign. Every interactive element keeps a visible
focus indicator; screen-reader labels and 390px overflow are checked alongside
AA accessibility scans.
