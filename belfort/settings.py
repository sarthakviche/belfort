"""Settings, style presets and thresholds. Every number a rule uses lives here, so it can be read and changed."""

import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSION = "0.1.0"


def load_env():
    """Read KEY=VALUE lines from a .env file in the project folder (existing variables win)."""
    f = ROOT / ".env"
    if f.exists():
        for line in f.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


load_env()
DATA_DIR = Path(os.environ.get("BELFORT_DATA_DIR", ROOT / "data"))
CACHE_DIR = DATA_DIR / "cache"
DB_FILE = DATA_DIR / "belfort.db"
STATS_FILE = ROOT / "data" / "pattern_stats.json"
CONTENT_DIR = ROOT / "content"


@dataclass(frozen=True)
class Style:
    key: str
    name: str
    holds: str
    k: int  # bars each side of a pivot
    fast: int  # fast moving average
    slow: int  # slow moving average
    min_bars: int
    atr_stop: float  # fallback stop in ATRs
    max_stop_pct: float  # widest acceptable stop distance
    breakout_n: int  # bars for a breakout high
    fib_lookback: int
    earnings_blackout: int  # trading days; 0 = flag only
    horizon: int  # bars used when judging patterns in the backtest


STYLES = {
    "swing": Style("swing", "Swing", "2 to 15 days", 5, 20, 50, 120, 1.5, 0.08, 20, 90, 5, 30),
    "positional": Style("positional", "Positional", "weeks to months", 10, 50, 200, 250, 3.0, 0.15, 55, 250, 0, 60),
}

MIN_REWARD_TO_RISK = 1.5
# Support and resistance: swing points within this many ATRs of a zone's lowest point form one level; levels come from
# this many recent daily bars (about one year for swing, two for positional); 3 or more swing points make a strong level.
LEVEL_ZONE_ATR = 0.75
LEVEL_LOOKBACK_BARS = {"swing": 260, "positional": 500}


def level_span(style_key: str) -> str:
    """The level lookback in words, for sentences such as "in the last year of swings"."""
    years = round(LEVEL_LOOKBACK_BARS[style_key] / 250)
    return "the last year" if years <= 1 else f"the last {years} years"


LEVEL_STRONG_TOUCHES = 3
BREAKOUT_VOLUME = 1.5  # times the 20-day average
TICK = 0.05
# Context for the checks (research/analysis/context.py). A run is a rise of at least RUN_MIN_PCT from the lowest low of
# the last RUN_LOOKBACK_BARS sessions; a sideways range (base) is at least BASE_MIN_BARS sessions whose high-to-low
# range stays within BASE_MAX_RANGE_PCT, searched back up to BASE_MAX_BARS sessions.
# Weekly chart: averages in weeks (10 and 40 weeks are about the 50 and 200-day averages).
WEEKLY_FAST = 10
WEEKLY_SLOW = 40
RUN_LOOKBACK_BARS = 40
RUN_MIN_PCT = 8.0
BASE_MIN_BARS = 20
BASE_MAX_BARS = 400
BASE_MAX_RANGE_PCT = 15.0
PROFILE_MAX_CHARS = 420  # the company description at the top of a report, cut at a sentence
QUARTER_STALE_DAYS = 200  # a newest quarter older than this means the fundamentals source is behind

# Labels describe whether a fixed rule's conditions hold. They are not buy or sell words.
LABEL_VALID = "Conditions met"
LABEL_WATCH = "Partly met"
LABEL_AVOID = "Rule excludes"
LABEL_NODATA = "Insufficient data"
LABEL_KEYS = {LABEL_VALID: "met", LABEL_WATCH: "partial", LABEL_AVOID: "excluded", LABEL_NODATA: "nodata"}

PRICE_SOURCE = "Yahoo Finance daily prices (NSE), computed by this app"
FUND_SOURCE = "Yahoo Finance company statements"

# Learning content that names a stock only uses prices at least this old (SEBI education norms, July 2026).
EDU_LAG_DAYS = 30

# Practice: virtual points only. 1 point stands for 1 rupee. Never redeemable for anything.
PAPER_START_POINTS = 1_000_000
# End-of-day data for a session is complete by this time (IST) on weekdays; cached bars stay valid until the next one.
MARKET_DATA_READY_IST = (18, 0)
PAPER_COST_PCT = 0.0005  # rough cost per side (brokerage, taxes) so practice is not cost-free
PAPER_DEFAULT_RISK_PCT = 1.0  # the "Size it" helper starts at the 1% rule taught in Learn
PAPER_MAX_RISK_PCT = 2.0  # one trade risking more than this gets a warning
PAPER_MAX_OPEN_RISK_PCT = 6.0  # open positions and orders together risking more than this get a warning
REPLAY_WINDOW_BARS = 200  # one replay chart: what you see plus what is revealed
REPLAY_VISIBLE_BARS = 140  # sessions shown before the decision; the other 60 stay on the server
REPLAY_MIN_HISTORY_BARS = 260  # skip symbols with less lagged history than this
TICKET_CHART_BARS = 63
# Journal analytics
ANALYTICS_MIN_GROUP = 3  # a pattern needs this many trades before it is called a habit
ANALYTICS_R_BUCKETS = (-2, -1, 0, 1, 2, 3)  # edges of the R distribution bands
ANALYTICS_HOLDING_BUCKETS = ((0, 2), (3, 5), (6, 10), (11, 20), (21, 10_000))  # calendar days held
TRAIL_ATR_PERIOD = 14  # sessions in the ATR a trailing stop can use
TRAIL_PCT_RANGE = (1.0, 25.0)  # allowed trailing distance in percent of the close
TRAIL_ATR_RANGE = (
    0.5,
    6.0,
)  # allowed trailing distance in ATR multiples  # about three months of sessions on the order ticket's mini chart
# ---------------- Stock search (the picker) ----------------
SEARCH_LIMIT = 8  # rows in the picker dropdown
NIFTY_MIN_MEMBERS = 45  # an official Nifty 50 file with fewer symbols than this is treated as broken
SEARCH_MIN_INITIALS = 2  # "hul" matches Hindustan Unilever from two letters up
SEARCH_MIN_SUBSTRING = 3  # shorter queries only match prefixes, to keep the list relevant
SEARCH_MIN_FUZZY = 4  # typo tolerance starts at four characters
SEARCH_FUZZY_MIN_RATIO = 0.75  # difflib similarity per word ("hdcf" vs "hdfc" is 0.75)

# ---------------- Ask Belfort (assistant) ----------------
AI_TIMEOUT_SECONDS = {"gemini": 40.0, "openai": 60.0}  # local models can be slow on the first answer
AI_MAX_OUTPUT_TOKENS = 800
AI_ERROR_DETAIL_CHARS = 200  # how much of a provider's own error text to show

PREDICTION_HORIZONS = {"1 week": 5, "2 weeks": 10, "4 weeks": 20, "3 months": 63}
