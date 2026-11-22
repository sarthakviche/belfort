"""Pure settlement rules for paper trades and predictions. No database, no network: easy to test.

End-of-day model, long only (the cash market most beginners start in):
  - An order placed on day D fills on the first session after D.
  - Market order: fills at that session's open.
  - Limit order: fills when the low reaches the limit, at the better of open and limit. Expires after 5 sessions.
  - Stop and target are checked every session from the fill day. If the open gaps past either, the exit is at
    the open. If one session touches both, the stop is assumed first (the cautious reading).
  - A close request exits at the open of the next session.
"""

from dataclasses import dataclass

import pandas as pd

LIMIT_EXPIRY_SESSIONS = 5


@dataclass
class Fill:
    status: str
    entry_price: float | None = None
    entry_date: str | None = None
    exit_price: float | None = None
    exit_date: str | None = None
    exit_reason: str | None = None


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

    stop, target = float(t["stop"]), t.get("target")
    target = float(target) if target else None
    close_req = t.get("close_requested_on")
    for ts, bar in _after(df, f.entry_date, inclusive=True).iterrows():
        day = ts.strftime("%Y-%m-%d")
        o, h, lo = float(bar["open"]), float(bar["high"]), float(bar["low"])
        first = day == f.entry_date
        if close_req and day > close_req:
            return _exit(f, o, day, "closed by you")
        if not first and o <= stop:
            return _exit(f, o, day, "gapped below the stop")
        if not first and target and o >= target:
            return _exit(f, o, day, "gapped above the target")
        if lo <= stop:
            return _exit(f, stop, day, "stop-loss hit")
        if target and h >= target:
            return _exit(f, target, day, "target reached")
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
