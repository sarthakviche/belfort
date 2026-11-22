"""Daily bars for any vertical, from the same providers the research report uses.

Practice and learning call `bars()`; tests replace it. The providers live in the research pipeline so one
substitution (pipeline.prices / pipeline.nse) changes the data for every vertical.
"""

from datetime import date, timedelta

import pandas as pd


def bars(symbol: str, years: int = 5) -> pd.DataFrame:
    from ..research.analysis import pipeline

    df = pipeline.prices.history(symbol, years)
    try:
        extra = pipeline.nse.recent_bars(symbol, df.index[-1].date())
        if (
            isinstance(extra, pd.DataFrame)
            and len(extra)
            and abs(float(extra["close"].iloc[0]) / float(df["close"].iloc[-1]) - 1) < 0.25
        ):
            df = pd.concat([df, extra])
    except Exception:
        pass
    return df[~df.index.duplicated(keep="last")].sort_index()


def lagged(df: pd.DataFrame, lag_days: int) -> pd.DataFrame:
    """Only bars at least `lag_days` calendar days old: used for learning content that names a stock."""
    cutoff = pd.Timestamp(date.today() - timedelta(days=lag_days))
    return df[df.index <= cutoff]
