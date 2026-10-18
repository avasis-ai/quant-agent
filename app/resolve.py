"""Resolve user input with the existing read-only coin search, never session defaults."""
from __future__ import annotations

import re

from . import tools

DEFAULT_QUESTION = "Who is behind this coin?"
NOT_FOUND = "Not in our snapshot (ends 14 Oct 2026). Try a recorded coin below or check the mint address."
STOP = set("who what when where why how is are was were did does do the a an of for in on to by and or its this that coin token creator funder funded funding behind launched launch tell me about investigate please can you has have with other coins wallet wallets ring connected socials shared history show".split())


def normalize(text: str) -> str:
    return " ".join(re.findall(r"[\w]+", text.casefold()))


def resolve(text: str) -> dict:
    text = text.strip()[:500]
    question = bool(re.search(r"\?|^(?:who|what|when|where|why|how|is|are|did|does|can|show|tell|investigate)\b", text, re.I))
    mints = re.findall(r"\b[1-9A-HJ-NP-Za-km-z]{32,44}\b", text)
    words = [word for word in re.findall(r"[A-Za-z0-9]+", text) if word.casefold() not in STOP]
    query = mints[0] if mints else " ".join(words[:4])
    if not query:
        return {"status": "question", "coin": None, "question": text, "rows": []}
    ev = tools.Evidence()
    if mints:
        result, ok = tools.run_tool(ev, "coin_dossier", {"mint": query})
        rows = [result["coin"]] if ok and result.get("found") else []
    else:
        result, ok = tools.run_tool(ev, "search_coins", {"query": query})
        rows = result.get("rows", []) if ok else []
    if not ok:
        return {"status": "error", "message": "Coin search is unavailable. Please try again.", "rows": []}
    normalized = normalize(text)
    matches = []
    for row in rows:
        aliases = [normalize(row.get(field, "")) for field in ("name", "symbol")]
        if mints or any(alias and (normalized == alias or f" {alias} " in f" {normalized} ") for alias in aliases):
            matches.append({key: value for key, value in row.items() if key != "evidence"})
    # Prefer the longest named match ("Subprime Cat" over a coin called "Cat").
    matches.sort(key=lambda row: max((len(normalize(row.get(field, ""))) for field in ("name", "symbol") if normalize(row.get(field, "")) in normalized), default=0), reverse=True)
    if matches:
        coin = matches[0]
        return {"status": "found", "coin": coin, "question": text if question and normalize(text) not in (normalize(coin.get("name", "")), normalize(coin.get("symbol", ""))) else DEFAULT_QUESTION,
                "rows": matches, "note": "Several coins share this name. Showing the best search match; use a mint to select another." if len(matches) > 1 else ""}
    return {"status": "missing", "coin": None, "question": text if question else DEFAULT_QUESTION, "rows": [], "message": NOT_FOUND}
