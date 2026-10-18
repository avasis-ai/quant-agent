"""Sniff web app (FastAPI): the landing page, /settings (owner key + visitor BYOK), /api/ask (the agent),
/mcp (the graph tools over MCP)."""
from __future__ import annotations

import asyncio
import hashlib
import json
import hmac
import logging
import os
import secrets
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import agent, ai, tools, memory
from . import mcp as sniff_mcp
from .limits import Limiter
from .secrets import check_passcode, install_log_masking, read_env, write_env

log = logging.getLogger("sniff")
install_log_masking()

STATIC = Path(__file__).parent / "static"
LANDING = Path(os.environ.get("SNIFF_LANDING_DIR", "/opt/lineage/placeholder"))
ORIGINS = {o.strip() for o in os.environ.get("SNIFF_ORIGINS", "https://sniff.quantbase.live,http://127.0.0.1:8080").split(",")}
COOKIE = "sniff_owner"
SESSION_HOURS = 12

SECRET = b""


@asynccontextmanager
async def lifespan(_app):
    global SECRET
    SECRET = _session_secret()
    ai.load_owner()
    log.info("sniff app up; owner key %s", "active" if ai.OWNER.active else "not set")
    async with sniff_mcp.lifespan():
        yield


app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC), name="static")
app.mount("/blog-assets", StaticFiles(directory=STATIC.parent.parent / "docs" / "blog"), name="blog-assets")
app.router.add_route(sniff_mcp.PATH, sniff_mcp.Limited(), methods=["GET", "POST", "DELETE"],
                     include_in_schema=False)  # MCP: the agent's graph tools for any MCP client
if os.environ.get("SNIFF_MEDIA_DIR"):  # local dev only: in production Caddy serves /media
    app.mount("/media", StaticFiles(directory=os.environ["SNIFF_MEDIA_DIR"]), name="media")

login_limit = Limiter(5, 15 * 60)
key_limit = Limiter(10, 60 * 60)
visitor_check_limit = Limiter(10, 60 * 60)
owner_ping_limit = Limiter(20, 60 * 60)
ask_owner_limit = Limiter(15, 60 * 60)        # per visitor IP, on the site's key
ask_owner_daily = Limiter(300, 24 * 60 * 60)  # all visitors together, on the site's key
ask_visitor_limit = Limiter(60, 60 * 60)      # per IP, on the visitor's own key
ask_dossier_limit = Limiter(60, 60 * 60)      # per IP, no AI
lookup_limit = Limiter(240, 60 * 60)          # per IP: search box and dossier cards


def _session_secret() -> bytes:
    env = read_env()
    s = env.get("SESSION_SECRET")
    if not s:
        s = secrets.token_hex(32)
        write_env({"SESSION_SECRET": s})
    return bytes.fromhex(s)


# ---- helpers -------------------------------------------------------------------

def ip(req: Request) -> str:
    """The visitor's IP. Behind Caddy every request comes from 127.0.0.1; Caddy replaces any
    X-Forwarded-For the client sent with the real address, so trust it only from loopback."""
    host = req.client.host if req.client else "?"
    if host in ("127.0.0.1", "::1"):
        fwd = req.headers.get("x-forwarded-for", "").split(",")[0].strip()
        if fwd:
            return fwd
    return host


def same_origin(req: Request) -> None:
    origin = req.headers.get("origin")
    if origin and origin not in ORIGINS:
        raise HTTPException(403, "Wrong origin.")


def make_session() -> str:
    exp = str(int(time.time()) + SESSION_HOURS * 3600)
    sig = hmac.new(SECRET, exp.encode(), hashlib.sha256).hexdigest()
    return f"{exp}.{sig}"


def is_owner(req: Request) -> bool:
    tok = req.cookies.get(COOKIE, "")
    try:
        exp, sig = tok.split(".")
    except ValueError:
        return False
    good = hmac.compare_digest(sig, hmac.new(SECRET, exp.encode(), hashlib.sha256).hexdigest())
    return good and int(exp) > time.time()


def need_owner(req: Request) -> None:
    if not is_owner(req):
        raise HTTPException(401, "Enter the admin passcode first.")


def limited(lim: Limiter, key: str) -> None:
    if not lim.allow(key):
        raise HTTPException(429, f"Too many tries. Wait {lim.retry_after(key) // 60 + 1} min.")


def visitor_key(req: Request) -> str | None:
    k = req.headers.get(ai.VISITOR_HEADER, "").strip()
    return k or None


@app.exception_handler(HTTPException)
async def _http_err(_req: Request, e: HTTPException):
    return JSONResponse({"error": e.detail}, status_code=e.status_code)


