"""ipo_indexer.py — Bootstrap indexing for the IPO corpus.

Indexes IPO company websites directly (no LLM, no agent loop) to avoid
burning LLM tokens on 60 sequential perception/decision iterations.

Run standalone:
    python ipo_indexer.py --years 2022-2024
    python ipo_indexer.py --years 2020-2024 --force   # re-index even if cached
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Callable

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

import mcp_server as _s7mcp    # noqa: E402

from corpus import IPORecord, filter_by_timeframe  # noqa: E402

_TIMEFRAME_FILE = _STATE / "indexed_timeframe.json"


def _load_indexed_timeframes() -> dict:
    if _TIMEFRAME_FILE.exists():
        try:
            return json.loads(_TIMEFRAME_FILE.read_text())
        except Exception:
            pass
    return {}


def _save_indexed_timeframe(start_date: str, end_date: str, stats: dict) -> None:
    data = _load_indexed_timeframes()
    key = f"{start_date}_{end_date}"
    data[key] = {**stats, "indexed_at": datetime.now().isoformat()}
    _TIMEFRAME_FILE.write_text(json.dumps(data, indent=2))


def is_cached(start_date: str, end_date: str) -> bool:
    key = f"{start_date}_{end_date}"
    return key in _load_indexed_timeframes()


def get_cached_stats(start_date: str, end_date: str) -> dict | None:
    key = f"{start_date}_{end_date}"
    return _load_indexed_timeframes().get(key)


async def _fetch_and_index_company(
    record: IPORecord,
    run_id: str,
) -> tuple[int, int]:
    """Returns (pages_fetched, chunks_indexed) for one company."""
    total_chunks = 0

    # IPO metadata fact
    listing_gain = (record.listing_price - record.issue_price) / record.issue_price * 100
    meta_descriptor = (
        f"[ipo_metadata:{record.symbol}] {record.company} | Sector: {record.sector} | "
        f"IPO Date: {record.ipo_date} | Issue Price: ₹{record.issue_price} | "
        f"Listing Price: ₹{record.listing_price} | Listing Gain: {listing_gain:.1f}%"
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
            "listing_gain_pct": round(listing_gain, 2),
            "description": record.description,
        },
        keywords=[record.symbol.lower(), record.sector.lower(), "ipo", "listing", "price"],
        source=f"ipo_metadata:{record.symbol}",
        run_id=run_id,
    )

    # Description as a semantic anchor chunk
    _memory.add_fact(
        descriptor=f"[ipo:{record.symbol} description] {record.description[:120]}",
        value={"chunk": record.description, "source": f"ipo:{record.symbol}",
               "company": record.company, "sector": record.sector, "symbol": record.symbol},
        keywords=[record.symbol.lower(), record.sector.lower(), "ipo"],
        source=f"ipo:{record.symbol}",
        run_id=run_id,
    )
    total_chunks += 1

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
                    value={
                        "chunk": chunk, "chunk_index": i, "total_chunks": len(chunks),
                        "source": source_label, "company": record.company,
                        "sector": record.sector, "symbol": record.symbol,
                    },
                    source=source_label,
                    run_id=run_id,
                )
                total_chunks += 1
            pages_fetched += 1
        except Exception as e:
            print(f"  [warn] fetch failed for {record.symbol} {url_label} ({e!r})")

    return pages_fetched, total_chunks


ProgressCallback = Callable[[str, str, int, int, int, int], None] | None
# args: symbol, company, pages_fetched, chunks_written, done_count, total_count


async def index_corpus(
    records: list[IPORecord],
    progress_callback: ProgressCallback = None,
    force: bool = False,
) -> dict:
    """Index all records into memory. Sequential to avoid Chromium resource exhaustion.

    Returns {companies_indexed, pages_fetched, total_chunks}.
    """
    run_id = f"ipo-corpus-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    total_companies = len(records)
    companies_done = 0
    total_pages = 0
    total_chunks = 0

    for record in records:
        pages, chunks = await _fetch_and_index_company(record, run_id)
        companies_done += 1
        total_pages += pages
        total_chunks += chunks
        print(f"  [{companies_done}/{total_companies}] {record.symbol}: {pages} pages, {chunks} chunks")
        if progress_callback:
            progress_callback(
                record.symbol, record.company,
                pages, chunks,
                companies_done, total_companies,
            )

    return {
        "companies_indexed": companies_done,
        "pages_fetched": total_pages,
        "total_chunks": total_chunks,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Bootstrap IPO corpus index")
    parser.add_argument(
        "--years", default="2022-2024",
        help="Year range in format START-END, e.g. 2022-2024",
    )
    parser.add_argument("--force", action="store_true", help="Re-index even if cached")
    args = parser.parse_args()

    try:
        start_str, end_str = args.years.split("-")
        start_year, end_year = int(start_str), int(end_str)
    except ValueError:
        print(f"Invalid --years format: {args.years!r}. Use e.g. 2022-2024")
        sys.exit(1)

    records = filter_by_timeframe(start_year, end_year)
    print(f"IPO corpus: {len(records)} companies from {start_year} to {end_year}")

    if not args.force and is_cached(start_year, end_year):
        cached = get_cached_stats(start_year, end_year)
        print(f"Already indexed: {cached}")
        return

    from gateway import ensure_gateway
    ensure_gateway()

    print(f"Indexing {len(records)} companies...")
    stats = asyncio.run(index_corpus(records))
    _save_indexed_timeframe(start_year, end_year, stats)
    print(
        f"\nDone: {stats['companies_indexed']} companies | "
        f"{stats['pages_fetched']} pages | "
        f"{stats['total_chunks']} chunks"
    )


if __name__ == "__main__":
    main()
