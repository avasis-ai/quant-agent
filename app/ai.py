"""Which Anthropic key a request uses, and checking that a key works.

Owner key: set on /settings behind the admin passcode, kept in the env file and in memory,
hot-swapped without a restart. Visitor key: sent per request in the X-Anthropic-Key header,
used for that request only, never stored or logged.
"""
from __future__ import annotations

from dataclasses import dataclass

import anthropic
import httpx

from .secrets import last4, read_env, write_env

API = "https://api.anthropic.com/v1"
VERSION = "2023-06-01"
# Best first. The first model the key can use answers questions; the cheapest one validates.
PREFERRED = ["claude-sonnet-5-5", "claude-opus-5-5", "claude-sonnet-5", "claude-haiku-5-5"]
CHEAP = ["claude-haiku-5-5", "claude-sonnet-5-5"]
VISITOR_HEADER = "x-anthropic-key"


class KeyError_(Exception):
    """A key that does not work, with a message safe to show (never contains the key)."""


@dataclass
class Owner:
    key: str | None = None
    model: str | None = None
    client: anthropic.AsyncAnthropic | None = None

    @property
    def active(self) -> bool:
        return self.key is not None

    def public(self, admin: bool) -> dict:
        out = {"active": self.active, "model": self.model}
        if admin:
            out["last4"] = last4(self.key)
        return out


OWNER = Owner()


def load_owner() -> None:
    env = read_env()
    key = env.get("ANTHROPIC_API_KEY") or None
    _set_owner(key, env.get("ANTHROPIC_MODEL") or None)


def _set_owner(key: str | None, model: str | None) -> None:
    OWNER.key = key
    OWNER.model = model if key else None
    OWNER.client = anthropic.AsyncAnthropic(api_key=key, max_retries=2) if key else None


async def check_key(key: str) -> str:
    """One free call (list models) and one 1-token call. Returns the model to use."""
    key = (key or "").strip()
    if not key.startswith("sk-ant-") or len(key) < 40:
        raise KeyError_("That doesn't look like an Anthropic key (it should start with sk-ant-).")
    headers = {"x-api-key": key, "anthropic-version": VERSION}
    async with httpx.AsyncClient(timeout=20) as http:
        r = await http.get(f"{API}/models", headers=headers, params={"limit": 100})
        if r.status_code in (401, 403):
            raise KeyError_("Anthropic did not accept that key.")
        if r.status_code != 200:
            raise KeyError_(f"Anthropic answered {r.status_code}. Try again in a minute.")
        ids = [m["id"] for m in r.json().get("data", [])]
        model = next((m for m in PREFERRED if m in ids), None) or next((i for i in ids if "sonnet" in i), None)
        if not model:
            raise KeyError_("This key has no Claude model Sniff can use.")
        cheap = next((m for m in CHEAP if m in ids), model)
        r = await http.post(f"{API}/messages", headers={**headers, "content-type": "application/json"},
                            json={"model": cheap, "max_tokens": 1, "messages": [{"role": "user", "content": "hi"}]})
        if r.status_code == 400 and "credit" in r.text.lower():
            raise KeyError_("The key works but its account has no credit left.")
        if r.status_code == 429:
            raise KeyError_("The key works but is rate-limited right now. Try again shortly.")
        if r.status_code != 200:
            raise KeyError_(f"A test message failed ({r.status_code}).")
    return model


async def activate_owner(key: str) -> Owner:
    model = await check_key(key)
    write_env({"ANTHROPIC_API_KEY": key.strip(), "ANTHROPIC_MODEL": model})
    _set_owner(key.strip(), model)
    return OWNER


def remove_owner() -> None:
    write_env({"ANTHROPIC_API_KEY": None, "ANTHROPIC_MODEL": None})
    _set_owner(None, None)


def client_for(visitor_key: str | None) -> tuple[anthropic.AsyncAnthropic | None, str | None, str]:
    """(client, model, who) for one request. who is 'visitor', 'owner' or 'none'."""
    if visitor_key:
        return anthropic.AsyncAnthropic(api_key=visitor_key.strip(), max_retries=1), OWNER.model or PREFERRED[0], "visitor"
    if OWNER.client:
        return OWNER.client, OWNER.model, "owner"
    return None, None, "none"