@app.exception_handler(Exception)
async def _any_err(_req: Request, e: Exception):
    log.error("unhandled %s", type(e).__name__)  # never the message: it could carry request data
    return JSONResponse({"error": "Something went wrong."}, status_code=500)


@app.middleware("http")
async def _headers(req: Request, call_next):
    res = await call_next(req)
    res.headers["X-Content-Type-Options"] = "nosniff"
    res.headers["Referrer-Policy"] = "same-origin"
    if req.url.path.startswith("/api/settings") or req.url.path == "/settings":
        res.headers["Cache-Control"] = "no-store"
    return res


# ---- pages -----------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
def app_page(req: Request):
    # Coin links from the original single-page UI and demo keep opening the investigation.
    if req.query_params.get("mint") or req.query_params.get("q"):
        return RedirectResponse("/app?" + req.url.query, status_code=302)
    return FileResponse(STATIC / "home.html", headers={"Cache-Control": "no-cache"})


@app.get("/app", response_class=HTMLResponse)
def investigation_page():
    return FileResponse(STATIC / "app.html", headers={"Cache-Control": "no-cache"})


@app.get("/waitlist", response_class=HTMLResponse)
def waitlist_page():
    """The pre-launch page with the waitlist form (it posts to /api/waitlist, served by its own service)."""
    page = LANDING / "index.html"
    if page.exists():
        return FileResponse(page, headers={"Cache-Control": "no-cache"})
    return RedirectResponse("/", status_code=302)


@app.get("/settings", response_class=HTMLResponse)
def settings_page():
    return FileResponse(STATIC / "settings.html")


@app.get("/blog", response_class=HTMLResponse)
def blog_page():
    return FileResponse(STATIC / "blog.html", headers={"Cache-Control": "no-cache"})


@app.get("/healthz")
def healthz():
    return {"ok": True}


# ---- settings API ------------------------------------------------------------------

class Passcode(BaseModel):
    passcode: str


class KeyIn(BaseModel):
    key: str


@app.get("/api/settings/status")
def status(req: Request):
    admin = is_owner(req)
    return {"admin": admin, "owner": ai.OWNER.public(admin)}


@app.post("/api/settings/login")
def login(body: Passcode, req: Request):
    same_origin(req)
    limited(login_limit, ip(req))
    if not check_passcode(body.passcode.strip(), read_env().get("ADMIN_PASSCODE_HASH")):
        raise HTTPException(401, "Wrong passcode.")
    res = JSONResponse({"ok": True, "owner": ai.OWNER.public(True)})
    res.set_cookie(COOKIE, make_session(), max_age=SESSION_HOURS * 3600, httponly=True,
                   secure=req.url.scheme == "https" or req.headers.get("x-forwarded-proto") == "https",
                   samesite="strict", path="/")
    return res


@app.post("/api/settings/logout")
def logout(req: Request):
    same_origin(req)
    res = JSONResponse({"ok": True})
    res.delete_cookie(COOKIE, path="/")
    return res


@app.post("/api/settings/owner-key")
async def set_owner_key(body: KeyIn, req: Request):
    same_origin(req)
    need_owner(req)
    limited(key_limit, ip(req))
    try:
        owner = await ai.activate_owner(body.key)
    except ai.KeyError_ as e:
        raise HTTPException(400, str(e))
    log.info("owner key activated (%s), model %s", owner.public(True)["last4"], owner.model)
    return {"ok": True, "owner": owner.public(True)}


@app.delete("/api/settings/owner-key")
def delete_owner_key(req: Request):
    same_origin(req)
    need_owner(req)
    ai.remove_owner()
    log.info("owner key removed")
    return {"ok": True, "owner": ai.OWNER.public(True)}


@app.post("/api/settings/visitor-check")
async def visitor_check(req: Request):
    """Checks a visitor's own key. Nothing is stored; the key came in a header."""
    same_origin(req)
    key = visitor_key(req)
    if not key:
        raise HTTPException(400, "No key sent.")
    limited(visitor_check_limit, ip(req))
    try:
        model = await ai.check_key(key)
    except ai.KeyError_ as e:
        raise HTTPException(400, str(e))
    return {"ok": True, "model": model}


