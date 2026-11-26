"""Context for the rule's checks: facts behind a failed check, never a change to the check. No network."""

import numpy as np
import pandas as pd

from belfort.research.analysis import context
from belfort.settings import STYLES

SWING = STYLES["swing"]


def _frame(closes, spread=0.01):
    closes = np.asarray(closes, dtype=float)
    idx = pd.bdate_range(end="2026-11-20", periods=len(closes))
    return pd.DataFrame(
        {
            "open": closes,
            "high": closes * (1 + spread),
            "low": closes * (1 - spread),
            "close": closes,
            "volume": np.full(len(closes), 1e6),
        },
        index=idx,
    )


def _base_then_run(base_bars=60, run_bars=15, run_pct=28.0):
    flat = 100 + 4 * np.sin(np.arange(base_bars) / 3)  # a sideways range of about 10%
    run = np.linspace(flat[-1], flat[-1] * (1 + run_pct / 100), run_bars + 1)[1:]
    return _frame(np.r_[np.full(40, 120.0), flat, run])


def test_finds_the_run_and_the_sideways_range_before_it():
    move = context.recent_move(_base_then_run())
    assert move["run"]["pct"] > 20 and move["run"]["sessions"] <= 25  # counted from the lowest low
    base = move["base"]
    assert base["sessions"] >= 50 and base["range_pct"] <= 15 and base["broken_out"]


def test_no_run_when_price_is_flat():
    move = context.recent_move(_frame(100 + np.sin(np.arange(200))))
    assert move["run"] is None and move["base"] is None
    assert move["current_range"]["sessions"] >= context.BASE_MIN_BARS


def test_short_history_gives_nothing():
    assert context.recent_move(_frame(np.linspace(100, 120, 10))) == {"run": None, "base": None, "current_range": None}


def _tech(close=130.0, fast=110.0, atr=3.0, res=None, sup=None):
    return {
        "trend": {"close": close, "fast": fast},
        "atr": atr,
        "levels": {"resistances": res or [], "supports": sup or []},
    }


def _verdict(*failed):
    names = [
        "Trend is up",
        "Price is at a sensible entry area",
        "Price is not stretched",
        "Stop distance is acceptable",
        "Room to the next resistance",
        "No results due inside the holding window",
        "Business concerns check ran",
    ]
    return {"checks": [{"name": n, "passed": n not in failed, "detail": ""} for n in names]}


def test_failed_stretch_check_stays_failed_and_explains_the_breakout():
    df = _base_then_run()
    move = context.recent_move(df)
    v = _verdict("Price is not stretched")
    close = float(df["close"].iloc[-1])
    context.annotate(v, _tech(close=close), {}, {"entry": close, "stop": close * 0.95}, SWING, move, 1.0)
    check = next(c for c in v["checks"] if c["name"] == "Price is not stretched")
    assert check["passed"] is False
    assert "sideways range" in check["context"] and "still fails" in check["context"]
    assert all(c["context"] is None for c in v["checks"] if c["passed"])
    assert any(f.startswith("Chart:") for f in v["context"]["facts"])


def test_room_context_names_the_next_tested_level():
    res = [
        {"price": 140.0, "touches": 1, "strength": "single", "last_touch": "2026-01-27"},
        {"price": 150.0, "touches": 1, "strength": "single"},
        {"price": 160.0, "touches": 3, "strength": "strong"},
    ]
    v = _verdict("Room to the next resistance")
    context.annotate(v, _tech(res=res), {}, {"entry": 130.0, "stop": 120.0}, SWING, {}, 1.0)
    text = next(c for c in v["checks"] if c["name"] == "Room to the next resistance")["context"]
    assert "single swing high" in text and "27 Jan 2026" in text
    assert "₹160.00" in text and "3.00 times" in text


def test_room_context_says_when_no_level_above_is_tested():
    res = [{"price": 140.0, "touches": 1, "strength": "single"}]
    v = _verdict("Room to the next resistance")
    context.annotate(v, _tech(res=res), {}, {"entry": 130.0, "stop": 120.0}, SWING, {}, 1.0)
    assert "No level above it" in v["checks"][4]["context"]


def test_entry_context_lists_the_entry_areas_in_rupees():
    v = _verdict("Price is at a sensible entry area")
    sup = [{"price": 115.0, "touches": 2}]
    context.annotate(v, _tech(sup=sup), {}, {}, SWING, {}, 1.0)
    text = v["checks"][1]["context"]
    assert "₹119.50" in text and "₹110.00 to ₹113.00" in text and "20-day high" in text


def test_stop_and_results_context():
    v = _verdict("Stop distance is acceptable", "No results due inside the holding window")
    fund = {
        "available": True,
        "verdict": "constructive",
        "pros": ["a"],
        "cons": [],
        "quarter": {
            "available": True,
            "quarter": "Sep 2026",
            "basis": "year",
            "sales_growth_pct": 12.0,
            "profit_growth_pct": -3.0,
        },
    }
    sizing = {"stop_basis": "half an ATR below support at ₹100.00"}
    context.annotate(v, _tech(), fund, sizing, SWING, {}, 1.0)
    assert "half an ATR below support" in v["checks"][3]["context"]
    assert "sales up 12.0%" in v["checks"][5]["context"] and "profit down 3.0%" in v["checks"][5]["context"]
    assert v["context"]["facts"][0].startswith("Business read: constructive, with 1 strength and 0 concerns")


def test_context_never_uses_advice_words():
    df = _base_then_run()
    move = context.recent_move(df)
    v = _verdict(*[c["name"] for c in _verdict()["checks"]])
    close = float(df["close"].iloc[-1])
    res = [{"price": close * 1.05, "touches": 1, "strength": "single"}]
    context.annotate(v, _tech(close=close, res=res), {}, {"entry": close, "stop": close * 0.95}, SWING, move, 1.0)
    text = " ".join(c["context"] or "" for c in v["checks"]) + " ".join(v["context"]["facts"])
    for word in ("buy", "sell", "target", "will rise", "will fall", "recommend"):
        assert word not in text.lower()
