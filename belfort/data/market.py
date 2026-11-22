"""Daily bars for any vertical, from the same providers the research report uses.

Practice and learning call `bars()`; tests replace it. The providers live in the research pipeline so one
substitution (pipeline.prices / pipeline.nse) changes the data for every vertical.
"""

import threading
from datetime import date, datetime, time, timedelta, timezone

import pandas as pd

from .. import settings

IST = timezone(timedelta(hours=5, minutes=30))
_memory: dict[tuple[str, int], tuple[datetime, pd.DataFrame]] = {}
_memory_lock = threading.Lock()


def last_release(now: datetime | None = None) -> datetime:
    """The latest moment (IST) at or before `now` when a session's end-of-day data became complete."""
    now = (now or datetime.now(IST)).astimezone(IST)
    ready = time(*settings.MARKET_DATA_READY_IST)
    day = now.date()
    while True:
        moment = datetime.combine(day, ready, tzinfo=IST)
        if day.weekday() < 5 and moment <= now:
            return moment
        day -= timedelta(days=1)


def next_release(now: datetime | None = None) -> datetime:
    """The first moment (IST) after `now` when new end-of-day data is expected. Holidays only cost one extra fetch."""
    now = (now or datetime.now(IST)).astimezone(IST)
    ready = time(*settings.MARKET_DATA_READY_IST)
    day = now.date()
    while True:
        moment = datetime.combine(day, ready, tzinfo=IST)
        if day.weekday() < 5 and moment > now:
            return moment
        day += timedelta(days=1)


def data_day(now: datetime | None = None) -> str:
    """The session whose end-of-day data is the newest that can exist now, as an ISO date."""
    return last_release(now).date().isoformat()


def clear_cache() -> None:
    with _memory_lock:
        _memory.clear()


def bars(symbol: str, years: int = 5) -> pd.DataFrame:
    """Daily bars, kept in memory until the next end-of-day data release so repeat views do not refetch."""
    now = datetime.now(IST)
    with _memory_lock:
        hit = _memory.get((symbol, years))
    if hit and hit[0] > now:
        return hit[1].copy()
    df = _fetch_bars(symbol, years)
    with _memory_lock:
        _memory[(symbol, years)] = (next_release(now), df)
    return df.copy()


def _fetch_bars(symbol: str, years: int) -> pd.DataFrame:
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
    df = df[~df.index.duplicated(keep="last")].sort_index()
    if len(df):
        from . import symbols

        symbols.remember_close(symbol, float(df["close"].iloc[-1]), df.index[-1].date().isoformat())
    return df


def lagged(df: pd.DataFrame, lag_days: int) -> pd.DataFrame:
    """Only bars at least `lag_days` calendar days old: used for learning content that names a stock."""
    cutoff = pd.Timestamp(date.today() - timedelta(days=lag_days))
    return df[df.index <= cutoff]
