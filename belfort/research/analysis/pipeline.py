"""Run the whole analysis for one symbol and style and return a JSON-ready report."""

import json
import math
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import date

import numpy as np
import pandas as pd

from ...core.compliance import DISCLAIMER
from ...data import symbols
from ...data.providers import DataError, NseArchiveProvider, YahooProvider, clean_symbol
from ...data.universe import LENDER_SECTORS, SECTOR_OF, peers_of
from ...settings import (
    FUND_SOURCE,
    LEVEL_LOOKBACK_BARS,
    MOMENTUM_CHART_BARS,
    PRICE_SOURCE,
    PROFILE_MAX_CHARS,
    STATS_FILE,
    STYLES,
    WEEKLY_FAST,
    WEEKLY_SLOW,
)
from . import context, explain, fundamentals, sizing, verdict
from .indicators import atr as atr_series
from .indicators import macd, rsi, sma
from .patterns import Ctx, detect_all
from .pivots import find_pivots
from .structure import fibonacci, find_levels, trend_state, volume_read

prices = YahooProvider()
nse = NseArchiveProvider()
_pool = ThreadPoolExecutor(max_workers=8)


def _safe(fn, *a):
    try:
        return fn(*a)
    except Exception as e:  # a failed side-fetch must never break the report
        return e


def _clean(o):
    """Make the report JSON-safe: numpy types to Python, NaN to None."""
    if isinstance(o, dict):
        return {k: _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    if isinstance(o, (np.floating, float)):
        return None if math.isnan(float(o)) or math.isinf(float(o)) else float(o)
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.bool_):
        return bool(o)
    if isinstance(o, (pd.Timestamp, date)):
        return o.isoformat()[:10]
    return o


def pattern_stats() -> dict:
    if STATS_FILE.exists():
        return json.loads(STATS_FILE.read_text(encoding="utf-8"))
    return {"available": False, "missing_reason": "The backtest has not been run. Run: python scripts/run_backtest.py"}


def _quote(df: pd.DataFrame) -> dict:
    last, c = df.iloc[-1], df["close"]
    yr = df.iloc[-250:]
    ret = lambda n: round((float(c.iloc[-1]) / float(c.iloc[-1 - n]) - 1) * 100, 1) if len(c) > n else None  # noqa: E731
    return {
        "open": float(last["open"]),
        "high": float(last["high"]),
        "low": float(last["low"]),
        "prev_close": float(c.iloc[-2]),
        "volume": float(last["volume"]),
        "high_52w": float(yr["high"].max()),
        "low_52w": float(yr["low"].min()),
        "ret_1w": ret(5),
        "ret_1m": ret(21),
        "ret_3m": ret(63),
        "ret_1y": ret(249),
    }


def technical(df: pd.DataFrame, st) -> dict:
    hi, lo, cl, vo = (df[c].values.astype(float) for c in ("high", "low", "close", "volume"))
    a = float(atr_series(df).iloc[-1])
    piv = find_pivots(hi, lo, st.k)
    trend = trend_state(df, piv, st)
    levels = find_levels(piv, float(cl[-1]), a, len(df), LEVEL_LOOKBACK_BARS[st.key])
    vol = volume_read(df, st)
    line, sig, hist = macd(df["close"])
    mom = {
        "rsi": float(rsi(df["close"]).iloc[-1]),
        "macd": float(line.iloc[-1]),
        "macd_signal": float(sig.iloc[-1]),
        "macd_hist": float(hist.iloc[-1]),
    }
    fib = fibonacci(df, st.fib_lookback)
    pats = [p.to_dict() for p in detect_all(Ctx(hi, lo, cl, vo, piv, st.k, a))]
    return {
        "atr": a,
        "trend": trend,
        "levels": levels,
        "volume": vol,
        "momentum": mom,
        "fib": fib,
        "patterns": pats,
        "pivots": [{"idx": p.idx, "price": p.price, "kind": p.kind} for p in piv[-12:]],
    }


