"""Conservative gate for public knowledge and shared memory. Never echo a match."""
from __future__ import annotations

import ipaddress
import json
import re


class PrivacyError(ValueError):
    pass


PATTERNS = {
    "email": r"[A-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Z0-9-]+(?:\.[A-Z0-9-]+)+",
    "api_key": r"\b(?:sk-(?:ant-)?[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AIza[A-Za-z0-9_-]{30,}|xox[baprs]-[A-Za-z0-9-]{12,})",
    "aws_id": r"\b(?:AKIA|ASIA|AIDA|AROA)[A-Z0-9]{16}\b|arn:aws:[^\s\"<>]+|\b\d{12}\b",
    "private_key": r"-----BEGIN (?:RSA |EC |OPENSSH |ENCRYPTED )?PRIVATE KEY-----|\b[1-9A-HJ-NP-Za-km-z]{80,90}\b|\b(?:0x)?[a-f0-9]{64}\b",
    "credential_assignment": r"\b(?:password|secret|private[_ -]?key|seed[_ -]?phrase|mnemonic|access[_ -]?token|api[_ -]?key)\s*[=:]\s*[\"']?[A-Za-z0-9/+_-]{8,}",
    "wallet_key_array": r"\[\s*(?:\d{1,3}\s*,\s*){31,}\d{1,3}\s*\]",
    "seed_phrase": r"\b(?:seed|mnemonic|recovery)(?:\s+phrase)?\s*[:=]\s*(?:[a-z]+\s+){11,23}[a-z]+\b",
}
CHECKS = {name: re.compile(pattern, re.I if name != "aws_id" else 0) for name, pattern in PATTERNS.items()}


def scan(text: str) -> list[str]:
    found = [name for name, pattern in CHECKS.items() if pattern.search(text)]
    candidates = re.findall(r"(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])|(?<![\w:])(?:[0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}(?![\w:])", text)
    for candidate in candidates:
        try:
            ipaddress.ip_address(candidate)
            found.append("ip_address")
            break
        except ValueError:
            pass
    return sorted(set(found))


def require_public(value) -> None:
    """Reject the whole payload before a write; error contains categories only."""
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, default=str)
    reasons = scan(text)
    if reasons:
        raise PrivacyError("Public-source privacy check refused: " + ", ".join(reasons))
