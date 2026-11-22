"""Export the practice journal as CSV files or one JSON backup, and restore a backup with validation.

A backup holds only what the user created in Practice: the account, trades, predictions and replay results.
"""

import csv
import io
import json
import sqlite3
from datetime import date

from ..core import db
from ..settings import VERSION

BACKUP_FORMAT = "belfort-practice-backup"
BACKUP_VERSION = 1
TABLES = {
    "trades": (
        "id",
        "account_id",
        "symbol",
        "qty",
        "entry_type",
        "limit_price",
        "stop",
        "target",
        "thesis",
        "confidence",
        "placed_on",
        "status",
        "entry_price",
        "entry_date",
        "exit_price",
        "exit_date",
        "exit_reason",
        "close_requested_on",
        "review",
        "created",
        "stop_moves",
        "current_stop",
        "trail_kind",
        "trail_value",
        "trail_from",
        "parent_id",
        "setup",
        "mistakes",
    ),
    "predictions": (
        "id",
        "symbol",
        "direction",
        "horizon_days",
        "confidence",
        "reason",
        "made_on",
        "ref_date",
        "ref_close",
        "status",
        "outcome_date",
        "outcome_close",
        "correct",
        "brier",
        "score",
    ),
    "replays": ("id", "symbol", "start_date", "decision", "r_multiple", "outcome", "created"),
}
REQUIRED = {
    "trades": ("symbol", "qty", "entry_type", "stop", "placed_on", "status"),
    "predictions": ("symbol", "direction", "horizon_days", "confidence", "made_on", "ref_date", "ref_close", "status"),
    "replays": ("symbol", "start_date", "decision", "outcome"),
}
ACCOUNT_COLUMNS = ("id", "name", "start_points", "created")


class BackupError(Exception):
    pass


def _rows(table: str) -> list[dict]:
    with db.connect() as con:
        return db.rows(con.execute(f"SELECT {', '.join(TABLES[table])} FROM {table} ORDER BY id"))  # noqa: S608 (fixed names)


def export_csv(table: str) -> str:
    """One table of the journal as CSV text, with a header row."""
    if table not in TABLES:
        raise BackupError("Export trades, predictions or replays.")
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=TABLES[table], lineterminator="\n")
    writer.writeheader()
    writer.writerows(_rows(table))
    return out.getvalue()


def export_backup() -> dict:
    """Everything in Practice as one JSON-ready dict."""
    with db.connect() as con:
        accounts = db.rows(con.execute(f"SELECT {', '.join(ACCOUNT_COLUMNS)} FROM accounts ORDER BY id"))
    return {
        "format": BACKUP_FORMAT,
        "version": BACKUP_VERSION,
        "app_version": VERSION,
        "exported_on": date.today().isoformat(),
        "accounts": accounts,
        **{table: _rows(table) for table in TABLES},
    }


def _check(backup: dict) -> None:
    if not isinstance(backup, dict) or backup.get("format") != BACKUP_FORMAT:
        raise BackupError("This file is not a Belfort practice backup.")
    if backup.get("version") != BACKUP_VERSION:
        raise BackupError(f"This backup is version {backup.get('version')}; this Belfort reads version {BACKUP_VERSION}.")
    accounts = backup.get("accounts")
    if not isinstance(accounts, list) or len(accounts) > 1:
        raise BackupError("The backup must hold one practice account.")
    for table, required in REQUIRED.items():
        rows = backup.get(table)
        if not isinstance(rows, list):
            raise BackupError(f"The backup has no {table} list.")
        for i, row in enumerate(rows, start=1):
            if not isinstance(row, dict):
                raise BackupError(f"{table} row {i} is not a record.")
            missing = [c for c in required if row.get(c) in (None, "")]
            if missing:
                raise BackupError(f"{table} row {i} is missing {', '.join(missing)}.")
            unknown = set(row) - set(TABLES[table])
            if unknown:
                raise BackupError(f"{table} row {i} has unknown fields: {', '.join(sorted(unknown))}.")
    account_ids = {a.get("id") for a in accounts}
    if backup["trades"] and (not accounts or any(t.get("account_id") not in account_ids for t in backup["trades"])):
        raise BackupError("Every trade in the backup must belong to its practice account.")
    for i, t in enumerate(backup["trades"], start=1):
        try:
            if int(t["qty"]) < 1 or float(t["stop"]) <= 0:
                raise ValueError
            json.loads(t.get("stop_moves") or "[]")
            json.loads(t.get("mistakes") or "[]")
        except (TypeError, ValueError):
            raise BackupError(f"trades row {i} has an invalid quantity, stop or tag list.") from None


def import_backup(backup: dict) -> dict:
    """Replace all practice data with a validated backup, in one transaction."""
    _check(backup)
    try:
        _replace(backup)
    except sqlite3.Error as e:
        raise BackupError(f"The backup could not be restored, and nothing was changed: {e}.") from None
    counts = {table: len(backup[table]) for table in TABLES}
    return {
        **counts,
        "message": f"Backup restored: {counts['trades']} trades, {counts['predictions']} predictions, {counts['replays']} replays.",
    }


def _replace(backup: dict) -> None:
    with db.connect() as con:
        for table in ("trades", "predictions", "replays", "replay_sessions", "equity_snapshots", "accounts"):
            con.execute(f"DELETE FROM {table}")  # noqa: S608 (fixed names)
        for account in backup["accounts"]:
            cols = [c for c in ACCOUNT_COLUMNS if c in account]
            con.execute(
                f"INSERT INTO accounts ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})", [account[c] for c in cols]
            )
        for table in TABLES:
            for row in backup[table]:
                cols = [c for c in TABLES[table] if c in row]
                con.execute(
                    f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})", [row[c] for c in cols]
                )
