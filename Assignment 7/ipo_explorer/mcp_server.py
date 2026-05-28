"""IPO Explorer MCP server.

Extends the agent_core MCP server with one additional tool: index_ipo_company.
All 11 original tools are re-registered. agent_core modules are imported via
sys.path — no file duplication.

Architectural compliance: Perception's SYSTEM prompt contains zero MCP tool
names. The index_ipo_company docstring teaches Decision when to call it.
Grep test: grep 'index_ipo_company' ../agent_core/perception.py → zero matches.

Run standalone (for MCP protocol over stdio):
    python mcp_server.py
"""

from __future__ import annotations

import json
import os
import sys
import threading
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx
from mcp.server.fastmcp import FastMCP

# ── State isolation ──────────────────────────────────────────────────────────
_HERE = Path(__file__).parent
_S7 = _HERE.parent / "agent_core"
_STATE = _HERE / "state"
_STATE.mkdir(parents=True, exist_ok=True)
(_STATE / "artifacts").mkdir(exist_ok=True)

sys.path.insert(0, str(_S7))

import memory as _memory        # noqa: E402
import artifacts as _artifacts  # noqa: E402

_memory.STATE_PATH = _STATE / "memory.json"
_memory.STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
_artifacts.STORE = _STATE / "artifacts"
_artifacts.STORE.mkdir(exist_ok=True)

# Import helpers from agent_core's mcp_server (crawl4ai fetch, chunking, etc.)
import mcp_server as _s7mcp  # noqa: E402

from dotenv import load_dotenv  # noqa: E402
from ddgs import DDGS           # noqa: E402

load_dotenv(_HERE.parent / ".env")

# IPO corpus for index_ipo_company
from corpus import get_by_symbol  # noqa: E402

mcp = FastMCP("ipo-rag-server")

SANDBOX = _S7 / "sandbox"
SANDBOX.mkdir(exist_ok=True)

USAGE_PATH = _HERE / "usage.json"
MONTHLY_CAP = 950
_usage_lock = threading.Lock()

MAX_SEARCH_RESULTS = 5


def _safe(path: str) -> Path:
    p = (SANDBOX / path).resolve()
    base = SANDBOX.resolve()
    if p != base and base not in p.parents:
        raise ValueError(f"Path '{path}' escapes the sandbox")
    return p


def _empty_usage(month: str) -> dict:
    return {
        "month": month,
        "tavily": {"count": 0, "errors": 0},
        "duckduckgo": {"count": 0, "errors": 0},
    }


