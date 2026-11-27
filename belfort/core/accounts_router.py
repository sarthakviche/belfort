"""Accounts and sync API (T43). Everything here is off, and the app is local only, until SUPABASE_URL and
SUPABASE_ANON_KEY are set."""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, Field

from . import auth, sync
from .users import LOCAL_USER, current_user_id

router = APIRouter(tags=["accounts"])

PRIVACY = (
    "An account is optional. Without one, everything stays on this computer. With one, Belfort keeps your email and "
    "your own practice, learning and settings documents in its account service (Supabase) so they follow you between "
    "devices; nothing else is sent: no prices, no research, no tracking, and never your AI key. You can delete your "
    "account and its synced data at any time from the account menu. This is how Belfort handles your personal data "
    "under India's Digital Personal Data Protection Act, 2023."
)


class Credentials(BaseModel):
    email: str = Field(min_length=3, max_length=200, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(min_length=6, max_length=200)


class SettingsIn(BaseModel):
    settings: dict = Field(default_factory=dict)


def _fail(e: Exception, status: int = 400):
    raise HTTPException(status_code=status, detail=str(e)) from e


def state() -> dict:
    u = auth.user()
    return {
        "configured": auth.configured(),
        "user": u,
        "last_synced": sync.last_synced() if u else None,
        "local_has_data": sync.has_data(LOCAL_USER),
        "privacy": PRIVACY,
    }


def after_sign_in() -> dict:
    """Right after a sign-in: offer to bring the local data in when the account is new, otherwise sync."""
    uid = current_user_id()
    try:
        remote = sync.fetch_remote()
    except (sync.SyncError, auth.AuthError):
        remote = None
    if remote == {} and sync.has_data(LOCAL_USER) and not sync.has_data(uid):
        return {"offer_import": True}
    try:
        return {"offer_import": False, "sync": sync.sync()}
    except (sync.SyncError, auth.AuthError) as e:
        return {"offer_import": False, "sync_error": str(e)}


@router.get("/api/auth/state")
def api_state():
    return state()


@router.post("/api/auth/signup")
def api_signup(body: Credentials):
    try:
        out = auth.sign_up(body.email, body.password)
    except auth.AuthError as e:
        _fail(e)
    if out.get("user"):
        out.update(after_sign_in())
    return out


@router.post("/api/auth/signin")
def api_signin(body: Credentials):
    try:
        user = auth.sign_in(body.email, body.password)
    except auth.AuthError as e:
        _fail(e)
    return {"user": user, **after_sign_in()}


@router.get("/api/auth/google")
def api_google(request: Request):
    try:
        return {"url": auth.google_url(str(request.base_url) + "auth/callback")}
    except auth.AuthError as e:
        _fail(e)


@router.get("/auth/callback", include_in_schema=False)
def google_callback(code: str = "", error_description: str = ""):
    if not code:
        return HTMLResponse(_page(error_description or "Google sign-in was cancelled."), status_code=400)
    try:
        auth.finish_google(code)
    except auth.AuthError as e:
        return HTMLResponse(_page(str(e)), status_code=400)
    done = after_sign_in()
    return RedirectResponse("/?signedin=1" + ("&import=1" if done.get("offer_import") else ""), status_code=303)


def _page(message: str) -> str:
    from html import escape

    return (
        "<!doctype html><meta charset=utf-8><title>Belfort</title>"
        "<body style='background:#08080a;color:#f4f4f2;font:16px system-ui;padding:40px'>"
        f"<p>{escape(message)}</p><p><a style='color:#facc15' href='/'>Back to Belfort</a></p>"
    )


@router.post("/api/auth/signout")
def api_signout():
    sync.background.once()  # push what changed since the last sync before leaving
    auth.sign_out()
    return state()


@router.post("/api/auth/delete")
def api_delete():
    try:
        auth.delete_account()
    except auth.AuthError as e:
        _fail(e)
    return state()


@router.post("/api/auth/import-local")
def api_import_local():
    try:
        sync.import_local()
        return {"sync": sync.sync()}
    except (sync.SyncError, auth.AuthError) as e:
        _fail(e)


@router.post("/api/sync")
def api_sync():
    try:
        return sync.sync()
    except (sync.SyncError, auth.AuthError) as e:
        _fail(e, 503)


@router.get("/api/sync/settings")
def api_get_settings():
    return {"settings": sync.export_settings() if current_user_id() != LOCAL_USER else {}}


@router.put("/api/sync/settings")
def api_put_settings(body: SettingsIn):
    if current_user_id() == LOCAL_USER:
        return {"settings": {}}
    return {"settings": sync.save_settings(body.settings)}
