"""Sniff over MCP: the same 9 read-only graph tools the agent uses, for any MCP client (Claude Code,
Claude Desktop, other agents). Streamable HTTP at /mcp, stateless, JSON responses.

No AI key is involved: every tool is a fixed, parameterised read of the graph, so a call costs the
site nothing but a query. Calls are rate-limited per IP and per day like /api/ask. Each call gets a
fresh evidence list, so ids restart at E1 per call.
"""
from __future__ import annotations

import asyncio
import json
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from mcp.server.fastmcp.server import StreamableHTTPASGIApp

from . import tools
from .limits import Limiter

PATH = "/mcp"
per_ip = Limiter(120, 60 * 60)        # MCP requests (initialize, list, calls) per IP per hour
daily = Limiter(5000, 24 * 60 * 60)   # all MCP requests together per day

INSTRUCTIONS = """Sniff answers who is behind a pump.fun meme coin on Solana, from a graph of public on-chain
history: coins, their creators, who funded the creators, early buyers, shared socials and funding rings.
Start with coin_dossier for a coin (search_coins if you only have a name). Hubs are funders of more than 200
wallets, likely exchanges: they end funding trails and never link two things. Every result carries evidence
ids; cite them. This is history, not a prediction or advice."""

server = FastMCP(
    "sniff", instructions=INSTRUCTIONS, website_url="https://sniff.quantbase.live",
    stateless_http=True, json_response=True, streamable_http_path=PATH,
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=["sniff.quantbase.live", "127.0.0.1:*", "localhost:*", "testserver"],
        allowed_origins=["https://sniff.quantbase.live", "http://127.0.0.1:*", "http://localhost:*"]),
)


async def _run(name: str, args: dict[str, Any]) -> dict:
    ev = tools.Evidence()
    res, ok = await asyncio.to_thread(tools.run_tool, ev, name, args)
    if not ok:
        raise ValueError(res.get("error") or "The tool failed.")
    return {"result": json.loads(tools.cap(res, 20000)), "evidence": ev.items}


@server.tool()
async def search_coins(query: str) -> dict:
    """Find pump.fun coins by words from their name or ticker. Use when you have a name, not an address.
    Several coins can share a name: pick by mint."""
    return await _run("search_coins", {"query": query})


@server.tool()
async def coin_dossier(mint: str) -> dict:
    """Start here for a coin (mint address): its creator, the creator's other coins and how many graduated,
    who funded the creator (hubs marked), and the creator's funding ring if any."""
    return await _run("coin_dossier", {"mint": mint})


@server.tool()
async def funding_trail(address: str) -> dict:
    """Who funded a wallet, up to 3 hops back. A hub (likely an exchange) ends a trail and proves nothing."""
    return await _run("funding_trail", {"address": address})


@server.tool()
async def siblings(mint: str) -> dict:
    """Other creators paid by the same (non-hub) funder as this coin's creator, and how their coins did."""
    return await _run("siblings", {"mint": mint})


@server.tool()
async def shared_snipers(mint: str) -> dict:
    """Other coins this coin's early buyers also bought early, scored by how rare each buyer is.
    Bots (wallets with more than 100 early buys) are ignored."""
    return await _run("shared_snipers", {"mint": mint})


@server.tool()
async def shared_handles(mint: str) -> dict:
    """Other coins that reuse this coin's X, Telegram or website, by how many other creators."""
    return await _run("shared_handles", {"mint": mint})


@server.tool()
async def ring(mint: str | None = None, address: str | None = None) -> dict:
    """The funding ring (creators linked to each other through funding) that a coin's creator or a wallet
    belongs to: its size, coins, graduations and top creators. Give a mint or an address."""
    return await _run("ring", {"mint": mint, "address": address})


@server.tool()
async def connect(a: str, b: str) -> dict:
    """Shortest funding, creation or social link between two coins or wallets (up to 6 hops), never
    through a hub or a platform-sized handle. Empty means no link was found."""
    return await _run("connect", {"a": a, "b": b})


@server.tool()
async def top_operators(days: int = 7) -> dict:
    """Funders behind the most creators whose coins launched in the last `days` (1-30) of the graph,
    with how many of those coins graduated."""
    return await _run("top_operators", {"days": days})


def _client_ip(scope: dict) -> str:
    """Same rule as main.ip(): trust X-Forwarded-For only from Caddy on loopback."""
    host = (scope.get("client") or ("?", 0))[0]
    if host in ("127.0.0.1", "::1"):
        for k, v in scope.get("headers") or []:
            if k == b"x-forwarded-for":
                fwd = v.decode("latin-1").split(",")[0].strip()
                if fwd:
                    return fwd
    return host


class Limited:
    """ASGI wrapper: rate limits, then hands the request to the MCP transport of the current lifespan."""

    def __init__(self):
        self._for, self._inner = None, None

    async def __call__(self, scope, receive, send):
        mgr = server.session_manager
        if self._for is not mgr:
            self._for, self._inner = mgr, StreamableHTTPASGIApp(mgr)
        key = _client_ip(scope)
        if scope.get("method") == "POST" and (not per_ip.allow(key) or not daily.allow("all")):
            body = json.dumps({"error": "Too many requests. Try again later."}).encode()
            await send({"type": "http.response.start", "status": 429,
                        "headers": [(b"content-type", b"application/json"),
                                    (b"retry-after", str(per_ip.retry_after(key) or 60).encode())]})
            await send({"type": "http.response.body", "body": body})
            return
        await self._inner(scope, receive, send)


def lifespan():
    """Async context manager that must wrap the app's lifetime. A session manager runs only once, so
    each app lifespan (and each test client) gets a fresh one."""
    server._session_manager = None
    server.streamable_http_app()
    return server.session_manager.run()
