"""Context for the rule's checks: why a check reads the way it does, from the figures on the page.

The label never changes here. A check that fails stays failed; this module adds the facts behind the number, such as a
long sideways range followed by a fast move, which makes the "not stretched" check fail on almost every breakout.
Every sentence states a measured fact (prices, dates, sessions, percentages). Nothing here predicts a price.
"""

import numpy as np
import pandas as pd

from ...settings import (
    BASE_MAX_BARS,
    BASE_MAX_RANGE_PCT,
    BASE_MIN_BARS,
    BREAKOUT_VOLUME,
    MIN_REWARD_TO_RISK,
    RUN_LOOKBACK_BARS,
    RUN_MIN_PCT,
    Style,
)

NOTE = "Context explains the numbers behind each check. It does not change the label."


def _day(df: pd.DataFrame, i: int) -> str:
    return df.index[int(i)].strftime("%d %b %Y")


def _base_ending_at(high: np.ndarray, low: np.ndarray, end: int) -> tuple[int, float, float] | None:
    """The longest window ending at bar `end` (inclusive) whose high-to-low range stays within BASE_MAX_RANGE_PCT."""
    best = None
    for length in range(BASE_MIN_BARS, BASE_MAX_BARS + 1):
        start = end - length
        if start < 0:
            break
        hi, lo = float(high[start : end + 1].max()), float(low[start : end + 1].min())
        if lo <= 0 or (hi - lo) / lo * 100 > BASE_MAX_RANGE_PCT:
            break
        best = (start, lo, hi)
    return best


def recent_move(df: pd.DataFrame) -> dict:
    """The current run (from the lowest low of the last RUN_LOOKBACK_BARS sessions) and the sideways range before it.

    Also reports whether price is inside a sideways range right now. All figures are from daily bars.
    """
    high, low, close = (df[c].values.astype(float) for c in ("high", "low", "close"))
    n = len(df)
    out: dict = {"run": None, "base": None, "current_range": None}
    if n < BASE_MIN_BARS + 5:
        return out
    look = min(RUN_LOOKBACK_BARS, n - 1)
    start = n - look + int(np.argmin(low[-look:]))
    run_pct = (close[-1] / low[start] - 1) * 100
    if run_pct >= RUN_MIN_PCT and start < n - 1:
        out["run"] = {
            "from_price": round(float(low[start]), 2),
            "from_date": _day(df, start),
            "pct": round(float(run_pct), 1),
            "sessions": n - 1 - start,
        }
        base = _base_ending_at(high, low, start)
        if base:
            b_start, lo, hi = base
            out["base"] = {
                "low": round(lo, 2),
                "high": round(hi, 2),
                "range_pct": round((hi - lo) / lo * 100, 1),
                "sessions": start - b_start + 1,
                "from_date": _day(df, b_start),
                "to_date": _day(df, start),
                "broken_out": bool(close[-1] > hi),
            }
    now = _base_ending_at(high, low, n - 1)
    if now:
        b_start, lo, hi = now
        out["current_range"] = {
            "low": round(lo, 2),
            "high": round(hi, 2),
            "range_pct": round((hi - lo) / lo * 100, 1),
            "sessions": n - b_start,
            "from_date": _day(df, b_start),
        }
    return out


def _stretch(move: dict, st: Style, close: float) -> str | None:
    run, base = move.get("run"), move.get("base")
    if not run:
        return None
    text = (
        f"Price has risen {run['pct']}% in {run['sessions']} sessions from ₹{run['from_price']:,.2f} on {run['from_date']}. "
        f"The {st.fast}-day average lags a move this fast, so price sits far above it."
    )
    if base and base["broken_out"]:
        stop_gap = (close / base["high"] - 1) * 100
        text = (
            f"Before this move, price traded between ₹{base['low']:,.2f} and ₹{base['high']:,.2f} (a {base['range_pct']}% "
            f"range) for {base['sessions']} sessions, from {base['from_date']} to {base['to_date']}. It then rose "
            f"{run['pct']}% in {run['sessions']} sessions and is now above the top of that range. A long sideways range "
            f"followed by a fast move usually fails this check, because the {st.fast}-day average trails the move. "
            f"The check still fails: the top of the range, ₹{base['high']:,.2f}, is {stop_gap:.1f}% below today's price, "
            + (
                f"more than the {st.max_stop_pct * 100:.0f}% stop the {st.name.lower()} rule allows."
                if stop_gap / 100 > st.max_stop_pct
                else "so a stop under it would be wide and the position small."
            )
        )
    return text


def _room(levels: dict, entry: float | None, stop: float | None, history_years: float) -> str | None:
    res = levels.get("resistances") or []
    if not res:
        return None
    first = res[0]
    kind = {
        "single": "a single swing high, the weakest kind of level",
        "moderate": "a level price turned at twice",
        "strong": f"a strong level that turned price {first['touches']} times",
    }[first.get("strength", "single")]
    when = f", last tested on {pd.Timestamp(first['last_touch']):%d %b %Y}" if first.get("last_touch") else ""
    text = f"₹{first['price']:,.2f} is {kind}{when}."
    risk = (entry - stop) if entry and stop and entry > stop else None
    nxt = next((lv for lv in res[1:] if lv.get("strength") != "single"), None)
    if nxt and risk:
        rr2 = (nxt["price"] - entry) / risk
        text += (
            f" The next tested level above is ₹{nxt['price']:,.2f} ({nxt['touches']} swing points), "
            f"{rr2:.2f} times the stop distance away."
        )
    elif not nxt:
        text += f" No level above it has been tested more than once in the last {history_years:g} years of swings."
    return text


