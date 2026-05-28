"""server.py — FastAPI backend for the IPO RAG chatbot.

Endpoints:
  GET  /                        serves static/index.html
  POST /api/index               start indexing job, returns {job_id, ipo_count, cached}
  GET  /api/index/{job_id}/stream  SSE stream for indexing progress
  POST /api/query               SSE stream of agent iteration events
  GET  /api/state               current index state {indexed, companies, chunks}
  GET  /api/corpus              full IPO list

Run:
  uvicorn server:app --port 8200 --reload
"""

from __future__ import annotations

import asyncio
import json
import sys
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# ── Path setup ───────────────────────────────────────────────────────────────
_HERE = Path(__file__).parent
_S7 = _HERE.parent / "agent_core"
sys.path.insert(0, str(_S7))

from gateway import ensure_gateway  # noqa: E402

from corpus import CORPUS, filter_by_timeframe  # noqa: E402
from indexer import (  # noqa: E402
    get_cached_stats,
    index_corpus,
    is_cached,
    _save_indexed_timeframe,
    _load_indexed_timeframes,
)

_STATIC = _HERE / "static"
_STATE = _HERE / "state"

# In-memory job queues: job_id → asyncio.Queue of event dicts
_index_jobs: dict[str, asyncio.Queue] = {}
# In-memory session history: session_id → list[dict]
_sessions: dict[str, list[dict]] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_gateway()
    yield


app = FastAPI(title="IPO RAG", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(_STATIC)), name="static")


# ── Request / Response models ─────────────────────────────────────────────────

class IndexRequest(BaseModel):
    start_year: int = 2022
    end_year: int = 2024


class QueryRequest(BaseModel):
    query: str
    session_id: str = ""


# ── SSE helpers ───────────────────────────────────────────────────────────────

def _sse(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"


async def _drain_queue(q: asyncio.Queue, timeout: float = 300.0) -> AsyncIterator[str]:
    """Yield SSE-formatted strings from queue until a 'done' event or timeout."""
    while True:
        try:
            event = await asyncio.wait_for(q.get(), timeout=timeout)
        except asyncio.TimeoutError:
            yield _sse({"event": "error", "message": "timeout"})
            return
        yield _sse(event)
        if event.get("event") in ("done", "error"):
            return


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return FileResponse(str(_STATIC / "index.html"))


@app.get("/api/state")
async def get_state():
    """Return current index state."""
    all_timeframes = _load_indexed_timeframes()
    if not all_timeframes:
        return {"indexed": False, "companies": 0, "chunks": 0, "timeframes": []}

    # Aggregate across all indexed timeframes
    total_companies = sum(v.get("companies_indexed", 0) for v in all_timeframes.values())
    total_chunks = sum(v.get("total_chunks", 0) for v in all_timeframes.values())
    return {
        "indexed": True,
        "companies": total_companies,
        "chunks": total_chunks,
        "timeframes": list(all_timeframes.keys()),
    }


@app.get("/api/corpus")
async def get_corpus():
    """Full IPO corpus manifest."""
    return [
        {
            "symbol": r.symbol,
            "company": r.company,
            "sector": r.sector,
            "ipo_date": r.ipo_date,
            "issue_price": r.issue_price,
            "listing_price": r.listing_price,
            "listing_gain_pct": round(
                (r.listing_price - r.issue_price) / r.issue_price * 100, 2
            ),
            "website_url": r.website_url,
        }
        for r in CORPUS
    ]


@app.post("/api/index")
async def start_index(req: IndexRequest):
    """Start indexing IPOs for the given timeframe.

    Returns {job_id, ipo_count, cached}.
    If cached, no background task is started — frontend skips the stream.
    """
    records = filter_by_timeframe(req.start_year, req.end_year)
    if not records:
        raise HTTPException(400, f"No IPOs found for {req.start_year}–{req.end_year}")

    cached = is_cached(req.start_year, req.end_year)
    job_id = uuid.uuid4().hex[:12]

    if not cached:
        q: asyncio.Queue = asyncio.Queue()
        _index_jobs[job_id] = q

        def _progress_cb(symbol, company, pages, chunks, done, total):
            q.put_nowait({
                "event": "progress",
                "symbol": symbol,
                "company": company,
                "pages_fetched": pages,
                "chunks_written": chunks,
                "company_done": done,
                "company_total": total,
            })

        async def _run():
            try:
                stats = await index_corpus(records, progress_callback=_progress_cb)
                _save_indexed_timeframe(req.start_year, req.end_year, stats)
                q.put_nowait({
                    "event": "stats",
                    "companies_indexed": stats["companies_indexed"],
                    "pages_fetched": stats["pages_fetched"],
                    "total_chunks": stats["total_chunks"],
                })
            except Exception as e:
                q.put_nowait({"event": "error", "message": str(e)})
            finally:
                q.put_nowait({"event": "done"})

        asyncio.create_task(_run())

    return {"job_id": job_id, "ipo_count": len(records), "cached": cached}


@app.get("/api/index/{job_id}/stream")
async def index_stream(job_id: str):
    """SSE stream for indexing progress. Opens EventSource from frontend."""
    q = _index_jobs.get(job_id)
    if q is None:
        raise HTTPException(404, "Job not found")

    async def generate():
        async for chunk in _drain_queue(q):
            yield chunk
        _index_jobs.pop(job_id, None)

    return StreamingResponse(generate(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.post("/api/query")
async def query_agent(req: QueryRequest):
    """SSE stream of agent iteration events for a user query.

    Frontend uses fetch() + ReadableStream (not EventSource) because this is a POST.
    """
    if not req.query.strip():
        raise HTTPException(400, "Query cannot be empty")

    session_id = req.session_id or uuid.uuid4().hex[:8]
    q: asyncio.Queue = asyncio.Queue()

    def _callback(event: dict):
        q.put_nowait(event)

    async def _run():
        # Import here to ensure monkeypatches are in effect for this process
        import agent
        try:
            await agent.run(req.query, callback=_callback)
        except Exception as e:
            q.put_nowait({"event": "error", "message": str(e)})
            q.put_nowait({"event": "done", "answer": "", "iters": 0})

    asyncio.create_task(_run())

    async def generate():
        yield _sse({"event": "start", "query": req.query, "session_id": session_id})
        async for chunk in _drain_queue(q, timeout=600.0):
            yield chunk

    return StreamingResponse(generate(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