def _add_dates(tech: dict, df: pd.DataFrame):
    d = lambda i: df.index[int(i)].strftime("%Y-%m-%d")  # noqa: E731
    for p in tech["patterns"]:
        for pt in p["points"]:
            pt["date"] = d(pt["idx"])
        p["confirm_date"] = d(p["confirm_idx"]) if p.get("confirm_idx") is not None else None
    for side in ("supports", "resistances"):
        for level in tech["levels"][side]:
            level["dates"] = [d(i) for i in level.pop("bars")]
            level["last_touch"] = d(level.pop("last_touch_idx"))
    for key in ("swing_highs", "swing_lows"):
        for s in tech["trend"][key]:
            s["date"] = d(s["idx"])
    for p in tech["pivots"]:
        p["date"] = d(p["idx"])
    if tech["fib"]:
        tech["fib"]["high_date"], tech["fib"]["low_date"] = d(tech["fib"]["high_idx"]), d(tech["fib"]["low_idx"])
    bo = tech["volume"].get("breakout")
    if bo:
        bo["date"] = d(bo["idx"])


def _series_payload(bars: pd.DataFrame, fast_n: int, slow_n: int) -> dict:
    """Candles, volume and two simple averages for the chart library, one entry per bar."""
    fast_s, slow_s = sma(bars["close"], fast_n), sma(bars["close"], slow_n)
    ts = [d.strftime("%Y-%m-%d") for d in bars.index]
    return {
        "candles": [
            {
                "time": t,
                "open": round(float(o), 2),
                "high": round(float(h), 2),
                "low": round(float(lo), 2),
                "close": round(float(c), 2),
            }
            for t, o, h, lo, c in zip(ts, bars["open"], bars["high"], bars["low"], bars["close"], strict=False)
        ],
        "volume": [{"time": t, "value": int(x)} for t, x in zip(ts, bars["volume"], strict=False)],
        "fast": [{"time": t, "value": round(float(x), 2)} for t, x in zip(ts, fast_s, strict=False) if not math.isnan(x)],
        "slow": [{"time": t, "value": round(float(x), 2)} for t, x in zip(ts, slow_s, strict=False) if not math.isnan(x)],
        "fast_n": fast_n,
        "slow_n": slow_n,
        "first_date": ts[0] if ts else None,
    }


def weekly_bars(df: pd.DataFrame) -> pd.DataFrame:
    """Daily bars rolled up into weeks ending Friday. Each week is dated by its last trading day, so a week cut short
    by a holiday, and the current unfinished week, carry a real session date."""
    week = df.index.to_period("W-FRI")
    grouped = df.groupby(week)
    out = pd.DataFrame(
        {
            "open": grouped["open"].first(),
            "high": grouped["high"].max(),
            "low": grouped["low"].min(),
            "close": grouped["close"].last(),
            "volume": grouped["volume"].sum(),
        }
    )
    out.index = pd.DatetimeIndex(df.index.to_series().groupby(week).max().values)
    return out


def chart_data(df: pd.DataFrame, st) -> dict:
    """The whole daily history the source returned (up to CHART_YEARS), plus the same period as weekly bars.

    The daily keys stay at the top level; `weekly` holds the weekly series with WEEKLY_FAST and WEEKLY_SLOW averages.
    `years` is the span actually covered, so the page can say how much history it shows.
    """
    daily = _series_payload(df, st.fast, st.slow)
    daily["weekly"] = _series_payload(weekly_bars(df), WEEKLY_FAST, WEEKLY_SLOW)
    daily["years"] = round((df.index[-1] - df.index[0]).days / 365.25, 1) if len(df) else 0
    daily["momentum"] = momentum_series(df)
    return daily


def momentum_series(df: pd.DataFrame, bars: int = MOMENTUM_CHART_BARS) -> dict:
    """RSI(14), MACD(12,26,9) with its signal line and histogram, and ATR(14) for the last `bars` sessions, so the page
    can draw them as charts. Computed on the whole history first, so the early values are already settled."""
    line, sig, hist = macd(df["close"])
    series = {"rsi": rsi(df["close"]), "macd": line, "signal": sig, "hist": hist, "atr": atr_series(df)}
    tail = df.index[-bars:]
    ts = [d.strftime("%Y-%m-%d") for d in tail]
    return {
        k: [{"time": t, "value": round(float(x), 2)} for t, x in zip(ts, s.loc[tail], strict=False) if not math.isnan(x)]
        for k, s in series.items()
    }


