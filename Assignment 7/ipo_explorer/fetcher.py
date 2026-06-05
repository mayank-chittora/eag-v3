"""fetcher.py — Dynamic IPO data fetching for any date range.

Strategy (in order):
  1. NSE India JSON API via httpx with session cookie seeding
  2. crawl4ai Moneycontrol scrape (headless Chromium) as fallback
  3. Empty list — caller merges with static corpus
"""

from __future__ import annotations

import re
from datetime import datetime

import httpx

from corpus import IPORecord

_NSE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
}

_NSE_API = "https://www.nseindia.com/api/ipo-past-issues?category=mainboard"
_NSE_HOME = "https://www.nseindia.com"
_NSE_REFERER = "https://www.nseindia.com/market-data/all-upcoming-issues-ipo"

_MC_IPO_URL = "https://www.moneycontrol.com/ipo/"

# CORPUS max date — anything beyond this is fetched live
CORPUS_MAX_DATE = "2024-11-13"


def _parse_nse_date(s: str) -> str | None:
    """Convert 'DD-Mon-YYYY' or 'YYYY-MM-DD' to 'YYYY-MM-DD'. Returns None on failure."""
    if not s:
        return None
    s = s.strip()
    for fmt in ("%d-%b-%Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return None


def _nse_raw_to_record(item: dict) -> IPORecord | None:
    """Map one NSE API dict to an IPORecord. Returns None if essential fields are missing."""
    listing_date = _parse_nse_date(
        item.get("listingDate") or item.get("listing_date") or ""
    )
    if not listing_date:
        return None

    symbol = (item.get("symbol") or item.get("companyName", "")).strip().upper()
    company = (item.get("companyName") or symbol).strip()
    if not company:
        return None

    try:
        issue_price = float(str(item.get("issuePrice") or "0").replace(",", "").replace("₹", "").strip() or "0")
    except ValueError:
        issue_price = 0.0

    try:
        listing_price = float(str(item.get("listingPrice") or item.get("listing_price") or "0").replace(",", "").replace("₹", "").strip() or "0")
    except ValueError:
        listing_price = issue_price  # fallback

    sector = (item.get("sector") or item.get("industry") or "Unknown").strip()

    wiki_slug = company.replace(" ", "_")
    return IPORecord(
        symbol=symbol or company.split()[0].upper(),
        company=company,
        sector=sector,
        ipo_date=listing_date,
        issue_price=issue_price,
        listing_price=listing_price,
        website_url=f"https://www.google.com/search?q={company.replace(' ', '+')}+IPO",
        wikipedia_url=f"https://en.wikipedia.org/wiki/{wiki_slug}",
        description=(
            f"{company} is an Indian company listed on NSE/BSE. "
            f"IPO date: {listing_date}. Sector: {sector}."
        ),
    )


async def _fetch_nse_api() -> list[dict]:
    """Fetch mainboard IPO list from NSE India JSON API with cookie seeding."""
    try:
        async with httpx.AsyncClient(
            headers=_NSE_HEADERS,
            follow_redirects=True,
            timeout=30,
        ) as c:
            # Seed session cookies by visiting the homepage first
            await c.get(_NSE_HOME)
            r = await c.get(_NSE_API, headers={"Referer": _NSE_REFERER})
            if r.status_code != 200:
                return []
            data = r.json()
            # NSE returns either {"data": [...]} or a list directly
            if isinstance(data, list):
                return data
            return data.get("data") or []
    except Exception as e:
        print(f"[fetcher] NSE API failed: {e!r}")
        return []


async def _fetch_moneycontrol() -> list[dict]:
    """Fallback: scrape Moneycontrol IPO page via crawl4ai headless browser."""
    try:
        from crawl4ai import AsyncWebCrawler

        import os
        saved_fd = os.dup(1)
        os.dup2(2, 1)
        try:
            async with AsyncWebCrawler(verbose=False) as crawler:
                result = await crawler.arun(url=_MC_IPO_URL)
        finally:
            os.dup2(saved_fd, 1)
            os.close(saved_fd)

        md = result.markdown
        text = str(
            getattr(md, "raw_markdown", None)
            or getattr(md, "fit_markdown", None)
            or md
            or result.cleaned_html
            or ""
        )
        return _parse_moneycontrol_markdown(text)
    except Exception as e:
        print(f"[fetcher] Moneycontrol scrape failed: {e!r}")
        return []


def _parse_moneycontrol_markdown(text: str) -> list[dict]:
    """Extract IPO rows from crawl4ai markdown output of Moneycontrol IPO page.

    Moneycontrol renders a table with columns like:
      Company | Open Date | Close Date | Issue Price | Listing Date | Listing Price
    crawl4ai converts this to a markdown table; we parse each row.
    """
    records = []
    # Match markdown table rows: | col | col | ...
    rows = re.findall(r"^\|(.+)\|$", text, re.MULTILINE)
    if len(rows) < 2:
        return records

    # First non-separator row is the header
    header_row = [c.strip().lower() for c in rows[0].split("|")]

    def _col(row_cells: list[str], *names: str) -> str:
        for name in names:
            for i, h in enumerate(header_row):
                if name in h and i < len(row_cells):
                    return row_cells[i].strip()
        return ""

    for row in rows[1:]:
        if re.match(r"^[-| ]+$", row):
            continue  # separator row
        cells = [c.strip() for c in row.split("|")]
        company = _col(cells, "company", "name", "ipo")
        if not company or len(company) < 3:
            continue
        listing_date = _parse_nse_date(_col(cells, "listing", "list date"))
        open_date = _parse_nse_date(_col(cells, "open", "start"))
        date = listing_date or open_date
        if not date:
            continue
        records.append({
            "companyName": company,
            "symbol": company.split()[0].upper(),
            "listingDate": date,
            "issuePrice": _col(cells, "issue price", "price"),
            "listingPrice": _col(cells, "listing price", "list price"),
            "sector": "Unknown",
        })
    return records


def _to_ipo_records(raw: list[dict], start_date: str, end_date: str) -> list[IPORecord]:
    """Convert raw API/scrape dicts to IPORecord, filtered to [start_date, end_date]."""
    out = []
    for item in raw:
        rec = _nse_raw_to_record(item)
        if rec and start_date <= rec.ipo_date <= end_date:
            out.append(rec)
    return out


async def fetch_mainboard_ipos() -> list[dict]:
    """Fetch mainboard IPO raw dicts. Tries NSE API first, Moneycontrol fallback."""
    raw = await _fetch_nse_api()
    if not raw:
        print("[fetcher] NSE API returned empty — trying Moneycontrol fallback")
        raw = await _fetch_moneycontrol()
    print(f"[fetcher] fetched {len(raw)} raw IPO records from web")
    return raw