@app.post("/api/ai/ping")
async def ping(req: Request):
    """A one-line answer from whichever key this request would use."""
    same_origin(req)
    client, model, who = ai.client_for(visitor_key(req))
    if not client:
        raise HTTPException(503, "No AI key is active yet. Add one on the Settings page.")
    if who == "owner":
        limited(owner_ping_limit, ip(req))
    try:
        msg = await client.messages.create(model=model, max_tokens=20,
                                           messages=[{"role": "user", "content": "Reply with exactly: Sniff is ready."}])
    except Exception as e:  # noqa: BLE001 - the SDK error text is safe, but keep it short
        raise HTTPException(502, f"The AI call failed ({type(e).__name__}).")
    text = "".join(getattr(b, "text", "") for b in msg.content).strip()
    return {"ok": True, "using": who, "model": model, "reply": text[:80]}


# ---- the agent ---------------------------------------------------------------------------------

class Ask(BaseModel):
    question: str
    mint: str | None = None
    session_id: str | None = None


@app.post("/api/ask")
async def ask(body: Ask, req: Request):
    """Investigate a coin. JSON by default; server-sent events when the client accepts text/event-stream."""
    same_origin(req)
    question = (body.question or "").strip()[:500]
    mint = (body.mint or "").strip() or None
    if not question and not mint:
        raise HTTPException(400, "Ask about a coin: paste its address or name.")
    if mint and not agent.MINT_IN_TEXT.fullmatch(mint):
        raise HTTPException(400, "That doesn't look like a coin address.")
    question = question or "Who is behind this coin?"
    vkey = visitor_key(req)
    _, _, who = ai.client_for(vkey)
    who_ip = ip(req)
    if who == "owner":
        limited(ask_owner_limit, who_ip)
        if not ask_owner_daily.allow("all"):
            raise HTTPException(429, "Sniff's shared key is busy today. Add your own key on the Settings page.")
    elif who == "visitor":
        limited(ask_visitor_limit, who_ip)
    else:
        limited(ask_dossier_limit, who_ip)

    try:
        sid = memory.session_id(body.session_id or req.cookies.get("sniff_session") or None)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    events = agent.investigate(question, mint, vkey, session_id=sid)

    def with_session(res):
        res.set_cookie("sniff_session", sid, httponly=True, samesite="lax", path="/",
                       secure=req.url.scheme == "https" or req.headers.get("x-forwarded-proto") == "https",
                       max_age=30 * 24 * 3600)
        return res
    if "text/event-stream" in req.headers.get("accept", ""):
        async def sse():
            async for e in events:
                yield f"event: {e['type']}\ndata: {json.dumps(e, default=str)}\n\n"
        return with_session(StreamingResponse(sse(), media_type="text/event-stream",
                                 headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"}))
    out: dict = {"steps": [], "evidence": [], "verdict": None}
    async for e in events:
        if e["type"] == "step":
            out["steps"].append(e)
        elif e["type"] == "evidence":
            out["evidence"] = e["items"]
        elif e["type"] == "verdict":
            out["verdict"] = e
        elif e["type"] in ("start", "done"):
            out.update({k: v for k, v in e.items() if k != "type"})
        elif e["type"] == "notice":
            out.setdefault("notices", []).append(e["text"])
    return with_session(JSONResponse(out, headers={"Cache-Control": "no-store"}))


# ---- lookups for the app page (no AI) --------------------------------------------------------

@app.get("/api/search")
async def search(q: str, req: Request):
    """Coins by name, ticker or address, for the search box."""
    limited(lookup_limit, ip(req))
    q = q.strip()[:80]
    if agent.MINT_IN_TEXT.fullmatch(q):
        res, ok = await asyncio.to_thread(tools.run_tool, tools.Evidence(), "coin_dossier", {"mint": q})
        return {"rows": [res["coin"]] if ok and res.get("found") else []}
    res, ok = await asyncio.to_thread(tools.run_tool, tools.Evidence(), "search_coins", {"query": q})
    return {"rows": [{k: v for k, v in r.items() if k != "evidence"} for r in res.get("rows", [])] if ok else []}


@app.get("/api/dossier")
async def dossier_card(mint: str, req: Request):
    """The fixed facts for the dossier card: shown with or without an AI key."""
    limited(lookup_limit, ip(req))
    mint = mint.strip()
    if not agent.MINT_IN_TEXT.fullmatch(mint):
        raise HTTPException(400, "That doesn't look like a coin address.")
    ev = tools.Evidence()
    out = {}
    for name in ("coin_dossier", "siblings", "shared_handles"):
        res, ok = await asyncio.to_thread(tools.run_tool, ev, name, {"mint": mint})
        out[name] = res if ok else {"error": res.get("error")}
        if name == "coin_dossier" and not res.get("found"):
            break
    out["base"] = tools.base_rate()
    out["evidence"] = ev.items
    return out


# Memory and brain APIs live in their own router; their pages share the site chrome.
from .track_routes import router as track_router  # noqa: E402
app.include_router(track_router)