def company_profile(info: dict) -> dict:
    """What the company does, in the source's own words, cut to whole sentences within PROFILE_MAX_CHARS."""
    text = " ".join(str(info.get("longBusinessSummary") or "").split())
    summary = ""
    for sentence in re.split(r"(?<=[.!?])\s+(?=[A-Z])", text):
        if summary and len(summary) + len(sentence) + 1 > PROFILE_MAX_CHARS:
            break
        summary = f"{summary} {sentence}".strip()
    if len(summary) > PROFILE_MAX_CHARS:
        summary = summary[: PROFILE_MAX_CHARS - 1].rsplit(" ", 1)[0] + "…"
    employees = info.get("fullTimeEmployees")
    return {
        "available": bool(summary),
        "summary": summary or None,
        "industry": info.get("industry"),
        "website": info.get("website"),
        "employees": int(employees) if isinstance(employees, int | float) and employees > 0 else None,
        "source": FUND_SOURCE,
        "missing_reason": None if summary else "The source has no business description for this company.",
    }


def resolve(query: str) -> str:
    """Accept an NSE symbol or a company name and return the symbol."""
    try:
        sym = clean_symbol(query)
    except DataError:
        sym = None
    listed = _safe(nse.listed)
    known = {s for s, _ in listed} if isinstance(listed, list) else set()
    if sym and (sym in known or not known):
        return sym  # an exact symbol, or the company list is unavailable so trust the input
    hits = _safe(nse.search, query, 1)
    if isinstance(hits, list) and hits:
        return hits[0]["symbol"]
    if sym is None:
        raise DataError("No NSE company matches that name. Try the symbol, for example RELIANCE or HDFCBANK.")
    return sym


