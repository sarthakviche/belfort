"""Three screens built by fixed, visible criteria. They are filters over public data, not tips.

  large   - the built-in Nifty 50 list (large caps), with where each one stands today
  growth  - mid and small caps with an uptrend and growing, profitable business figures
  value   - large and mid caps priced below their sector on P/E and moving in a narrow range

Company-size bands use approximate market-value cut-offs, stated in the output.
"""

import threading
import time
import warnings
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import numpy as np
import pandas as pd

from ..data.cache import cached
from ..data.providers import YahooProvider
from ..settings import STYLES
from .analysis.pivots import find_pivots
from .analysis.structure import trend_state

warnings.filterwarnings("ignore")

# Fallback when NSE's official list cannot be fetched: the Nifty 50 as published by NSE Indices on 2026-11-26.
NIFTY_AS_OF = "2026-11-26"
NIFTY = [
    "ADANIENT",
    "ADANIPORTS",
    "APOLLOHOSP",
    "ASIANPAINT",
    "AXISBANK",
    "BAJAJ-AUTO",
    "BAJAJFINSV",
    "BAJFINANCE",
    "BEL",
    "BHARTIARTL",
    "BSE",
    "CIPLA",
    "COALINDIA",
    "DRREDDY",
    "EICHERMOT",
    "ETERNAL",
    "GRASIM",
    "HCLTECH",
    "HDFCBANK",
    "HDFCLIFE",
    "HINDALCO",
    "HINDUNILVR",
    "ICICIBANK",
    "INDIGO",
    "INFY",
    "ITC",
    "JIOFIN",
    "JSWSTEEL",
    "KOTAKBANK",
    "LT",
    "M&M",
    "MARUTI",
    "MAXHEALTH",
    "NESTLEIND",
    "NTPC",
    "ONGC",
    "POWERGRID",
    "RELIANCE",
    "SBILIFE",
    "SBIN",
    "SHRIRAMFIN",
    "SUNPHARMA",
    "TATACONSUM",
    "TATASTEEL",
    "TCS",
    "TECHM",
    "TITAN",
    "TMPV",
    "TRENT",
    "ULTRACEMCO",
]

BROADER = [
    "PERSISTENT",
    "COFORGE",
    "MPHASIS",
    "LTTS",
    "KPITTECH",
    "TATAELXSI",
    "DIXON",
    "POLYCAB",
    "KEI",
    "CUMMINSIND",
    "ABB",
    "SIEMENS",
    "BHEL",
    "HAL",
    "BDL",
    "MAZDOCK",
    "COCHINSHIP",
    "IRCTC",
    "IRFC",
    "RVNL",
    "NHPC",
    "SJVN",
    "SUZLON",
    "TATAPOWER",
    "JSWENERGY",
    "FEDERALBNK",
    "IDFCFIRSTB",
    "AUBANK",
    "BANKBARODA",
    "PNB",
    "CANBK",
    "MUTHOOTFIN",
    "CHOLAFIN",
    "LICHSGFIN",
    "LUPIN",
    "AUROPHARMA",
    "ALKEM",
    "TORNTPHARM",
    "LAURUSLABS",
    "GLENMARK",
    "ASHOKLEY",
    "TVSMOTOR",
    "BALKRISIND",
    "MRF",
    "APOLLOTYRE",
    "EXIDEIND",
    "PIIND",
    "UPL",
    "DEEPAKNTR",
    "SRF",
    "AARTIIND",
    "TATACHEM",
    "VOLTAS",
    "HAVELLS",
    "CROMPTON",
    "PAGEIND",
    "JUBLFOOD",
    "MARICO",
    "DABUR",
    "COLPAL",
    "GODREJCP",
    "INDHOTEL",
    "PVRINOX",
    "SAIL",
    "NMDC",
    "JINDALSTEL",
    "NATIONALUM",
    "VEDL",
    "OBEROIRLTY",
    "DLF",
    "GODREJPROP",
    "PRESTIGE",
    "CDSL",
    "BSE",
    "CAMS",
    "ANGELONE",
    "KAYNES",
    "IEX",
    "NBCC",
    "IREDA",
    "HUDCO",
    "IOC",
    "BPCL",
    "DIVISLAB",
    "BRITANNIA",
]

LARGE_CR, MID_CR = 100000, 30000  # approximate market-value bands in ₹ crore
CR = 1e7
_state = {"data": None, "building": False, "error": None}
_lock = threading.Lock()
_yp = YahooProvider()


