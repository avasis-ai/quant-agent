# Asset provenance

All interface code, the landing graph illustration and the evidence renderer
were written for this brief. The existing FastAPI, graph tools and API contracts
remain the application foundation. No interface code was copied from the
reference applications.

| Asset | Source | License / treatment |
| --- | --- | --- |
| Host Grotesk variable WOFF2 | User-provided `sniff-app-astra/public/fonts` | OFL; license shipped beside font |
| Geist Mono variable WOFF2 | User-provided `sniff-app-astra/public/fonts` | OFL; license shipped beside font |
| Instrument Serif italic TTF | Google Fonts, `fonts.gstatic.com/s/instrumentserif/v5/jizHRFtNs2ka5fXjeivQ4LroWlx-6zATiw.ttf` | OFL from `google/fonts/ofl/instrumentserif`; license shipped beside font |
| QuantBase marks and favicon | User-provided `sniff-app-prod/public/media/brand` | Existing QuantBase identity |
| Cytoscape.js 3.33.1 | cdnjs, same pinned version and SHA-512 as the previous UI | MIT; license shipped in `app/static/vendor` |
| Landing graph | Fresh inline SVG in `app/static/home.html` | Central addresses and aggregate counts from the recorded METHU dossier; peripheral branches explicitly labelled a schematic |
| Snapshot metrics | README, `docs/GRAPH.md`, local graph import | Maintained in `app/static/snapshot.json` |
| Eval table | `docs/EVAL.md` | Both recorded runs, all columns, and the length caveat retained |
| Screenshots | Playwright against the local application and full graph snapshot | Streaming captures delay the recorded local SSE events; settings lifecycle checks use browser fixtures |

Fonts, CSS, JavaScript, marks and the graph library are self-hosted. The website
does not require a font CDN or JavaScript CDN to render. QuantBase, GitHub, video
and blog links remain external destinations.
