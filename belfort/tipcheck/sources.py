"""Data Tip Check reads: NSE's daily regulatory-indicator file and a local copy of SEBI's adviser and analyst registers.

NSE publishes `REG1_IND<ddmmyy>.csv` after each session on nsearchives.nseindia.com, the same public host the app
already reads bhavcopies from. It has one row per symbol and one column per surveillance measure (GSM, ASM, ESM, NSE's
flags for SMS and social media tips, and more). SEBI has no public download for its registers, so Belfort keeps a
local snapshot that the user can refresh from SEBI's site (see `register.py`). Tests replace both functions.
"""

import csv
import io
import json
from datetime import date, timedelta

import httpx

from .. import settings
from ..data import market
from ..data.cache import cached

REG_IND_URL = "https://nsearchives.nseindia.com/content/cm/REG1_IND{d}.csv"
HEADERS = {"User-Agent": "stock-analyst/0.1"}
REGISTER_FILE = "sebi_register.json"


def parse_reg_ind(text: str) -> dict[str, dict]:
    """Symbol to {column: value}. Where a symbol trades in several series, the EQ row wins."""
    rows: dict[str, dict] = {}
    for row in csv.DictReader(io.StringIO(text)):
        sym = (row.get("Symbol") or "").strip().upper()
        if not sym:
            continue
        clean = {(k or "").strip(): (v or "").strip() for k, v in row.items() if k}
        if sym not in rows or clean.get("Series") == "EQ":
            rows[sym] = clean
    return rows


def _fetch_reg_ind(day: date) -> str | None:
    r = httpx.get(REG_IND_URL.format(d=day.strftime("%d%m%y")), headers=HEADERS, timeout=8.0, follow_redirects=True)
    if r.status_code != 200 or "Symbol" not in r.text[:200]:
        return None
    return r.text


def surveillance_rows() -> tuple[dict | None, str | None]:
    """(rows, as-of date) from NSE's newest regulatory-indicator file, or (None, None) when none could be fetched."""
    day, tried = date.fromisoformat(market.data_day()), 0
    while tried < settings.TIP_SURVEILLANCE_LOOKBACK_DAYS:
        if day.weekday() < 5:
            tried += 1

            def load(d=day):
                text = _fetch_reg_ind(d)
                if not text:
                    raise LookupError(d)  # not published (yet, or a holiday): try the day before, and cache nothing
                return parse_reg_ind(text)

            try:
                return cached(f"reg1ind:{day.isoformat()}", 24 * 3600, load), day.isoformat()
            except LookupError:
                pass
            except httpx.HTTPError:
                return None, None  # offline: do not walk back through every day
        day -= timedelta(days=1)
    return None, None


def sebi_register() -> tuple[dict | None, str | None]:
    """(number to {"name", "kind"}, as-of date) from the local snapshot, or (None, None) when there is none."""
    path = settings.DATA_DIR / REGISTER_FILE
    if not path.exists():
        return None, None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data["entries"], data["as_of"]
    except (ValueError, KeyError, OSError):
        return None, None
