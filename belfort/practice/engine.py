"""Pure settlement rules for paper trades and predictions. No database, no network: easy to test.

End-of-day model, long only (the cash market most beginners start in):
  - An order placed on day D fills on the first session after D.
  - Market order: fills at that session's open.
  - Limit order: fills when the low reaches the limit, at the better of open and limit. Expires after 5 sessions.
  - Stop and target are checked every session from the fill day. If the open gaps past either, the exit is at
    the open. If one session touches both, the stop is assumed first (the cautious reading).
  - A close request exits at the open of the next session.

Managing an open trade (every change acts from the session after the day it was made):
  - Raising the stop: the stop can only move up. Each raise is kept as {"on": day, "stop": price} in the trade's
    stop_moves, so a replay of old bars uses the stop that applied on each day.
  - Trailing stop: after each session's close, a candidate stop is the close minus a fixed percentage, or minus a
    multiple of the 14-session ATR at that close. The stop ratchets up to the candidate and never moves down. The new
    level applies from the next session.
  - Selling part: the service splits the trade into two rows with the same entry and plan; the part sold carries a
    close request and exits at the next open by the rule above, the rest stays open.
  - The original stop stays as the trade's risk, so R multiples always measure against the risk taken at entry.
"""

import json
from dataclasses import dataclass

import pandas as pd

from ..settings import TRAIL_ATR_PERIOD

LIMIT_EXPIRY_SESSIONS = 5


@dataclass
class Fill:
    status: str
    entry_price: float | None = None
    entry_date: str | None = None
    exit_price: float | None = None
    exit_date: str | None = None
    exit_reason: str | None = None
    stop: float | None = None  # the stop that applies from the next session


def stop_moves(t: dict) -> list[dict]:
    """The trade's stop raises, oldest first."""
    raw = t.get("stop_moves") or "[]"
    moves = json.loads(raw) if isinstance(raw, str) else list(raw)
    return sorted(moves, key=lambda m: m["on"])


def atr(df: pd.DataFrame, period: int = TRAIL_ATR_PERIOD) -> pd.Series:
    """Average true range: the average daily range including gaps, over `period` sessions."""
    prev = df["close"].shift(1)
    true_range = pd.concat([df["high"] - df["low"], (df["high"] - prev).abs(), (df["low"] - prev).abs()], axis=1).max(axis=1)
    return true_range.rolling(period, min_periods=1).mean()


def trail_candidate(kind: str | None, value: float | None, close: float, atr_now: float | None) -> float | None:
    """Where a trailing stop would sit after a session closed at `close`."""
    if not kind or not value:
        return None
    if kind == "pct":
        return round(close * (1 - value / 100), 2)
    if kind == "atr" and atr_now is not None:
        return round(close - value * atr_now, 2)
    return None


def _after(df: pd.DataFrame, day: str, inclusive: bool = False) -> pd.DataFrame:
    t = pd.Timestamp(day)
    return df[df.index >= t] if inclusive else df[df.index > t]


