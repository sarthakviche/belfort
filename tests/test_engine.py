import math

import numpy as np
import pytest

from belfort.research.analysis import explain, fundamentals, sizing, verdict
from belfort.research.analysis.indicators import atr, rsi, sma
from belfort.research.analysis.pivots import confirmed_pivots, find_pivots, raw_pivots
from belfort.research.backtest.evaluate import synthetic_report
from belfort.settings import LABEL_AVOID, LABEL_NODATA, LABEL_VALID, LABEL_WATCH, STYLES
from tests.helpers import price_frame, statements

SWING = STYLES["swing"]


# ---------- position sizing (acceptance 5) ----------
def test_sizing_exact_example():
    s = sizing.position_size(200000, 1, 500, 480)
    assert s["quantity"] == 100 and s["risk_amount"] == 2000 and s["risk_budget"] == 2000


def test_sizing_never_exceeds_limit():
    rng = np.random.default_rng(0)
    for _ in range(3000):
        cap, risk = rng.uniform(5e3, 5e7), rng.uniform(0.1, 5)
        entry = rng.uniform(5, 50000)
        stop = entry * (1 - rng.uniform(0.002, 0.3))
        s = sizing.position_size(cap, risk, entry, stop)
        budget, per = cap * risk / 100, entry - stop
        assert s["quantity"] * per <= budget + 1e-6  # never over the limit
        assert s["quantity"] * entry <= cap + 1e-6  # never over capital
        if not s["capped_by_capital"]:
            assert (s["quantity"] + 1) * per > budget - 1e-6  # and one more share would break it


def test_sizing_rejects_bad_inputs():
    assert sizing.position_size(100000, 1, 100, 100)["error"]
    assert sizing.position_size(100000, 1, 100, 120)["error"]
    assert sizing.position_size(0, 1, 100, 90)["error"]
    assert sizing.position_size(1000, 1, 5000, 4000)["quantity"] == 0


def test_stop_is_below_price_and_within_limit():
    df = price_frame()
    a = float(atr(df).iloc[-1])
    close = float(df["close"].iloc[-1])
    s = sizing.suggest_stop(close, a, [{"price": close - a, "touches": 2}], SWING)
    assert s["stop"] < close and (close - s["stop"]) / close <= SWING.max_stop_pct


# ---------- indicators and pivots ----------
def test_indicators_basic():
    df = price_frame()
    r = rsi(df["close"])
    assert r.dropna().between(0, 100).all()
    assert math.isclose(sma(df["close"], 20).iloc[-1], df["close"].iloc[-20:].mean())
    assert (atr(df).iloc[20:] > 0).all()


def test_pivots_have_no_lookahead():
    df = price_frame(seed=3)
    hi, lo = df["high"].values, df["low"].values
    raw = raw_pivots(hi, lo, 5)
    for t in (150, 250, 399):
        known = confirmed_pivots(raw, 5, t)
        assert all(p.idx + 5 <= t for p in known)
        # the same pivots come out when the future bars are cut off entirely
        cut = find_pivots(hi[: t + 1], lo[: t + 1], 5)
        assert [(p.idx, p.kind) for p in cut] == [(p.idx, p.kind) for p in known]


# ---------- pattern detectors (acceptance 2) ----------
def test_detectors_find_textbook_shapes_and_rarely_fire_on_noise():
    rep = synthetic_report(n_pos=40, n_neg=150, seed=3)
    for name, r in rep.items():
        assert r["hit_rate"] >= 0.7, (name, r)
        assert r["false_positive_rate"] <= 0.2, (name, r)


# ---------- concerns list (acceptance 3, synthetic archetypes only) ----------
def _titles(f, sev=None):
    return [c["title"] for c in f["concerns"] if sev is None or c["severity"] == sev]


def test_healthy_company_is_not_flagged():
    f = fundamentals.analyse(statements(), is_lender=False)
    assert f["available"] and f["verdict"] == "constructive"
    assert not _titles(f, "high") and not _titles(f, "medium")
    assert any(c["severity"] == "info" and "pledge" in c["title"].lower() for c in f["concerns"])


