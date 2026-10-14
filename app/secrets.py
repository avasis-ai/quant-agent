"""Key handling for Sniff. The rule everywhere: a key is never logged, echoed or returned.

The owner's key lives in the app env file (chmod 600) and in this process's memory.
A visitor's own key arrives per request in a header and is never stored.
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import os
import re
import secrets
import tempfile
import threading
from pathlib import Path

ENV_FILE = Path(os.environ.get("SNIFF_ENV_FILE", "/opt/lineage/env/app.env"))
KEY_RE = re.compile(r"sk-ant-[A-Za-z0-9_\-]{8,}")
_lock = threading.Lock()


def mask(text: str) -> str:
    """Hide anything that looks like an Anthropic key."""
    return KEY_RE.sub(lambda m: "sk-ant-…" + m.group(0)[-4:], text or "")


class MaskFilter(logging.Filter):
    """Masks keys in every log record, including formatted arguments."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            msg = record.getMessage()
        except Exception:  # noqa: BLE001 - a broken record must not crash logging
            return True
        masked = mask(msg)
        if masked != msg:
            record.msg, record.args = masked, ()
        return True


def install_log_masking() -> None:
    for name in ("", "uvicorn", "uvicorn.error", "uvicorn.access", "httpx", "anthropic", "fastapi"):
        logging.getLogger(name).addFilter(MaskFilter())
    for h in logging.getLogger().handlers:
        h.addFilter(MaskFilter())


def last4(key: str | None) -> str | None:
    return f"…{key[-4:]}" if key else None


# ---- env file ---------------------------------------------------------------

def read_env() -> dict[str, str]:
    out: dict[str, str] = {}
    if not ENV_FILE.exists():
        return out
    for line in ENV_FILE.read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def write_env(updates: dict[str, str | None]) -> None:
    """Atomically rewrite the env file with chmod 600. None removes a key."""
    with _lock:
        env = read_env()
        for k, v in updates.items():
            if v is None:
                env.pop(k, None)
            else:
                env[k] = v
        ENV_FILE.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=ENV_FILE.parent, prefix=".app.env.")
        try:
            os.fchmod(fd, 0o600)
            with os.fdopen(fd, "w") as f:
                f.write("".join(f"{k}={v}\n" for k, v in env.items()))
            os.replace(tmp, ENV_FILE)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)
        os.chmod(ENV_FILE, 0o600)


# ---- admin passcode (scrypt) --------------------------------------------------

def hash_passcode(code: str) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.scrypt(code.encode(), salt=salt, n=2**15, r=8, p=1, maxmem=64 * 1024 * 1024, dklen=32)
    return f"scrypt$32768$8$1${salt.hex()}${dk.hex()}"


def check_passcode(code: str, stored: str | None) -> bool:
    if not stored or not code:
        return False
    try:
        _, n, r, p, salt, want = stored.split("$")
        dk = hashlib.scrypt(code.encode(), salt=bytes.fromhex(salt), n=int(n), r=int(r), p=int(p),
                            maxmem=64 * 1024 * 1024, dklen=32)
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(dk.hex(), want)
