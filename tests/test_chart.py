"""Chart payload: the whole daily history plus weekly bars. No network."""

import pandas as pd

from belfort.research.analysis import pipeline
from belfort.settings import STYLES, WEEKLY_FAST, WEEKLY_SLOW
from tests.helpers import price_frame


def test_weekly_bars_roll_up_each_week_and_date_it_by_its_last_session():
    df = price_frame(n=15)  # three business weeks of daily bars
    weeks = pipeline.weekly_bars(df)
    for date, row in weeks.iterrows():
        days = df[df.index.to_period("W-FRI") == date.to_period("W-FRI")]
        assert date == days.index[-1]
        assert row["open"] == days["open"].iloc[0] and row["close"] == days["close"].iloc[-1]
        assert row["high"] == days["high"].max() and row["low"] == days["low"].min()
        assert row["volume"] == days["volume"].sum()
    assert weeks.index[-1] == df.index[-1]


def test_weekly_bars_handle_a_holiday_week():
    df = price_frame(n=20).drop(pd.Timestamp("2026-11-06"))  # a Friday holiday
    weeks = pipeline.weekly_bars(df)
    assert pd.Timestamp("2026-11-05") in weeks.index and len(weeks) == 4


def test_chart_data_sends_the_whole_history_and_weekly_series():
    df = price_frame(n=1200)
    c = pipeline.chart_data(df, STYLES["swing"])
    assert len(c["candles"]) == 1200 and c["first_date"] == df.index[0].strftime("%Y-%m-%d")
    assert c["years"] > 4.5
    w = c["weekly"]
    assert w["fast_n"] == WEEKLY_FAST and w["slow_n"] == WEEKLY_SLOW
    assert 235 <= len(w["candles"]) <= 245
    assert len(w["slow"]) == len(w["candles"]) - WEEKLY_SLOW + 1
    assert all(isinstance(v["value"], int) for v in w["volume"][:5])


def test_momentum_series_match_the_reported_latest_values():
    df = price_frame(n=400)
    m = pipeline.chart_data(df, STYLES["swing"])["momentum"]
    tech = pipeline.technical(df, STYLES["swing"])
    assert set(m) == {"rsi", "macd", "signal", "hist", "atr"}
    assert all(len(v) == 250 and v[-1]["time"] == df.index[-1].strftime("%Y-%m-%d") for v in m.values())
    assert abs(m["rsi"][-1]["value"] - tech["momentum"]["rsi"]) < 0.01
    assert abs(m["macd"][-1]["value"] - tech["momentum"]["macd"]) < 0.01
    assert abs(m["atr"][-1]["value"] - tech["atr"]) < 0.01
    assert all(0 <= x["value"] <= 100 for x in m["rsi"])