def analyze(
    symbol: str,
    style: str = "swing",
    capital: float = 100000,
    risk_pct: float = 1.0,
    stop: float | None = None,
    entry: float | None = None,
) -> dict:
    symbol = resolve(symbol)
    if style not in STYLES:
        raise DataError("Style must be 'swing' or 'positional'.")
    st = STYLES[style]

    f_hist = _pool.submit(prices.history, symbol)
    f_fund = _pool.submit(_safe, prices.fundamentals, symbol)
    f_earn = _pool.submit(_safe, prices.earnings_date, symbol)
    f_deliv = _pool.submit(_safe, nse.delivery, symbol)
    f_bulk = _pool.submit(_safe, nse.bulk_deals, symbol)
    sector, peer_syms = peers_of(symbol)
    f_peers = {s: _pool.submit(_safe, prices.info, s) for s in peer_syms}

    df = f_hist.result()
    deliv = f_deliv.result()  # also warms the NSE file cache used just below
    price_note = ""
    extra = _safe(nse.recent_bars, symbol, df.index[-1].date())
    # Guard against an unadjusted corporate action between the two sources.
    if (
        isinstance(extra, pd.DataFrame)
        and len(extra)
        and abs(float(extra["close"].iloc[0]) / float(df["close"].iloc[-1]) - 1) < 0.25
    ):
        df = pd.concat([df, extra])
        price_note = f" Last {len(extra)} session(s) taken from the NSE end-of-day file."
    if len(df) < 40:
        raise DataError(f"{symbol} has only {len(df)} days of price history, too little to analyse.")
    as_of = df.index[-1].strftime("%Y-%m-%d")
    close = float(df["close"].iloc[-1])
    prev = float(df["close"].iloc[-2])
    symbols.remember_close(symbol, close, as_of)

    tech = technical(df, st)
    _add_dates(tech, df)

    # Sizing comes before the signal.
    entry_px = float(entry) if entry else close
    sug = sizing.suggest_stop(close, tech["atr"], tech["levels"]["supports"], st)
    stop_px = float(stop) if stop else sug["stop"]
    sz = sizing.position_size(float(capital), float(risk_pct), entry_px, stop_px)
    sz.update(
        {
            "stop_basis": "your own stop" if stop else sug["basis"],
            "suggested_stop": sug["stop"],
            "suggested_basis": sug["basis"],
            "entry_basis": "your own entry" if entry else "last close",
            "text": explain.sizing_text(sz),
        }
    )

    raw = f_fund.result()
    info = {} if isinstance(raw, Exception) or not raw else (raw.get("info") or {})
    is_lender = SECTOR_OF.get(symbol) in LENDER_SECTORS or info.get("sector") == "Financial Services"
    if isinstance(raw, Exception) or not raw:
        fund = {
            "available": False,
            "concerns": [],
            "pros": [],
            "cons": [],
            "verdict": None,
            "missing_reason": "Company statements could not be fetched from the data source.",
            "source": FUND_SOURCE,
            "as_of": None,
        }
    else:
        infos = {s: (None if isinstance(f.result(), Exception) else f.result()) for s, f in f_peers.items()}
        fund = fundamentals.analyse(raw, is_lender, fundamentals.peer_block(sector, infos))
    fund["text"] = explain.fundamental_text(fund)

    ed = f_earn.result()
    earnings = {
        "available": False,
        "missing_reason": "Results date not returned by the source.",
        "source": "Yahoo Finance calendar",
    }
    earn_days = None
    if isinstance(ed, date):
        earn_days = int(np.busday_count(date.today(), ed)) if ed >= date.today() else None
        if earn_days is not None:
            earnings = {
                "available": True,
                "date": ed.isoformat(),
                "trading_days_away": earn_days,
                "source": "Yahoo Finance calendar (estimate; confirm on the exchange)",
                "as_of": date.today().isoformat(),
            }
        else:
            earnings["missing_reason"] = "The source only has a past results date; the next date is not announced there."

    v = verdict.decide(
        st, len(df), tech["trend"], tech["levels"], tech["volume"], tech["atr"], entry_px, stop_px, fund, earn_days
    )
    v["agreement"] = verdict.agreement(tech["trend"]["direction"], fund, st)
    years = round(LEVEL_LOOKBACK_BARS[st.key] / 250, 1)
    context.annotate(v, tech, fund, sz, st, context.recent_move(df), years)
    v["invalidation"] = {"price": stop_px, "text": f"A daily close below ₹{stop_px:.2f} ({sz['stop_basis']})."}
    tech["text"] = explain.technical_text(
        st, tech["trend"], tech["levels"], tech["volume"], tech["momentum"], tech["fib"], tech["patterns"]
    )
    tech["style_text"] = explain.style_text(st, tech["trend"], stop_px, v)

    bulk = f_bulk.result()
    na = lambda why: {"available": False, "missing_reason": why}  # noqa: E731
    extras = {
        "delivery": deliv if isinstance(deliv, dict) else na("NSE archive request failed."),
        "bulk_deals": bulk if isinstance(bulk, dict) else na("NSE archive request failed."),
        "earnings": earnings,
        "order_book": na("Live buy and sell quantities need a broker or exchange feed, which is not connected."),
        "pledge": na("Promoter pledge data needs exchange shareholding filings or a licensed provider, which is not connected."),
        "announcements": na("Corporate announcements need an exchange feed, which is not connected. Check the NSE website."),
    }

    chart = chart_data(df, st)

    sources = [
        {
            "item": "Price, volume, averages, levels, patterns, RSI, MACD, ATR, Fibonacci",
            "source": PRICE_SOURCE,
            "as_of": as_of,
            "note": f"{len(df)} daily bars from {df.index[0].strftime('%Y-%m-%d')}. Split-adjusted, not dividend-adjusted."
            + price_note,
        },
        {
            "item": "Annual statements and ratios",
            "source": fund.get("source"),
            "as_of": fund.get("as_of"),
            "note": fund.get("missing_reason") or fund.get("history_note"),
        },
        {
            "item": "Valuation (P/E, market value) and peers",
            "source": "Yahoo Finance key ratios (trailing)",
            "as_of": "latest available",
            "note": (fund.get("peers") or {}).get("missing_reason"),
        },
    ]
    for label, key in (
        ("Delivery percentage", "delivery"),
        ("Bulk deals", "bulk_deals"),
        ("Next results date", "earnings"),
        ("Order book depth", "order_book"),
        ("Promoter pledge", "pledge"),
        ("Corporate announcements", "announcements"),
    ):
        e = extras[key]
        sources.append(
            {
                "item": label,
                "source": e.get("source") or "not available",
                "as_of": e.get("as_of"),
                "note": e.get("missing_reason"),
            }
        )

    report = {
        "symbol": symbol,
        "name": info.get("longName") or info.get("shortName") or symbol,
        "sector": sector or info.get("sector"),
        "profile": company_profile(info),
        "style": {"key": st.key, "name": st.name, "holds": st.holds},
        "as_of": as_of,
        "bars": len(df),
        "price": {"close": close, "change_pct": round((close / prev - 1) * 100, 2), "source": PRICE_SOURCE, "as_of": as_of},
        "quote": _quote(df),
        "verdict": v,
        "sizing": sz,
        "technical": tech,
        "fundamental": fund,
        "extras": extras,
        "chart": chart,
        "pattern_stats": pattern_stats(),
        "sources": sources,
        "disclaimer": DISCLAIMER,
    }
    return _clean(report)
