# Submission checklist (for Abhay)

Deadline: **Oct 18, 2026, 23:59 IST**. Our own target: submitted by **18:00 IST**.

## Pre-filled form fields

| Field | Value |
|---|---|
| Project name | Sniff |
| Team | QuantBase (code F92P7R) |
| Tracks | 01: Agents That Act on Connected Data; 02: Agent Memory and Coordination; 03: Company Brain |
| Repository | https://github.com/avasis-ai/quant-agent |
| Live demo | https://sniff.quantbase.live |
| MCP endpoint | https://sniff.quantbase.live/mcp |
| Video | https://youtu.be/YMQKpynEsI0 |
| Blog post | https://dev.to/quantbase/who-is-behind-this-meme-coin-building-sniff-on-a-graph-4nnc |

**Updated short description (≤ 300 characters):**

> Sniff investigates meme-coin operators through FalkorDB lineage, remembers findings across agent sessions,
> and answers QuantBase product and policy questions from a public company graph. Every answer links to its
> graph evidence or source section. History, not a prediction.

Tracks 02 and 03 are implemented on `final/tracks` and verified locally. Before updating the submitted
entry, the leader must integrate/deploy the branch and load both new graphs using
[the exact commands in GRAPH.md](GRAPH.md#leader-only-demo-box-commands-not-run-by-this-task).
The included public corpus is explicitly source-only; the builder supports capped Haiku extraction
through the configured owner key. No deploy or form update was performed by the tracks implementation.

**Tech used:** FalkorDB 6.0.2 (bulk loader, range and full-text indexes, `algo.WCC`, `algo.SPpaths`,
read-only queries with timeouts), Claude Sonnet 5.5 with tool use, MCP (streamable HTTP), Python, FastAPI,
Cytoscape.js, DuckDB (data prep and test ground truth), AWS EC2 and Caddy.

## Steps only you can do

1. **Make the repo public:** GitHub → avasis-ai/quant-agent → Settings → Danger Zone → Change visibility →
   Public.
   - **Secret scan, 2026-10-17:** gitleaks 8.28.0 over the full git history (10 commits) found no leaks. A
     manual grep for `sk-ant`, private keys, `ws_` secrets, scrypt hashes and password assignments found only
     test fakes (`sk-ant-api03-xxxx…`) and the hash *format* string.
   - **Not in git:** the admin passcode, `.falkordb.pw`, `*.env`, `*.key` and `data/` are all gitignored.
   - **Public on purpose:** the demo box's public IP appears in `deploy/deploy.sh`. It's already public through
     DNS, and SSH is closed except during a deploy.
   - **Re-run before flipping**, in case anything was committed since: `~/.cache/gl/gitleaks git ~/dev/quant-agent --no-banner --redact`
2. **Fill in and submit the form** with the fields above, plus the video link.
3. **Publish the blog** (side prize). Post `docs/BLOG.md` on Hashnode, dev.to or Medium, then add the link to
   the form if it asks for one.
4. **After judging:** tear down the demo box. The steps are in the hackathon notes: terminate
   i-0ec741d963da4a248, release the Elastic IP, delete the security group, and delete the `sniff` and
   `lineage` DNS records.

## Check before submitting

- [x] https://sniff.quantbase.live loads, and the METHU example answers.
- [ ] `/settings` shows the site key as Active.
- [ ] `claude mcp add --transport http sniff https://sniff.quantbase.live/mcp` lists 12 tools after the tracks deploy.
- [ ] `/memory` recalls a real METHU investigation and a second agent can add an attributed note over MCP.
- [ ] `/brain` answers the paper/live question with `[B#]` source sections and a knowledge graph.
- [ ] The README renders on GitHub, including the screenshots and mermaid diagrams.
- [x] The video link works when you're logged out.

**Submitted 2026-10-17 13:48 IST, video link updated 13:57 IST.**
