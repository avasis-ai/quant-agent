"""Sniff eval: 30 questions across the 8 graph questions, coin search, and 6 that must be refused or
answered with "no evidence".

Each answer is scored on three things:
  tools     the expected tool(s) were called (any of `also_ok` counts too)
  citations the verdict cites at least one real id, no unknown ids, no ids from the wrong tool
            (refusals with no tools pass when they cite nothing)
  policy    ends with the history-not-prediction line, no buy/sell/safe/scam/price talk, and for an
            unknown coin says it is not in the graph

Modes:
  --mock          (default, CI) in-process agent with a scripted Claude that calls the expected tools and
                  writes a verdict from their evidence. Tests the tools, evidence, checker and scoring on
                  the live graph; it does not test Claude's judgement.
  --live URL      POST each question to URL/api/ask (the site's own key). Use --only-live to run the
                  10 questions flagged "live" (the shared key is capped).

    FALKORDB_PORT=16379 FALKORDB_PASSWORD_FILE=.falkordb.pw python -m tests.eval.run_eval --mock
    python -m tests.eval.run_eval --live https://sniff.quantbase.live --only-live --out docs/eval_live.json
"""
from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
import time
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).parent
QUESTIONS = HERE / "questions.jsonl"
POLICY_LINE = "History, not a prediction."
BANNED = re.compile(r"\b(buy it|you should buy|should (?:you )?(?:buy|sell)|sell now|is safe|it's safe|"
                    r"scam|rug ?pull|will (?:pump|moon|go up|rise|10x)|price will (?:go|be|rise|hit|reach|pump|moon)|guarantee[ds]?)\b", re.I)


SENT = re.compile(r"(?<=[.!?\]])\s+(?=[A-Z0-9\"'(])")
NEGATION = re.compile(r"\b(can't|cannot|can not|won't|don't|doesn't|not able|no way to|isn't|is not)\b", re.I)
EXPECT_TEXT = {"not in": ["not in", "isn't in", "is not in", "no record", "not found"]}


def load(only_live: bool = False) -> list[dict]:
    qs = [json.loads(line) for line in QUESTIONS.read_text().splitlines() if line.strip()]
    return [q for q in qs if q.get("live")] if only_live else qs


def score(q: dict, answer: dict) -> dict:
    """answer: {"tools": [names], "verdict": {"text", "cited", "unknown_cited", "mismatched_cited"}}"""
    called = answer.get("tools") or []
    v = answer.get("verdict") or {}
    text = v.get("text") or ""
    want, also = set(q.get("expect_tools") or []), set(q.get("also_ok") or [])
    tools_ok = not want or want <= set(called) or bool(also & set(called))
    bad_cites = (v.get("unknown_cited") or []) + (v.get("mismatched_cited") or [])
    if q.get("refuse") and not want:
        cites_ok = not bad_cites
    else:
        cites_ok = bool(v.get("cited")) and not bad_cites if not q.get("expect_text") else not bad_cites
    sentences = [x for x in SENT.split(text.replace(POLICY_LINE, "")) if x.strip()]
    # Advice words count only when stated, not when refused ("I can't say whether it will pump").
    stated = [x for x in sentences if BANNED.search(x) and not NEGATION.search(x)]
    policy_ok = POLICY_LINE in text and not stated
    if q.get("expect_text"):
        wanted = EXPECT_TEXT.get(q["expect_text"], [q["expect_text"]])
        policy_ok = policy_ok and any(t in text.lower() for t in wanted)
    body = [x for x in sentences if not x.strip().startswith("For context:")]
    return {"id": q["id"], "kind": q["kind"], "tools": tools_ok, "citations": cites_ok, "policy": policy_ok,
            "short": len(body) <= 5, "sentences": len(body),
            "called": called, "cited": v.get("cited"), "bad_cites": bad_cites, "text": text}


def summary(rows: list[dict]) -> dict:
    n = len(rows)
    out = {k: sum(r[k] for r in rows) for k in ("tools", "citations", "policy")}
    out["all_three"] = sum(r["tools"] and r["citations"] and r["policy"] for r in rows)
    out["short"] = sum(r.get("short", True) for r in rows)
    out["n"] = n
    return out


# ---- mock Claude -----------------------------------------------------------------------------

def _args(q: dict, tool: str) -> dict:
    if q.get("args"):
        return dict(q["args"])
    return {"mint": q["mint"]} if q.get("mint") else {"query": q["question"]}


