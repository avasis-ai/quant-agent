"""Sniff web app (FastAPI). Day 1: the landing page, /settings (owner key + visitor BYOK)."""
from __future__ import annotations

import hashlib
import hmac
import logging
import os
import secrets
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from pydantic import BaseModel

from . import ai
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
    yield


app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)

login_limit = Limiter(5, 15 * 60)
key_limit = Limiter(10, 60 * 60)
visitor_check_limit = Limiter(10, 60 * 60)
owner_ping_limit = Limiter(20, 60 * 60)


def _session_secret() -> bytes:
    env = read_env()
    s = env.get("SESSION_SECRET")
    if not s:
        s = secrets.token_hex(32)
        write_env({"SESSION_SECRET": s})
    return bytes.fromhex(s)


# ---- helpers -------------------------------------------------------------------

def ip(req: Request) -> str:
    return req.client.host if req.client else "?"


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
def landing():
    page = LANDING / "index.html"
    if page.exists():
        return FileResponse(page, headers={"Cache-Control": "no-cache"})
    return HTMLResponse("<h1>Sniff</h1>")


@app.get("/settings", response_class=HTMLResponse)
def settings_page():
    return FileResponse(STATIC / "settings.html")


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