def _download(symbols: list[str]) -> dict[str, pd.DataFrame]:
    import yfinance as yf

    raw = yf.download(
        [s + ".NS" for s in symbols], period="1y", auto_adjust=False, group_by="ticker", threads=True, progress=False
    )
    out = {}
    for s in symbols:
        try:
            df = raw[s + ".NS"].rename(columns=str.lower)[["open", "high", "low", "close", "volume"]].dropna()
            if len(df) >= 120:
                df.index = pd.DatetimeIndex(df.index).tz_localize(None)
                out[s] = df
        except Exception:
            continue
    return out


def _row(sym: str, df: pd.DataFrame, info: dict | None) -> dict:
    c = df["close"]
    close = float(c.iloc[-1])
    st = STYLES["swing"]
    trend = trend_state(df, find_pivots(df["high"].values.astype(float), df["low"].values.astype(float), st.k), st)
    w = df.iloc[-60:]
    info = info or {}
    mcap = info.get("marketCap")
    cap_cr = mcap / CR if mcap else None
    size = None if cap_cr is None else "Large cap" if cap_cr >= LARGE_CR else "Mid cap" if cap_cr >= MID_CR else "Small cap"
    de = info.get("debtToEquity")
    sma200 = float(c.iloc[-200:].mean()) if len(c) >= 200 else None
    return {
        "symbol": sym,
        "name": info.get("shortName") or info.get("longName") or sym,
        "sector": info.get("sector"),
        "close": round(close, 2),
        "as_of": df.index[-1].strftime("%Y-%m-%d"),
        "chg_1d": round((close / float(c.iloc[-2]) - 1) * 100, 2),
        "chg_1m": round((close / float(c.iloc[-22]) - 1) * 100, 1),
        "chg_3m": round((close / float(c.iloc[-64]) - 1) * 100, 1),
        "from_high": round((close / float(df["high"].max()) - 1) * 100, 1),
        "range_60": round((float(w["high"].max()) / float(w["low"].min()) - 1) * 100, 1),
        "above_200": None if sma200 is None else bool(close >= sma200),
        "trend": trend["direction"],
        "phase": trend["phase"],
        "size": size,
        "mcap_cr": None if cap_cr is None else round(cap_cr),
        "pe": info.get("trailingPE"),
        "roe": None if info.get("returnOnEquity") is None else round(info["returnOnEquity"] * 100, 1),
        "sales_growth": None if info.get("revenueGrowth") is None else round(info["revenueGrowth"] * 100, 1),
        "de": None if de is None else round(de / 100, 2),
        "lender": info.get("sector") == "Financial Services",
    }


def nifty_members() -> tuple[list[str], str]:
    """Today's Nifty 50 from NSE Indices, or the built-in copy (with its date) when that cannot be fetched."""
    from ..research.analysis.pipeline import nse

    try:
        live = nse.nifty50()
    except Exception:
        live = None
    if live:
        return live, "NSE Indices' current Nifty 50 list"
    return list(NIFTY), f"Belfort's built-in copy of the Nifty 50 list from {NIFTY_AS_OF} (NSE's list could not be fetched)"