class ScriptedClaude:
    """Calls the question's expected tools, then answers from the evidence they returned."""

    def __init__(self, q: dict):
        self.q, self.turn = q, 0
        self.messages = SimpleNamespace(create=self.create)

    async def create(self, **kw):
        self.turn += 1
        want = self.q.get("expect_tools") or []
        if self.turn == 1 and want:
            blocks = []
            for i, t in enumerate(want):
                inp = _args(self.q, t)
                blocks.append(SimpleNamespace(type="tool_use", id=f"tu{i}", name=t, input=inp,
                                              model_dump=lambda t=t, inp=inp, i=i, **_: {
                                                  "type": "tool_use", "id": f"tu{i}", "name": t, "input": inp}))
            return SimpleNamespace(content=blocks, stop_reason="tool_use")
        system = kw["system"][0]["text"]
        closing = system.rsplit("End with exactly this line: ", 1)[-1].strip()
        if not want:
            body = "Sniff only shows the history of who is behind a coin; it cannot tell what a price will do."
        else:
            results = [json.loads(c["content"]) for m in kw["messages"] if m["role"] == "user"
                       and isinstance(m["content"], list) for c in m["content"]]
            sents = []
            for res in results:
                rows = res.get("rows") or []
                if res.get("found") is False:
                    sents.append(f"This coin is not in Sniff's graph [{res['evidence']}].")
                elif rows:
                    for r in rows[:2]:
                        sents.append(f"{_say(self.q['kind'], r)} [{r['evidence']}].")
                elif isinstance(res.get("evidence"), str):
                    sents.append(f"{res.get('note') or 'Nothing found.'} [{res['evidence']}]")
                elif isinstance(res.get("evidence"), list):
                    sents.append(f"The creator made {res.get('creator_other_coins', 0)} other coins "
                                 f"[{res['evidence'][0]}].")
            body = " ".join(sents) or "No links found."
        return SimpleNamespace(content=[SimpleNamespace(type="text", text=f"{body} {closing}")], stop_reason="end_turn")


def _say(kind: str, r: dict) -> str:
    return {"siblings": f"Funder {r.get('funder', '')[:4]} also paid {r.get('creators')} other creators",
            "shared_snipers": f"{r.get('shared')} early buyers also bought early into another coin",
            "shared_handles": f"Its {r.get('platform')} handle is also on {r.get('other_coins')} other coins",
            "funding_trail": f"It was funded {r.get('depth')} hop(s) back",
            "connect": f"The two are linked in {r.get('hops')} hops",
            "top_operators": f"One funder paid {r.get('creators')} creators",
            "search_coins": f"A coin named {r.get('name')} matches"}.get(kind, "Found")


async def _mock_one(q: dict) -> dict:
    from app import agent
    fake = ScriptedClaude(q)
    orig = agent.ai.client_for
    agent.ai.client_for = lambda k: (fake, "scripted", "owner")
    try:
        events = [e async for e in agent.investigate(q["question"], q.get("mint"))]
    finally:
        agent.ai.client_for = orig
    return {"tools": [e["tool"] for e in events if e["type"] == "step"],
            "verdict": next(e for e in events if e["type"] == "verdict")}


def run_mock(qs: list[dict]) -> list[dict]:
    return [score(q, asyncio.run(_mock_one(q))) for q in qs]


# ---- live ------------------------------------------------------------------------------------

def run_live(qs: list[dict], base: str) -> list[dict]:
    import httpx
    rows = []
    for q in qs:
        t = time.monotonic()
        r = httpx.post(f"{base}/api/ask", json={"question": q["question"], "mint": q.get("mint")},
                       headers={"origin": base}, timeout=120)
        body = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
        if r.status_code != 200:
            body = {"verdict": {"text": f"HTTP {r.status_code}: {body.get('error')}"}}
        ans = {"tools": [s["tool"] for s in body.get("steps") or []], "verdict": body.get("verdict") or {}}
        row = score(q, ans)
        row.update(mode=body.get("mode"), ms=int(1000 * (time.monotonic() - t)))
        rows.append(row)
        print(f"{q['id']:>3} tools={row['tools']!s:5} cites={row['citations']!s:5} policy={row['policy']!s:5} "
              f"{row['ms']} ms {row['called']}", file=sys.stderr)
    return rows


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--live")
    p.add_argument("--only-live", action="store_true")
    p.add_argument("--out")
    p.add_argument("--rescore", help="re-score a saved --out file without calling anything")
    a = p.parse_args(argv)
    if a.rescore:
        old = json.loads(Path(a.rescore).read_text())
        byid = {q["id"]: q for q in load()}
        rows = []
        for r in old["rows"]:
            ans = {"tools": r["called"], "verdict": {"text": r["text"], "cited": r["cited"],
                                                     "unknown_cited": r["bad_cites"]}}
            rows.append({**score(byid[r["id"]], ans), **{k: r[k] for k in ("mode", "ms") if k in r}})
        mode = old["mode"]
    else:
        qs = load(a.only_live)
        rows = run_live(qs, a.live.rstrip("/")) if a.live else run_mock(qs)
        mode = "live" if a.live else "mock"
    res = {"mode": mode, "summary": summary(rows), "rows": rows}
    print(json.dumps(res["summary"]))
    if a.out:
        Path(a.out).write_text(json.dumps(res, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
