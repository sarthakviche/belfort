"""Sync (T43): the signed-in user's documents to and from Supabase's `user_state` table, last write wins.

One row per (user, kind) holds a whole JSON document:
  practice  the Practice backup (practice/backup.py, the same format as Settings > Backup)
  learn     lesson progress and study days, plus any extra parts registered by other modules (T42's game state)
  settings  interface choices the browser sends (style, capital, risk, language, AI provider; never an AI key)

How a sync decides, per kind:
- local changed  = the document's hash differs from the one recorded at the last sync
- remote changed = the row's server-set updated_at differs from the one recorded at the last sync
- only remote changed, or both changed and the remote row is newer than the local change: the remote copy replaces
  the local one; only local changed (or both, local newer): the local copy is pushed.
Whatever is replaced is first saved as a JSON file in the data folder (sync-backups/), so nothing is lost.
Payload shapes are documented in docs/ARCHITECTURE.md for the Android app.
"""

import hashlib
import json
import threading
import time
from collections.abc import Callable
from datetime import UTC, datetime

from .. import settings
from . import auth, db
from .users import LOCAL_USER, current_user_id

KINDS = ("practice", "learn", "settings")
SETTINGS_KEYS = ("style", "capital", "risk", "language", "aiProvider", "aiModel", "aiBase")
_lock = threading.Lock()
# Extra parts of the learn document, by name: (export, import). T42 registers its game state here.
LEARN_PARTS: dict[str, tuple[Callable[[], object], Callable[[object], None]]] = {}


class SyncError(Exception):
    pass


# ---------------- local documents ----------------


def _user_dir():
    return settings.DB_FILE.parent / "users"


def _settings_file():
    return _user_dir() / f"{_safe(current_user_id())}.settings.json"


def _state_file():
    return _user_dir() / f"{_safe(current_user_id())}.sync.json"


def _safe(uid: str) -> str:
    return "".join(c for c in uid if c.isalnum() or c == "-")[:64]


def export_learn() -> dict:
    with db.connect() as con:
        lessons = db.rows(con.execute("SELECT lesson_id, completed_on, quiz_score FROM lesson_progress ORDER BY lesson_id"))
        days = db.rows(con.execute("SELECT day, kind FROM activity ORDER BY day"))
    doc = {"lessons": lessons, "activity": days}
    for name, (export, _) in LEARN_PARTS.items():
        doc[name] = export()
    return doc


def import_learn(doc: dict) -> None:
    with db.connect() as con:
        con.execute("DELETE FROM lesson_progress")
        con.execute("DELETE FROM activity")
        for r in doc.get("lessons", []):
            con.execute(
                "INSERT INTO lesson_progress (lesson_id, completed_on, quiz_score) VALUES (?,?,?)",
                (r["lesson_id"], r.get("completed_on"), r.get("quiz_score")),
            )
        for r in doc.get("activity", []):
            con.execute("INSERT OR IGNORE INTO activity (day, kind) VALUES (?,?)", (r["day"], r.get("kind", "any")))
    for name, (_, imp) in LEARN_PARTS.items():
        if name in doc:
            imp(doc[name])