def _entry(move: dict, tech: dict, st: Style) -> str | None:
    """Where the rule's entry areas are today, in rupees, so the reader can see how far price is from each."""
    close, atr = float(tech["trend"]["close"]), float(tech["atr"] or 0)
    fast = tech["trend"].get("fast")
    sup = (tech["levels"].get("supports") or [None])[0]
    areas = []
    if sup and atr:
        areas.append(f"up to ₹{sup['price'] + 1.5 * atr:,.2f} (within 1.5 ATR of support at ₹{sup['price']:,.2f})")
    if fast and atr:
        areas.append(f"₹{fast:,.2f} to ₹{fast + atr:,.2f} (a pullback to the {st.fast}-day average)")
    areas.append(f"a close above the {st.breakout_n}-day high on at least {BREAKOUT_VOLUME:g} times average volume")
    text = f"At ₹{close:,.2f}, price is outside the rule's entry areas: " + "; ".join(areas) + "."
    rng = move.get("current_range")
    if rng:
        text = (
            f"Price has been inside a {rng['range_pct']}% range, between ₹{rng['low']:,.2f} and ₹{rng['high']:,.2f}, "
            f"for {rng['sessions']} sessions since {rng['from_date']}. "
        ) + text
    return text


def _stop(tech: dict, sizing: dict, st: Style) -> str | None:
    close, atr = float(tech["trend"]["close"]), float(tech["atr"] or 0)
    if not atr or not sizing.get("stop_basis"):
        return None
    return (
        f"The stop is placed {sizing['stop_basis']}. A normal day's range (ATR) is ₹{atr:,.2f}, "
        f"{atr / close * 100:.1f}% of the price, so a stop that leaves room for ordinary swings is wider than "
        f"the {st.max_stop_pct * 100:.0f}% the {st.name.lower()} rule allows."
    )


def _trend(move: dict, st: Style) -> str | None:
    run = move.get("run")
    if not run:
        return None
    return (
        f"Price has risen {run['pct']}% in {run['sessions']} sessions from ₹{run['from_price']:,.2f} on {run['from_date']}. "
        f"A trend counts as up once price is above its {st.slow}-day average and has closed above its last swing high, "
        "or makes higher highs and higher lows."
    )


def _results(quarter: dict) -> str | None:
    if not quarter:
        return None
    if quarter.get("available"):
        basis = "the same quarter a year earlier" if quarter.get("basis") == "year" else "the quarter before"
        pg = quarter.get("profit_growth_pct")
        text = (
            f"The newest quarter in the source, {quarter['quarter']}, had sales "
            f"{'up' if quarter['sales_growth_pct'] >= 0 else 'down'} {abs(quarter['sales_growth_pct'])}% on {basis}"
            + (f" and profit {'up' if pg >= 0 else 'down'} {abs(pg)}%." if pg is not None else ".")
        )
        return text + (f" {quarter['stale_note']}" if quarter.get("stale_note") else "")
    return quarter.get("stale_note")


def annotate(verdict: dict, tech: dict, fund: dict, sizing: dict, st: Style, move: dict, history_years: float) -> dict:
    """Add `context` to each check that has one, and a short list of background facts to the verdict."""
    close = float(tech["trend"]["close"])
    entry, stop = sizing.get("entry"), sizing.get("stop")
    by_name = {
        "Trend is up": lambda: _trend(move, st),
        "Price is at a sensible entry area": lambda: _entry(move, tech, st),
        "Price is not stretched": lambda: _stretch(move, st, close),
        "Stop distance is acceptable": lambda: _stop(tech, sizing, st),
        "Room to the next resistance": lambda: _room(tech["levels"], entry, stop, history_years),
        "No results due inside the holding window": lambda: _results(fund.get("quarter") or {}),
    }
    for check in verdict["checks"]:
        maker = by_name.get(check["name"])
        check["context"] = maker() if maker and not check["passed"] else None

    facts = []
    if fund.get("available"):
        pros, cons = len(fund.get("pros", [])), len(fund.get("cons", []))
        facts.append(
            f"Business read: {fund.get('verdict')}, with {pros} strength{'s' if pros != 1 else ''} and "
            f"{cons} concern{'s' if cons != 1 else ''} in the annual figures."
        )
    q = fund.get("quarter") or {}
    if q.get("available") or q.get("stale_note"):
        facts.append(_results(q))
    base, run = move.get("base"), move.get("run")
    if base and run and base["broken_out"]:
        facts.append(
            f"Chart: {base['sessions']} sessions in a {base['range_pct']}% range up to {base['to_date']}, then up "
            f"{run['pct']}% in {run['sessions']} sessions, above the top of that range."
        )
    elif run:
        facts.append(f"Chart: up {run['pct']}% in {run['sessions']} sessions since {run['from_date']}.")
    elif move.get("current_range"):
        rng = move["current_range"]
        facts.append(f"Chart: in a {rng['range_pct']}% range for {rng['sessions']} sessions.")
    verdict["context"] = {"facts": [f for f in facts if f], "note": NOTE, "min_reward_to_risk": MIN_REWARD_TO_RISK}
    return verdict
