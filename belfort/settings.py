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
BREAKOUT_VOLUME = 1.5  # times the 20-day average
TICK = 0.05

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
PAPER_COST_PCT = 0.0005  # rough cost per side (brokerage, taxes) so practice is not cost-free
# ---------------- Ask Belfort (assistant) ----------------
AI_TIMEOUT_SECONDS = {"gemini": 40.0, "openai": 60.0}  # local models can be slow on the first answer
AI_MAX_OUTPUT_TOKENS = 800
AI_ERROR_DETAIL_CHARS = 200  # how much of a provider's own error text to show

PREDICTION_HORIZONS = {"1 week": 5, "2 weeks": 10, "4 weeks": 20, "3 months": 63}
