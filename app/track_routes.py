"""Small, independent pages and APIs for memory and the company brain."""
from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from . import brain, memory

router = APIRouter()
STATIC = Path(__file__).parent / "static" / "tracks"


@router.get("/memory")
def memory_page():
    return FileResponse(STATIC / "memory.html")


@router.get("/brain")
def brain_page():
    return FileResponse(STATIC / "brain.html")


@router.get("/track-assets/{asset}")
def track_asset(asset: str):
    if asset not in {"tracks.css", "tracks.js"}:
        raise HTTPException(404, "Unknown asset.")
    return FileResponse(STATIC / asset)


def _limited(req):
    from .main import limited, lookup_limit, ip
    limited(lookup_limit, ip(req))


@router.get("/api/memory")
async def memory_graph(req: Request, entity: str | None = None, session: str | None = None):
    _limited(req)
    session = session or (req.cookies.get("sniff_session") if not entity else None)
    if not entity and not session:
        return JSONResponse({"rows": [], "notes": [], "graph": {"nodes": [], "edges": []},
                             "note": "Investigate a coin in Sniff, or enter a coin or session to recall."},
                            headers={"Cache-Control": "no-store"})
    try:
        result = await asyncio.to_thread(memory.recall, entity=entity, session=session)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    except Exception:
        raise HTTPException(503, "Investigation memory is unavailable right now. Please try again later.")
    return JSONResponse(result, headers={"Cache-Control": "no-store"})


class BrainQuestion(BaseModel):
    question: str


@router.post("/api/brain/ask")
async def brain_ask(body: BrainQuestion, req: Request):
    from .main import same_origin
    same_origin(req)
    _limited(req)
    try:
        return await asyncio.to_thread(brain.ask, body.question)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    except Exception:
        raise HTTPException(503, "The company brain is unavailable right now. Please try again later.")


@router.get("/api/brain")
async def brain_status(req: Request):
    _limited(req)
    try:
        return await asyncio.to_thread(brain.status)
    except Exception:
        raise HTTPException(503, "The company brain is unavailable right now. Please try again later.")