def export_settings() -> dict:
    try:
        return json.loads(_settings_file().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def import_settings(doc: dict) -> None:
    clean = {k: doc[k] for k in SETTINGS_KEYS if k in doc}
    _user_dir().mkdir(parents=True, exist_ok=True)
    _settings_file().write_text(json.dumps(clean), encoding="utf-8")


def save_settings(doc: dict) -> dict:
    """Settings the browser sends. Only known keys are kept, so an AI key can never be synced."""
    import_settings(doc)
    return export_settings()


def _practice():
    from ..practice import backup

    return backup.export_backup, backup.import_backup


def _io(kind: str) -> tuple[Callable[[], dict], Callable[[dict], object]]:
    if kind == "practice":
        return _practice()
    if kind == "learn":
        return export_learn, import_learn
    return export_settings, import_settings


def _hash(doc) -> str:
    stable = doc
    if isinstance(doc, dict) and "exported_on" in doc:
        stable = {k: v for k, v in doc.items() if k != "exported_on"}  # the export date alone is not a change
    return hashlib.sha256(json.dumps(stable, sort_keys=True, default=str).encode()).hexdigest()


def _local_changed_at() -> float:
    """When the user's data last changed on this computer: the newer of the database file and the settings file."""
    times = [0.0]
    for p in (db.path_for(current_user_id()), _settings_file()):
        try:
            times.append(p.stat().st_mtime)
        except OSError:
            pass
    return max(times)


def _load_state() -> dict:
    try:
        return json.loads(_state_file().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _save_state(state: dict) -> None:
    _user_dir().mkdir(parents=True, exist_ok=True)
    _state_file().write_text(json.dumps(state), encoding="utf-8")


def _keep_copy(kind: str, doc, side: str) -> None:
    folder = settings.DB_FILE.parent / "sync-backups"
    folder.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    (folder / f"{_safe(current_user_id())}-{kind}-{side}-{stamp}.json").write_text(json.dumps(doc, default=str), encoding="utf-8")


# ---------------- remote rows ----------------


def _ts(value: str | None) -> float:
    if not value:
        return 0.0
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return 0.0


def fetch_remote() -> dict[str, dict]:
    uid = current_user_id()
    r = auth.request("GET", f"/rest/v1/user_state?select=kind,payload,updated_at&user_id=eq.{uid}", token=auth.access_token())
    if r.status_code >= 400:
        raise SyncError(f"Could not read your synced data (error {r.status_code}).")
    return {row["kind"]: row for row in r.json()}


def push_remote(kind: str, payload) -> dict:
    r = auth.request(
        "POST",
        "/rest/v1/user_state?on_conflict=user_id,kind",
        token=auth.access_token(),
        headers={"Prefer": "resolution=merge-duplicates,return=representation"},
        json=[{"user_id": current_user_id(), "kind": kind, "payload": payload}],
    )
    if r.status_code >= 400:
        raise SyncError(f"Could not save your {kind} data to your account (error {r.status_code}).")
    rows = r.json()
    return rows[0] if rows else {"updated_at": datetime.now(UTC).isoformat()}


# ---------------- the sync ----------------


def sync(kinds: tuple[str, ...] = KINDS) -> dict:
    """Sync each kind both ways. Returns what happened per kind and when."""
    if current_user_id() == LOCAL_USER:
        raise SyncError("Sign in to sync.")
    with _lock:
        remote = fetch_remote()
        state = _load_state()
        changed_at = _local_changed_at()
        result = {}
        for kind in kinds:
            export, imp = _io(kind)
            local = export()
            h = _hash(local)
            seen = state.get(kind, {})
            row = remote.get(kind)
            local_changed = h != seen.get("hash")
            remote_changed = row is not None and row.get("updated_at") != seen.get("remote_at")
            # first sync of this kind on this computer: an existing account copy wins over a fresh local file
            first = not seen
            if remote_changed and (first or not local_changed or _ts(row["updated_at"]) >= changed_at):
                if local_changed or seen:
                    _keep_copy(kind, local, "replaced-local")
                imp(row["payload"])
                state[kind] = {"hash": _hash(export()), "remote_at": row["updated_at"]}
                result[kind] = "pulled"
            elif local_changed or row is None:
                if row is not None and remote_changed:
                    _keep_copy(kind, row["payload"], "replaced-remote")
                saved = push_remote(kind, local)
                state[kind] = {"hash": h, "remote_at": saved.get("updated_at")}
                result[kind] = "pushed"
            else:
                result[kind] = "same"
        state["last_synced"] = datetime.now(UTC).isoformat()
        _save_state(state)
    return {"kinds": result, "last_synced": state["last_synced"]}


def last_synced() -> str | None:
    return _load_state().get("last_synced") if current_user_id() != LOCAL_USER else None


def has_data(user_id: str) -> bool:
    """Whether a user's database has any practice trades or lesson progress."""
    path = db.path_for(user_id)
    if not path.exists():
        return False
    import sqlite3

    con = sqlite3.connect(path)
    try:
        n = 0
        for table in ("trades", "predictions", "lesson_progress", "replays"):
            try:
                n += con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]  # noqa: S608 (fixed names)
            except sqlite3.Error:
                pass
        return n > 0
    finally:
        con.close()


def import_local() -> None:
    """Copy the local (signed-out) practice and learning into the signed-in user's database, replacing it."""
    import sqlite3

    uid = current_user_id()
    if uid == LOCAL_USER:
        raise SyncError("Sign in first.")
    src, dst = db.path_for(LOCAL_USER), db.path_for(uid)
    if not src.exists():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        _keep_copy("database", {"note": f"replaced by local data on {time.ctime()}", "file": str(dst)}, "replaced-local")
    with sqlite3.connect(src) as a, sqlite3.connect(dst) as b:
        a.backup(b)
    db._ready.discard(str(dst))


class Background:
    """Pushes local changes every SYNC_INTERVAL_SECONDS while signed in, and once more when the app closes."""

    def __init__(self):
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self):
        if not auth.configured() or self._thread:
            return
        self._thread = threading.Thread(target=self._run, name="belfort-sync", daemon=True)
        self._thread.start()

    def _run(self):
        while not self._stop.wait(settings.SYNC_INTERVAL_SECONDS):
            self.once()

    def once(self):
        try:
            if current_user_id() != LOCAL_USER:
                sync()
        except (SyncError, auth.AuthError):
            pass  # offline or signed out: the next round or "Sync now" tries again

    def stop(self):
        self._stop.set()
        self.once()


background = Background()
