# Sniff · QuantBase Ember

Sniff is a graph investigation product for pump.fun traders and a Graph Hacks
submission for technical reviewers. The primary action is to investigate a coin.
The graph must explain the evidence, and the copy must distinguish recorded
history from predictions. This is one system across the landing, workspace and
settings pages.

## Direction

Atmospheric, precise and spacious. Marketing uses a Map / Diagram composition:
large left-aligned type alongside a real, interactive graph. The application uses
a wide workbench with the dossier above a graph and a right-hand evidence column.
Settings uses a quiet two-column reading layout. No invented financial data,
customer claims, performance charts or trading controls.

Design variance 7, motion intensity 4, visual density 3 on the landing. The
workspace prioritizes readable evidence and useful canvas space. Native HTML,
CSS and JavaScript preserve the existing FastAPI application and API contract.

## Theme

The canonical tokens live in `app/static/tokens.css` (also linked as `tokens.css`
at the repository root). Ground #161316, cocoa #453027, ember #FF6D29, supporting
text #BABABA and white. One warm light source; glass on the frame, opaque reading
surfaces under words. White pills are primary actions. Ember identifies a
selected graph path or product state; green only communicates graduation.

Host Grotesk is the display and body face, with Instrument Serif italic as a
limited brand accent and Geist Mono for addresses and technical labels. All
fonts are self-hosted with swap and their licenses. Type has generous line
height; italic descenders have clearance. Body text is 16px, app text 14–16px,
supporting text 12–14px. Do not use low-contrast ornamental text for information.

## Shape and spacing

Four-point spacing scale. Marketing content max-width 1280px, workspace max-width
1720px. Desktop insets 48–80px, phone insets 20px. Major landing sections have
96–128px separation. Panels use 20px corners, inputs 12px and actions full pills.
Controls have at least 44px targets; labels always identify inputs.

## Motion and interaction

Three primitives: a single entrance, graph evidence transitions and button press
feedback. The landing graph cycles through the recorded funder → creator → coin
path to explain the traversal; pause is available. No moving background or
scroll hijacking. Graph positions animate when evidence changes. Reduced motion
removes spatial animation and pauses automatic graph focus. Reduced transparency
uses opaque surfaces. Every control has a visible, immediate keyboard focus ring.
Copy actions confirm in place. Errors stay close to their task. Search supports
arrow keys, Enter, Escape, and screen-reader combobox semantics.

## Shared elements

All pages share the Sniff wordmark, QuantBase brand mark, typography, warm palette,
navigation, action shape, focus behavior and policy language. Snapshot figures
are maintained only in `app/static/snapshot.json`; the UI labels them as a
snapshot. The application never infers links through exchange-like hub wallets.

## References

User-provided QuantBase DESIGN-V5.md and DESIGN-V6.md, palette-v5-arounda.jpg,
palette-v5-elasti.png, Astra inspiration 1 and 3, and https://quantbase.live.
The provided brand rules take precedence over generic skill defaults.