def build() -> dict:
    members, members_source = nifty_members()
    symbols = sorted(set(members + BROADER))
    frames = _download(symbols)
    with ThreadPoolExecutor(max_workers=6) as ex:
        infos = dict(zip(frames, ex.map(lambda s: _safe_info(s), frames), strict=False))
    rows = {s: _row(s, df, infos.get(s)) for s, df in frames.items()}
    with_info = [r for r in rows.values() if r["mcap_cr"]]

    order = {"up": 0, "sideways": 1, "down": 2}
    nifty = sorted([rows[s] for s in members if s in rows], key=lambda r: (order[r["trend"]], -r["chg_1m"]))
    missing = sorted(set(members) - set(rows))
    for r in nifty:
        r["why"] = f"Trend {r['trend']}{' (recent)' if r['phase'] == 'early' else ''}; {r['from_high']}% from its 1-year high."

    risky = [
        r
        for r in with_info
        if r["size"] in ("Mid cap", "Small cap")
        and r["trend"] == "up"
        and (r["sales_growth"] or 0) >= 10
        and (r["roe"] or 0) >= 12
        and (r["lender"] or (r["de"] is not None and r["de"] < 1.5))
    ]
    risky.sort(key=lambda r: -r["chg_3m"])
    for r in risky:
        r["why"] = (
            f"{r['size']}; uptrend; sales up {r['sales_growth']}% (latest quarter, year on year); "
            f"return on equity {r['roe']}%" + ("" if r["lender"] else f"; debt to equity {r['de']}") + "."
        )

    med = {}
    for sec in {r["sector"] for r in with_info if r["sector"]}:
        pes = [r["pe"] for r in with_info if r["sector"] == sec and r["pe"] and r["pe"] > 0]
        if len(pes) >= 4:
            med[sec] = float(np.median(pes))
    safer = []
    for r in with_info:
        m = med.get(r["sector"])
        if (
            r["size"] in ("Large cap", "Mid cap")
            and m
            and r["pe"]
            and 0 < r["pe"] < 0.9 * m
            and (r["roe"] or 0) >= 10
            and (r["lender"] or (r["de"] is not None and r["de"] < 1.0))
            and r["range_60"] <= 18
            and r["above_200"]
        ):
            r = dict(r)
            r["sector_pe"] = round(m, 1)
            r["why"] = (
                f"{r['size']}; P/E {r['pe']:.1f} against {m:.1f} for its sector here; return on equity {r['roe']}%; "
                f"price held inside a {r['range_60']}% range for 60 sessions and is above its 200-day average."
            )
            safer.append(r)
    safer.sort(key=lambda r: r["range_60"])

    as_of = max(r["as_of"] for r in rows.values()) if rows else None
    return {
        "status": "ready",
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "as_of": as_of,
        "source": "Yahoo Finance daily prices and key ratios",
        "coverage": f"{len(rows)} of {len(symbols)} built-in stocks returned prices; {len(with_info)} returned company ratios.",
        "note": (
            "These screens apply fixed criteria to end-of-day data. They are filters for your own study, not "
            "recommendations, and every stock on them can fall."
        ),
        "lists": {
            "large": {
                "title": "Large caps",
                "subtitle": "The companies in the Nifty 50 index",
                "criteria": f"All {len(members)} Nifty 50 companies from {members_source}, uptrends first."
                + (f" No price data for: {', '.join(missing)}." if missing else "")
                + " Large caps are usually steadier than smaller companies and "
                "have recovered from past falls more often, but they still fall. Index membership changes; the list is checked against NSE once a week.",
                "rows": nifty,
            },
            "growth": {
                "title": "Growth screen",
                "subtitle": "Mid and small caps with growing figures and an uptrend",
                "criteria": f"Market value under ₹{LARGE_CR:,} cr (approximate mid and small cap band), price in an uptrend, sales up at least 10% "
                "in the latest quarter, return on equity at least 12%, debt to equity under 1.5 (lenders exempt). "
                "Smaller companies can rise fast and fall just as fast. Keep position sizes small.",
                "rows": risky[:20],
            },
            "value": {
                "title": "Value screen",
                "subtitle": "Below their sector on P/E and trading in a narrow range",
                "criteria": f"Market value above ₹{MID_CR:,} cr, P/E at least 10% below the median of its sector within this app's stock list, return on equity at least 10%, "
                "debt to equity under 1 (lenders exempt), price inside an 18% range for 60 sessions and above its 200-day average. "
                "A narrow range can break upward or downward. Lower P/E than peers is not the same as low risk.",
                "rows": safer[:20],
            },
        },
    }


def _safe_info(sym: str) -> dict | None:
    try:
        return _yp.info(sym)
    except Exception:
        return None


def _run():
    try:
        data = cached("screens:" + datetime.now().strftime("%Y-%m-%d"), 6 * 3600, build, derived=True)
        _state.update(data=data, error=None)
    except Exception as e:  # network trouble: report it, allow a retry
        _state.update(error=f"The lists could not be built ({type(e).__name__}). Reload to try again.")
    finally:
        _state["building"] = False
        _state["built_at"] = time.time()


def get() -> dict:
    """Return the lists, starting a background build if needed."""
    with _lock:
        fresh = _state["data"] and time.time() - _state.get("built_at", 0) < 6 * 3600
        if not fresh and not _state["building"]:
            _state["building"] = True
            threading.Thread(target=_run, daemon=True).start()
    if _state["data"]:
        return _state["data"]
    if _state["error"] and not _state["building"]:
        return {"status": "error", "message": _state["error"]}
    return {"status": "building", "message": "Building the lists from live data. The first run takes up to a minute."}