@pytest.mark.parametrize(
    "kwargs,expect",
    [
        (dict(debt=(500, 900, 1600, 2600), eq=(1000, 1050, 1100, 1150), interest=(40, 80, 150, 260)), "Debt is high and rising"),
        (dict(interest=(40, 80, 150, 260)), "Profit barely covers interest"),
        (dict(recv=(200, 260, 420, 700)), "Money owed by customers is growing faster than sales"),
        (dict(cfo=(100, 60, 10, -50)), "Profit is not turning into cash"),
        (dict(ni=(120, 60, -40, -150)), "The company made a net loss"),
    ],
)
def test_serious_red_flags_are_caught(kwargs, expect):
    f = fundamentals.analyse(statements(**kwargs), is_lender=False)
    assert expect in _titles(f, "high"), _titles(f)
    assert f["verdict"] == "cautious"
    assert f["concerns"][0]["severity"] == "high"  # ranked most serious first


def test_moderate_flags():
    f = fundamentals.analyse(statements(unusual=(0, 0, 0, 120)), is_lender=False)
    assert "One-time gains lifted profit" in _titles(f, "medium")
    s = statements()
    s["income"].loc["Operating Income"] = np.array([220, 200, 180, 150]) * 1e7
    f = fundamentals.analyse(s, False)
    assert "Operating margin has fallen two years running" in _titles(f, "medium")


def test_every_concern_has_figure_period_and_source():
    f = fundamentals.analyse(
        statements(debt=(500, 900, 1600, 2600), eq=(1000, 1050, 1100, 1150), recv=(200, 260, 420, 700)), False
    )
    for c in f["concerns"]:
        assert c["detail"] and c["source"]
        if c["severity"] != "info":
            assert c["period"] and any(ch.isdigit() for ch in c["detail"])


def test_lenders_skip_debt_checks_and_say_so():
    f = fundamentals.analyse(statements(debt=(5000, 6000, 7000, 9000)), is_lender=True)
    assert not any("Debt" in t for t in _titles(f))
    assert f["notes"]


def test_missing_statements_are_reported_not_invented():
    f = fundamentals.analyse({"income": None, "balance": None, "cashflow": None, "info": {}}, False)
    assert f["available"] is False and f["missing_reason"]


# ---------- the label ----------
def _inputs(direction="up", close=100.0):
    trend = {
        "direction": direction,
        "structure": direction if direction != "sideways" else "mixed",
        "ma_alignment": "up" if direction == "up" else "mixed",
        "close": close,
        "fast": 99.0,
        "slow": 95.0,
    }
    levels = {"supports": [{"price": 98.0, "touches": 3}], "resistances": [{"price": 112.0, "touches": 2}]}
    vol = {"breakout": None}
    return trend, levels, vol


CLEAN = {"available": True, "verdict": "constructive", "concerns": []}


def test_label_valid_when_everything_is_met():
    t, lv, v = _inputs()
    out = verdict.decide(SWING, 300, t, lv, v, 2.0, 100.0, 96.0, CLEAN, None)
    assert out["label"] == LABEL_VALID and not out["unmet"]


def test_label_avoid_in_downtrend_or_with_serious_concern():
    t, lv, v = _inputs("down")
    assert verdict.decide(SWING, 300, t, lv, v, 2.0, 100.0, 96.0, CLEAN, None)["label"] == LABEL_AVOID
    t, lv, v = _inputs("up")
    bad = {
        "available": True,
        "verdict": "cautious",
        "concerns": [{"severity": "high", "title": "Debt is high and rising", "detail": "x"}],
    }
    out = verdict.decide(SWING, 300, t, lv, v, 2.0, 100.0, 96.0, bad, None)
    assert out["label"] == LABEL_AVOID and "Debt" in out["main_risk"]


