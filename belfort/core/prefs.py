"""Small non-secret settings per user, starting with the interface language (T50).

GET/PUT /api/settings/language store the choice in SQLite (settings table, user_id column). T43 accounts will sync
this as part of a `settings` document under the key `language`.
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from . import db, i18n
from .users import current_user_id

router = APIRouter(prefix="/api/settings", tags=["settings"])
LANGUAGE_KEY = "language"


class LanguageIn(BaseModel):
    language: str


def get_setting(user: str, key: str, default: str | None = None) -> str | None:
    with db.connect() as con:
        row = con.execute("SELECT value FROM settings WHERE user_id=? AND key=?", (user, key)).fetchone()
    return row["value"] if row else default


def set_setting(user: str, key: str, value: str):
    with db.connect() as con:
        con.execute(
            "INSERT INTO settings (user_id, key, value) VALUES (?, ?, ?) "
            "ON CONFLICT(user_id, key) DO UPDATE SET value=excluded.value",
            (user, key, value),
        )


def _languages() -> list[dict]:
    return [{"code": c, "name": n[0], "native": n[1]} for c, n in i18n.LANGUAGES.items()]


@router.get("/language")
def get_language(request: Request):
    return {"language": get_setting(current_user_id(request), LANGUAGE_KEY, i18n.DEFAULT), "languages": _languages()}


@router.put("/language")
def put_language(body: LanguageIn, request: Request):
    code = body.language.strip().lower()
    if code not in i18n.LANGUAGES:
        raise HTTPException(status_code=400, detail="Unknown language. Choose one of: " + ", ".join(i18n.LANGUAGES) + ".")
    set_setting(current_user_id(request), LANGUAGE_KEY, code)
    return {"language": code, "languages": _languages()}
