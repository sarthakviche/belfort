"""Local SQLite store for everything the user creates: paper trades, predictions, lesson progress, replay results.

One file (data/belfort.db) on the user's own machine. No account, no server. Migrations are numbered and run once.
"""

import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path

from .. import settings

MIGRATIONS = [
    # 1: practice and learning
    """
    CREATE TABLE IF NOT EXISTS accounts (
        id INTEGER PRIMARY KEY, name TEXT NOT NULL, start_points REAL NOT NULL, created TEXT NOT NULL DEFAULT (date('now'))
    );
    CREATE TABLE IF NOT EXISTS trades (
        id INTEGER PRIMARY KEY, account_id INTEGER NOT NULL REFERENCES accounts(id),
        symbol TEXT NOT NULL, qty INTEGER NOT NULL, entry_type TEXT NOT NULL, limit_price REAL,
        stop REAL NOT NULL, target REAL, thesis TEXT NOT NULL DEFAULT '', confidence REAL,
        placed_on TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending',
        entry_price REAL, entry_date TEXT, exit_price REAL, exit_date TEXT, exit_reason TEXT,
        close_requested_on TEXT, review TEXT NOT NULL DEFAULT '', created TEXT NOT NULL DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS predictions (
        id INTEGER PRIMARY KEY, symbol TEXT NOT NULL, direction TEXT NOT NULL, horizon_days INTEGER NOT NULL,
        confidence REAL NOT NULL, reason TEXT NOT NULL DEFAULT '', made_on TEXT NOT NULL,
        ref_date TEXT NOT NULL, ref_close REAL NOT NULL, status TEXT NOT NULL DEFAULT 'open',
        outcome_date TEXT, outcome_close REAL, correct INTEGER, brier REAL, score REAL
    );
    CREATE TABLE IF NOT EXISTS lesson_progress (
        lesson_id TEXT PRIMARY KEY, completed_on TEXT NOT NULL, quiz_score REAL
    );
    CREATE TABLE IF NOT EXISTS activity (day TEXT PRIMARY KEY, kind TEXT NOT NULL DEFAULT 'any');
    CREATE TABLE IF NOT EXISTS replays (
        id INTEGER PRIMARY KEY, symbol TEXT NOT NULL, start_date TEXT NOT NULL, decision TEXT NOT NULL,
        r_multiple REAL, outcome TEXT NOT NULL, created TEXT NOT NULL DEFAULT (datetime('now'))
    );
    """,
    # 2: settle the paper account at most once per trading day (T05)
    """
    ALTER TABLE accounts ADD COLUMN settled_for TEXT;
    """,
    # 3: replay sessions, so hidden bars stay on the server until the decision (T06)
    """
    CREATE TABLE IF NOT EXISTS replay_sessions (
        id TEXT PRIMARY KEY, symbol TEXT NOT NULL, start_date TEXT NOT NULL, end_date TEXT NOT NULL,
        visible INTEGER NOT NULL, created TEXT NOT NULL DEFAULT (datetime('now')), scored_on TEXT
    );
    """,
    # 4: managing open trades: raised stops, trailing stops, partial exits (T07)
    """
    ALTER TABLE trades ADD COLUMN stop_moves TEXT NOT NULL DEFAULT '[]';
    ALTER TABLE trades ADD COLUMN current_stop REAL;
    ALTER TABLE trades ADD COLUMN trail_kind TEXT;
    ALTER TABLE trades ADD COLUMN trail_value REAL;
    ALTER TABLE trades ADD COLUMN trail_from TEXT;
    ALTER TABLE trades ADD COLUMN parent_id INTEGER;
    """,
    # 5: journal analytics: a setup tag per trade and mistake tags on closed trades (T08)
    """
    ALTER TABLE trades ADD COLUMN setup TEXT;
    ALTER TABLE trades ADD COLUMN mistakes TEXT NOT NULL DEFAULT '[]';
    """,
    # 6: one account-value snapshot per settled trading day, for the equity curve (T11)
    """
    CREATE TABLE IF NOT EXISTS equity_snapshots (
        account_id INTEGER NOT NULL, day TEXT NOT NULL, equity REAL NOT NULL, PRIMARY KEY (account_id, day)
    );
    """,
    # 7: the Learn game: profile (XP, hearts, streak), daily XP, lessons, tests, weak spots, test sessions (T42)
    """
    CREATE TABLE IF NOT EXISTS learn_profile (
        user_id TEXT NOT NULL DEFAULT 'local' PRIMARY KEY, xp_total INTEGER NOT NULL DEFAULT 0,
        goal INTEGER NOT NULL DEFAULT 20, hearts INTEGER NOT NULL DEFAULT 5, hearts_day TEXT,
        streak INTEGER NOT NULL DEFAULT 0, last_goal_day TEXT, freezes INTEGER NOT NULL DEFAULT 0,
        placement_seen INTEGER NOT NULL DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS learn_xp_days (
        user_id TEXT NOT NULL DEFAULT 'local', day TEXT NOT NULL, xp INTEGER NOT NULL DEFAULT 0,
        PRIMARY KEY (user_id, day)
    );
    CREATE TABLE IF NOT EXISTS learn_lessons (
        user_id TEXT NOT NULL DEFAULT 'local', lesson_id TEXT NOT NULL, completed_on TEXT NOT NULL,
        best_score REAL NOT NULL, PRIMARY KEY (user_id, lesson_id)
    );
    CREATE TABLE IF NOT EXISTS learn_tests (
        user_id TEXT NOT NULL DEFAULT 'local', kind TEXT NOT NULL, key TEXT NOT NULL, best_score REAL NOT NULL,
        passed INTEGER NOT NULL, xp_awarded INTEGER NOT NULL DEFAULT 0, PRIMARY KEY (user_id, kind, key)
    );
    CREATE TABLE IF NOT EXISTS learn_weak (
        user_id TEXT NOT NULL DEFAULT 'local', lesson_id TEXT NOT NULL, q_index INTEGER NOT NULL,
        wrong_count INTEGER NOT NULL DEFAULT 1, last_wrong TEXT NOT NULL, PRIMARY KEY (user_id, lesson_id, q_index)
    );
    CREATE TABLE IF NOT EXISTS learn_sessions (
        id TEXT PRIMARY KEY, user_id TEXT NOT NULL DEFAULT 'local', kind TEXT NOT NULL, key TEXT NOT NULL,
        refs TEXT NOT NULL, created TEXT NOT NULL DEFAULT (datetime('now'))
    );
    """,
    # 8: small per-user, non-secret settings such as the interface language (T50)
    """
    CREATE TABLE IF NOT EXISTS settings (
        user_id TEXT NOT NULL DEFAULT 'local', key TEXT NOT NULL, value TEXT NOT NULL,
        PRIMARY KEY (user_id, key)
    );
    """,
]

_lock = threading.Lock()
_ready: set[str] = set()


def _path() -> Path:
    return settings.DB_FILE


def _migrate(con: sqlite3.Connection):
    con.execute("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL)")
    row = con.execute("SELECT MAX(version) FROM schema_version").fetchone()
    current = row[0] or 0
    for i, sql in enumerate(MIGRATIONS[current:], start=current + 1):
        con.executescript(sql)
        con.execute("INSERT INTO schema_version (version) VALUES (?)", (i,))
    con.commit()


@contextmanager
def connect():
    path = _path()
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path, timeout=10)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    try:
        key = str(path)
        if key not in _ready:
            with _lock:
                _migrate(con)
                _ready.add(key)
        yield con
        con.commit()
    finally:
        con.close()


def rows(cur) -> list[dict]:
    return [dict(r) for r in cur.fetchall()]


def touch_activity(kind: str = "any"):
    """Record that the user did something today (for the learning streak)."""
    from datetime import date

    with connect() as con:
        con.execute("INSERT OR IGNORE INTO activity (day, kind) VALUES (?, ?)", (date.today().isoformat(), kind))