def test_label_watch_cases():
    t, lv, v = _inputs("sideways")
    assert verdict.decide(SWING, 300, t, lv, v, 2.0, 100.0, 96.0, CLEAN, None)["label"] == LABEL_WATCH
    t, lv, v = _inputs("up")
    # fundamentals missing: capped at Watch
    assert (
        verdict.decide(SWING, 300, t, lv, v, 2.0, 100.0, 96.0, {"available": False, "concerns": []}, None)["label"] == LABEL_WATCH
    )
    # results due inside a swing holding window
    assert verdict.decide(SWING, 300, t, lv, v, 2.0, 100.0, 96.0, CLEAN, 2)["label"] == LABEL_WATCH
    # resistance too close for the stop distance
    lv["resistances"] = [{"price": 102.0, "touches": 2}]
    assert verdict.decide(SWING, 300, t, lv, v, 2.0, 100.0, 96.0, CLEAN, None)["label"] == LABEL_WATCH


def test_label_insufficient_data():
    t, lv, v = _inputs()
    assert verdict.decide(SWING, 60, t, lv, v, 2.0, 100.0, 96.0, CLEAN, None)["label"] == LABEL_NODATA


def test_agreement_states():
    assert verdict.agreement("up", {"available": True, "verdict": "constructive"}, SWING)["state"] == "agree"
    assert verdict.agreement("up", {"available": True, "verdict": "cautious"}, SWING)["state"] == "conflict"
    assert verdict.agreement("down", {"available": True, "verdict": "constructive"}, SWING)["state"] == "conflict"
    assert verdict.agreement("up", {"available": False}, SWING)["state"] == "unknown"


def test_banned_phrase_finder():
    assert explain.find_banned("This is a sure shot, buy now!") == ["sure shot", "buy now"]
    assert explain.find_banned("The trend is up and volume agrees.") == []


def test_sharp_recovery_is_read_as_a_new_uptrend_not_as_down():
    """A fall followed by a fast rally past the last swing high must not be called 'no trend' (HDFC Bank, Nov 2026)."""
    import pandas as pd

    from belfort.research.analysis.structure import trend_state

    path = np.r_[np.linspace(100, 80, 150), np.linspace(80, 84, 12), np.linspace(84, 78, 12), np.linspace(78, 95, 12)]
    rng = np.random.default_rng(5)
    close = path * (1 + rng.normal(0, 0.002, len(path)))
    df = pd.DataFrame(
        {"open": close, "high": close * 1.004, "low": close * 0.996, "close": close, "volume": 1e6},
        index=pd.bdate_range(end="2026-11-13", periods=len(path)),
    )
    t = trend_state(df, find_pivots(df["high"].values, df["low"].values, 5), SWING)
    assert t["direction"] == "up" and t["phase"] == "early" and t["broke_above_last_high"]
    assert "turned up" in explain.trend_sentence(t)


# ---------------- support and resistance zones ----------------


def test_levels_do_not_creep_past_the_zone_width():
    from belfort.research.analysis.pivots import Pivot
    from belfort.research.analysis.structure import find_levels

    # Four swing points 0.6 apart with ATR 1 (zone width 0.75). Comparing with a running average chained them all
    # into one level spanning 1.8 ATR; each zone may now span at most 0.75 ATR.
    piv = [Pivot(i, p, "H" if i % 2 else "L") for i, p in enumerate([100.0, 100.6, 101.2, 101.8])]
    lv = find_levels(piv, close=110.0, atr=1.0, n_bars=10)
    zones = sorted((z["low"], z["high"]) for z in lv["supports"])
    assert zones == [(100.0, 100.6), (101.2, 101.8)]
    assert all(z["high"] - z["low"] <= 0.75 for z in lv["supports"])


def test_level_strength_follows_touch_count():
    from belfort.research.analysis.pivots import Pivot
    from belfort.research.analysis.structure import find_levels, level_strength

    assert [level_strength(n) for n in (1, 2, 3, 5)] == ["single", "moderate", "strong", "strong"]
    piv = [Pivot(1, 90.0, "L"), Pivot(3, 90.2, "L"), Pivot(5, 90.1, "L"), Pivot(7, 120.0, "H")]
    lv = find_levels(piv, close=100.0, atr=1.0, n_bars=10)
    assert lv["supports"][0]["strength"] == "strong" and lv["supports"][0]["touches"] == 3
    assert lv["resistances"][0]["strength"] == "single"