def _load_usage() -> dict:
    month = datetime.now().strftime("%Y-%m")
    if not USAGE_PATH.exists():
        return _empty_usage(month)
    try:
        data = json.loads(USAGE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return _empty_usage(month)
    if data.get("month") != month:
        return _empty_usage(month)
    for k in ("tavily", "duckduckgo"):
        data.setdefault(k, {"count": 0, "errors": 0})
    return data


def _save_usage(data: dict) -> None:
    USAGE_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _bump(provider: str, field: str = "count") -> None:
    with _usage_lock:
        data = _load_usage()
        data[provider][field] = data[provider].get(field, 0) + 1
        _save_usage(data)


def _under_cap(provider: str) -> bool:
    return _load_usage()[provider]["count"] < MONTHLY_CAP


def _tavily_search(query: str, max_results: int) -> list[dict]:
    from tavily import TavilyClient
    client = TavilyClient(os.environ["TAVILY_API_KEY"])
    resp = client.search(query=query, max_results=max_results, search_depth="advanced")
    return [
        {"title": r.get("title", ""), "url": r.get("url", ""), "snippet": r.get("content", "")}
        for r in resp.get("results", [])
    ]


def _ddg_search(query: str, max_results: int) -> list[dict]:
    hits: list[dict] = []
    with DDGS() as ddgs:
        for backend in ("auto", "html", "lite"):
            try:
                hits = list(ddgs.text(query, max_results=max_results, backend=backend))
            except Exception:
                hits = []
            if hits:
                break
    return [
        {"title": h.get("title", ""), "url": h.get("href", ""), "snippet": h.get("body", "")}
        for h in hits
    ]


# ── Re-register all 11 original agent_core tools ────────────────────────────

@mcp.tool()
def web_search(query: str, max_results: int = 5) -> list[dict]:
    """Search the web (Tavily primary, DDG fallback). Hard-capped at 5 results."""
    max_results = max(1, min(max_results, MAX_SEARCH_RESULTS))
    if os.environ.get("TAVILY_API_KEY") and _under_cap("tavily"):
        try:
            results = _tavily_search(query, max_results)
            if results:
                _bump("tavily")
                return results
        except Exception:
            _bump("tavily", "errors")
    results = _ddg_search(query, max_results)
    _bump("duckduckgo")
    return results


@mcp.tool()
async def fetch_url(url: str, timeout: int = 20) -> dict:
    """Fetch clean markdown from a URL via crawl4ai (headless Chromium)."""
    return await _s7mcp._crawl4ai_fetch(url)


@mcp.tool()
def get_time(timezone: str = "UTC") -> dict:
    """Current time in a named IANA timezone. Example: get_time('Asia/Kolkata')."""
    tz = ZoneInfo(timezone)
    now = datetime.now(tz)
    offset = now.utcoffset()
    offset_hours = offset.total_seconds() / 3600 if offset else 0.0
    return {
        "iso": now.isoformat(),
        "human": now.strftime("%A, %d %B %Y %H:%M:%S %Z"),
        "timezone": timezone,
        "offset_hours": offset_hours,
    }


@mcp.tool()
def currency_convert(amount: float, from_currency: str, to_currency: str) -> dict:
    """Convert money between ISO-3 currencies via frankfurter.dev."""
    f = from_currency.upper()
    t = to_currency.upper()
    url = f"https://api.frankfurter.dev/v1/latest?amount={amount}&base={f}&symbols={t}"
    with httpx.Client(timeout=20, follow_redirects=True) as client:
        r = client.get(url)
        r.raise_for_status()
        data = r.json()
    converted = data["rates"][t]
    return {
        "amount": amount, "from": f, "to": t,
        "rate": converted / amount if amount else 0.0,
        "converted": converted, "date": data["date"],
        "source": "frankfurter.dev",
    }


@mcp.tool()
def read_file(path: str) -> dict:
    """Read a UTF-8 text file from the sandbox."""
    p = _safe(path)
    text = p.read_text(encoding="utf-8")
    return {"path": path, "size_bytes": p.stat().st_size, "content": text, "encoding": "utf-8"}


@mcp.tool()
def list_dir(path: str = ".") -> dict:
    """List a directory inside the sandbox."""
    p = _safe(path)
    entries, names = [], []
    for child in sorted(p.iterdir()):
        is_dir = child.is_dir()
        entries.append({"name": child.name, "type": "dir" if is_dir else "file",
                        "size_bytes": 0 if is_dir else child.stat().st_size})
        names.append(child.name)
    return {"path": path, "count": len(entries), "names": names, "entries": entries}


@mcp.tool()
def create_file(path: str, content: str) -> dict:
    """Create a new file in the sandbox; errors if it exists."""
    p = _safe(path)
    if p.exists():
        raise ValueError(f"File '{path}' already exists")
    if not p.parent.exists():
        raise ValueError(f"Parent directory of '{path}' does not exist")
    p.write_text(content, encoding="utf-8")
    return {"ok": True, "path": path, "size_bytes": p.stat().st_size}


@mcp.tool()
def update_file(path: str, content: str) -> dict:
    """Overwrite an existing sandbox file."""
    p = _safe(path)
    if not p.exists():
        raise ValueError(f"File '{path}' does not exist")
    p.write_text(content, encoding="utf-8")
    return {"ok": True, "path": path, "size_bytes": p.stat().st_size}


@mcp.tool()
def edit_file(path: str, find: str, replace: str, replace_all: bool = False) -> dict:
    """Find-and-replace inside a sandbox file."""
    p = _safe(path)
    text = p.read_text(encoding="utf-8")
    count = text.count(find)
    if count == 0:
        raise ValueError(f"'{find}' not found in '{path}'")
    if count > 1 and not replace_all:
        raise ValueError(f"'{find}' occurs {count} times; pass replace_all=True")
    new_text = text.replace(find, replace) if replace_all else text.replace(find, replace, 1)
    p.write_text(new_text, encoding="utf-8")
    return {"ok": True, "path": path, "replacements": count if replace_all else 1,
            "size_bytes": p.stat().st_size}


@mcp.tool()
def index_document(path: str, chunk_size: int = 400, overlap: int = 80) -> dict:
    """Chunk a sandbox file or artifact and write each chunk into Memory as a searchable fact.
    Use when content must remain retrievable across later turns or runs.
    For one-shot inspection, prefer read_file instead."""
    text, source = _s7mcp._read_for_index(path)
    if not text.strip():
        return {"path": path, "source": source, "chunks_indexed": 0, "warning": "empty content"}
    chunks = _s7mcp._chunk_text(text, size=chunk_size, overlap=overlap)
    run_id = f"index-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    indexed = 0
    for i, chunk in enumerate(chunks):
        preview = chunk[:120].replace("\n", " ")
        descriptor = f"[{source} chunk {i+1}/{len(chunks)}] {preview}"
        _memory.add_fact(
            descriptor=descriptor,
            value={"chunk": chunk, "chunk_index": i, "total_chunks": len(chunks), "source": source},
            source=source, run_id=run_id,
        )
        indexed += 1
    return {"path": path, "source": source, "chunks_indexed": indexed,
            "chunk_size": chunk_size, "overlap": overlap}


@mcp.tool()
def search_knowledge(query: str, k: int = 5) -> list[dict]:
    """Vector search over indexed fact chunks. Returns up to k ranked chunks with provenance.
    Call this rather than re-fetching URLs or re-reading files whenever Memory already
    contains indexed chunks for the topic — that is the whole point of having indexed the corpus."""
    items = _memory.read(query, kinds=["fact"], top_k=k)
    return [
        {
            "id": item.id,
            "descriptor": item.descriptor,
            "source": item.source,
            "chunk_preview": (item.value.get("chunk") or "")[:300],
            "metadata": {k_: v for k_, v in item.value.items() if k_ != "chunk"},
        }
        for item in items
    ]


# ── New IPO-specific tool ─────────────────────────────────────────────────────

@mcp.tool()
async def index_ipo_company(symbol: str) -> dict:
    """Fetch and index a specific IPO company's web pages into Memory as searchable fact chunks.
    Use when asked to load, index, or make searchable a company from the IPO corpus.
    symbol must be an uppercase ticker (e.g. 'PAYTM', 'ZOMATO', 'NYKAA').
    Fetches the company homepage and Wikipedia page, chunks the content, and writes
    the chunks into vector memory so they can be retrieved via search_knowledge later.
    Returns chunks_indexed and metadata_stored counts."""
    record = get_by_symbol(symbol.upper())
    if record is None:
        return {"error": f"Symbol '{symbol}' not found in IPO corpus", "chunks_indexed": 0}

    run_id = f"ipo-{symbol.lower()}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    total_chunks = 0

    # Write IPO metadata as a structured fact first
    meta_descriptor = (
        f"[ipo_metadata:{record.symbol}] {record.company} | Sector: {record.sector} | "
        f"IPO Date: {record.ipo_date} | Issue Price: ₹{record.issue_price} | "
        f"Listing Price: ₹{record.listing_price} | "
        f"Listing Gain: {((record.listing_price - record.issue_price) / record.issue_price * 100):.1f}%"
    )
    _memory.add_fact(
        descriptor=meta_descriptor,
        value={
            "symbol": record.symbol,
            "company": record.company,
            "sector": record.sector,
            "ipo_date": record.ipo_date,
            "issue_price": record.issue_price,
            "listing_price": record.listing_price,
            "listing_gain_pct": round(
                (record.listing_price - record.issue_price) / record.issue_price * 100, 2
            ),
            "description": record.description,
        },
        keywords=[record.symbol.lower(), record.company.lower()[:20], record.sector.lower(),
                  "ipo", "listing", "price"],
        source=f"ipo_metadata:{record.symbol}",
        run_id=run_id,
    )
    # Also index the description as a standalone chunk for semantic recall
    desc_descriptor = f"[ipo:{record.symbol} description] {record.description[:120]}"
    _memory.add_fact(
        descriptor=desc_descriptor,
        value={"chunk": record.description, "source": f"ipo:{record.symbol}",
               "company": record.company, "sector": record.sector},
        keywords=[record.symbol.lower(), record.sector.lower(), "ipo"],
        source=f"ipo:{record.symbol}",
        run_id=run_id,
    )
    total_chunks += 1

    # Fetch and index the company website
    pages_fetched = 0
    for url_label, url in [("website", record.website_url), ("wikipedia", record.wikipedia_url)]:
        try:
            result = await _s7mcp._crawl4ai_fetch(url)
            text = result.get("text", "")
            if not text.strip():
                continue
            chunks = _s7mcp._chunk_text(text, size=400, overlap=80)
            source_label = f"ipo:{record.symbol}:{url_label}"
            for i, chunk in enumerate(chunks):
                preview = chunk[:120].replace("\n", " ")
                descriptor = f"[{source_label} chunk {i+1}/{len(chunks)}] {preview}"
                _memory.add_fact(
                    descriptor=descriptor,
                    value={"chunk": chunk, "chunk_index": i, "total_chunks": len(chunks),
                           "source": source_label, "company": record.company,
                           "sector": record.sector, "symbol": record.symbol},
                    source=source_label,
                    run_id=run_id,
                )
                total_chunks += 1
            pages_fetched += 1
        except Exception as e:
            print(f"[index_ipo_company] fetch failed for {url}: {e!r}")

    return {
        "symbol": record.symbol,
        "company": record.company,
        "pages_fetched": pages_fetched,
        "chunks_indexed": total_chunks,
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