def settle_trade(t: dict, df: pd.DataFrame) -> Fill:
    """Return the trade's state after replaying every bar we have since it was placed."""
    f = Fill(
        t["status"], t.get("entry_price"), t.get("entry_date"), t.get("exit_price"), t.get("exit_date"), t.get("exit_reason")
    )
    if f.status in ("closed", "cancelled", "expired"):
        return f

    if f.status == "pending":
        later = _after(df, t["placed_on"])
        if t["entry_type"] == "market":
            if not len(later):
                return f
            bar = later.iloc[0]
            f.status, f.entry_price, f.entry_date = "open", float(bar["open"]), later.index[0].strftime("%Y-%m-%d")
        else:
            lim = float(t["limit_price"])
            for i, (ts, bar) in enumerate(later.iterrows()):
                if i >= LIMIT_EXPIRY_SESSIONS:
                    f.status, f.exit_reason = "expired", f"limit ₹{lim:.2f} not reached in {LIMIT_EXPIRY_SESSIONS} sessions"
                    return f
                if float(bar["low"]) <= lim:
                    f.status, f.entry_price, f.entry_date = "open", min(float(bar["open"]), lim), ts.strftime("%Y-%m-%d")
                    break
            else:
                return f

    initial = float(t["stop"])
    stop, target = initial, t.get("target")
    target = float(target) if target else None
    close_req = t.get("close_requested_on")
    moves = stop_moves(t)
    kind, value, trail_from = t.get("trail_kind"), t.get("trail_value"), t.get("trail_from")
    ranges = atr(df) if kind == "atr" else None
    trailed = None
    for ts, bar in _after(df, f.entry_date, inclusive=True).iterrows():
        day = ts.strftime("%Y-%m-%d")
        o, h, lo, c = float(bar["open"]), float(bar["high"]), float(bar["low"]), float(bar["close"])
        first = day == f.entry_date
        for m in moves:
            if m["on"] < day:
                stop = max(stop, float(m["stop"]))
        if trailed is not None:
            stop = max(stop, trailed)
        f.stop = stop
        raised = stop > initial
        if close_req and day > close_req:
            return _exit(f, o, day, "closed by you")
        if not first and o <= stop:
            return _exit(f, o, day, "gapped below the raised stop" if raised else "gapped below the stop")
        if not first and target and o >= target:
            return _exit(f, o, day, "gapped above the target")
        if lo <= stop:
            return _exit(f, stop, day, f"raised stop hit at ₹{stop:.2f}" if raised else "stop-loss hit")
        if target and h >= target:
            return _exit(f, target, day, "target reached")
        if trail_from and day > trail_from:
            candidate = trail_candidate(kind, value, c, float(ranges.loc[ts]) if ranges is not None else None)
            if candidate is not None and candidate < c:
                trailed = candidate if trailed is None else max(trailed, candidate)
    f.stop = max(stop, trailed) if trailed is not None else stop
    return f


def _exit(f: Fill, price: float, day: str, reason: str) -> Fill:
    f.status, f.exit_price, f.exit_date, f.exit_reason = "closed", float(price), day, reason
    return f


def r_multiple(entry: float, stop: float, exit_price: float) -> float | None:
    risk = entry - stop
    return None if risk <= 0 else round((exit_price - entry) / risk, 2)


def brier(confidence: float, correct: bool) -> float:
    """Brier score for a yes/no forecast: 0 is perfect, 0.25 is a coin flip, 1 is confidently wrong."""
    return round((1 - confidence) ** 2 if correct else confidence**2, 4)


def forecast_points(b: float) -> int:
    """Practice points for one resolved prediction. A 50% call scores 0; confident and right scores up to 100;
    confident and wrong loses more than it could have won. This rewards honest confidence, not bold calls."""
    return round(100 * (1 - 4 * b))


def resolve_prediction(p: dict, df: pd.DataFrame) -> dict | None:
    later = _after(df, p["ref_date"])
    n = int(p["horizon_days"])
    if len(later) < n:
        return None
    bar_ts, close = later.index[n - 1], float(later["close"].iloc[n - 1])
    went_up = close > float(p["ref_close"])
    correct = went_up if p["direction"] == "up" else not went_up
    b = brier(float(p["confidence"]), correct)
    return {
        "outcome_date": bar_ts.strftime("%Y-%m-%d"),
        "outcome_close": close,
        "correct": int(correct),
        "brier": b,
        "score": forecast_points(b),
        "status": "resolved",
    }


def calibration(resolved: list[dict]) -> list[dict]:
    """Group resolved predictions by stated confidence and compare with how often they came true."""
    buckets = [(0.5, 0.6), (0.6, 0.7), (0.7, 0.8), (0.8, 0.9), (0.9, 1.01)]
    out = []
    for lo, hi in buckets:
        xs = [p for p in resolved if lo <= p["confidence"] < hi]
        if xs:
            out.append(
                {
                    "range": f"{int(lo * 100)}–{int(min(hi, 1) * 100)}%",
                    "count": len(xs),
                    "stated": round(sum(p["confidence"] for p in xs) / len(xs), 3),
                    "actual": round(sum(p["correct"] for p in xs) / len(xs), 3),
                }
            )
    return out