def test_levels_only_use_the_lookback_window():
    from belfort.research.analysis.pivots import Pivot
    from belfort.research.analysis.structure import find_levels

    piv = [Pivot(5, 80.0, "L"), Pivot(400, 90.0, "L")]
    assert [z["price"] for z in find_levels(piv, 100.0, 1.0, n_bars=500, lookback=260)["supports"]] == [90.0]
    assert [z["price"] for z in find_levels(piv, 100.0, 1.0, n_bars=500, lookback=500)["supports"]] == [90.0, 80.0]


def test_ratio_text_never_rounds_across_the_limit():
    from belfort.research.analysis.verdict import ratio_text

    assert ratio_text(1.48, 1.5) == "1.48"  # would read 1.5 and look like a pass
    assert ratio_text(1.46, 1.5) == "1.46"
    assert ratio_text(1.51, 1.5) == "1.5"
    assert ratio_text(2.04, 1.5) == "2.0" and ratio_text(0.8, 1.5) == "0.8"


def test_ratio_text_for_an_upper_limit():
    from belfort.research.analysis.verdict import ratio_text

    assert ratio_text(3.04, 3, over=True) == "3.04"  # fails the at-most-3 check, must not read as 3.0
    assert ratio_text(2.97, 3, over=True) == "3.0"  # passes and 3.0 still passes
    assert ratio_text(3.8, 3, over=True) == "3.8"


# ---------------- latest quarter ----------------


def _quarters(rows):
    import pandas as pd

    cols = [pd.Timestamp(d) for d, _, _ in rows]
    return pd.DataFrame({c: {"Total Revenue": r, "Net Income": n} for c, (_, r, n) in zip(cols, rows, strict=True)})


def test_quarter_compares_with_the_year_ago_quarter():
    import pandas as pd

    from belfort.research.analysis.fundamentals import quarter_trend

    q = _quarters([("2025-09-30", 100.0, 10.0), ("2026-06-30", 105.0, 11.0), ("2026-09-30", 120.0, 13.0)])
    out = quarter_trend(q, today=pd.Timestamp("2026-11-26"))
    assert out["basis"] == "year" and out["compared_with"] == "Sep 2025"
    assert out["sales_growth_pct"] == 20.0 and out["profit_growth_pct"] == 30.0 and not out["stale"]


def test_quarter_falls_back_to_the_previous_quarter():
    import pandas as pd

    from belfort.research.analysis.fundamentals import quarter_trend

    q = _quarters([("2026-06-30", 100.0, 10.0), ("2026-09-30", 110.0, 9.0)])
    out = quarter_trend(q, today=pd.Timestamp("2026-11-26"))
    assert out["available"] and out["basis"] == "quarter" and out["compared_with"] == "Jun 2026"
    assert out["sales_growth_pct"] == 10.0 and out["profit_growth_pct"] == -10.0


def test_quarter_says_when_the_source_is_stale():
    import pandas as pd

    from belfort.research.analysis.fundamentals import quarter_trend

    # HDFC Bank on 2026-11-26: Yahoo's newest quarter was June 2025.
    q = _quarters([("2025-03-31", 953.0, 153.9), ("2025-06-30", 853.5, 162.6)])
    out = quarter_trend(q, today=pd.Timestamp("2026-11-26"))
    assert out["stale"] and "Jun 2025" in out["stale_note"] and "NSE or BSE" in out["stale_note"]


# ---------------- company profile ----------------


def test_company_profile_cuts_at_whole_sentences():
    from belfort.research.analysis.pipeline import company_profile
    from belfort.settings import PROFILE_MAX_CHARS

    text = "HDFC Bank Limited provides banking services in India. " + "It runs retail and wholesale banking. " * 30
    p = company_profile({"longBusinessSummary": text, "industry": "Banks", "fullTimeEmployees": 210109})
    assert p["available"] and p["summary"].startswith("HDFC Bank Limited provides banking services in India.")
    assert len(p["summary"]) <= PROFILE_MAX_CHARS and p["summary"].endswith(".")
    assert p["industry"] == "Banks" and p["employees"] == 210109


def test_company_profile_without_a_description():
    from belfort.research.analysis.pipeline import company_profile

    p = company_profile({})
    assert not p["available"] and p["summary"] is None and "no business description" in p["missing_reason"]
