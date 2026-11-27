"""Accounts (T43): sign-in with Supabase Auth, behind this one module.

Belfort runs on the user's own computer, so there is one signed-in user per running app. The session (access and
refresh tokens) is kept in the data folder, never in git. With SUPABASE_URL and SUPABASE_ANON_KEY unset, accounts are
off and Belfort works exactly as before, local only.

The anon key is meant to be public: row-level security on the server is what keeps each user's rows private
(supabase/migrations/). The service-role key is never used by the app.

Endpoints used (Supabase Auth, "GoTrue"):
  POST /auth/v1/signup                         email and password
  POST /auth/v1/token?grant_type=password      sign in
  POST /auth/v1/token?grant_type=refresh_token refresh an expired access token
  POST /auth/v1/token?grant_type=pkce          finish Google sign-in (PKCE)
  GET  /auth/v1/authorize?provider=google      start Google sign-in in the browser
  POST /auth/v1/logout                         sign out
  POST /rest/v1/rpc/delete_my_account          delete the account (SQL function, the user's own row only)
"""

import base64
import hashlib
import json
import os
import secrets
import threading
import time
from urllib.parse import urlencode

import httpx

from .. import settings

TIMEOUT = 10.0
REFRESH_MARGIN_SECONDS = 60  # refresh a little before the access token expires
_lock = threading.Lock()
_pkce: dict[str, float] = {}  # code verifier -> time created, for a Google sign-in in progress
PKCE_MAX_AGE_SECONDS = 900


class AuthError(Exception):
    """A sentence the user can act on."""


def config() -> tuple[str, str] | None:
    """(project URL, anon key), or None when accounts are off. They are also off while Belfort is shared on a network
    with ACCESS_CODES: one app has one signed-in user, so sharing it would share the account."""
    if os.environ.get("ACCESS_CODES", "").strip():
        return None
    url = os.environ.get("SUPABASE_URL", "").strip().rstrip("/")
    key = os.environ.get("SUPABASE_ANON_KEY", "").strip()
    return (url, key) if url and key else None


def configured() -> bool:
    return config() is not None


def _session_file():
    return settings.DATA_DIR / "session.json"


def _load() -> dict | None:
    try:
        return json.loads(_session_file().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _save(session: dict | None) -> None:
    path = _session_file()
    if session is None:
        path.unlink(missing_ok=True)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(session), encoding="utf-8")


def _headers(token: str | None = None) -> dict:
    url_key = config()
    if not url_key:
        raise AuthError("Accounts are not set up on this computer.")
    h = {"apikey": url_key[1], "Content-Type": "application/json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def _url(path: str) -> str:
    url_key = config()
    if not url_key:
        raise AuthError("Accounts are not set up on this computer.")
    return url_key[0] + path


def request(method: str, path: str, token: str | None = None, **kw) -> httpx.Response:
    """One call to the Supabase project. Network problems become an AuthError with a plain sentence."""
    headers = {**_headers(token), **kw.pop("headers", {})}
    try:
        return httpx.request(method, _url(path), headers=headers, timeout=TIMEOUT, **kw)
    except httpx.HTTPError:
        raise AuthError("Could not reach the account service. Check your internet connection and try again.") from None


def _error(r: httpx.Response) -> AuthError:
    try:
        data = r.json()
    except ValueError:
        data = {}
    msg = str(data.get("error_description") or data.get("msg") or data.get("message") or "").strip()
    low = msg.lower()
    if "invalid login" in low or "invalid_grant" in str(data.get("error", "")):
        return AuthError("That email and password do not match an account.")
    if "already registered" in low or "already been registered" in low:
        return AuthError("An account with that email already exists. Sign in instead.")
    if "email not confirmed" in low:
        return AuthError("Confirm your email first: open the link in the message we sent, then sign in.")
    if "password" in low and ("short" in low or "at least" in low or "weak" in low):
        return AuthError(msg or "Choose a longer password.")
    if r.status_code == 429:
        return AuthError("Too many attempts. Wait a minute and try again.")
    return AuthError(f"The account service said: {msg}" if msg else f"The account service returned an error ({r.status_code}).")


def _store(data: dict) -> dict:
    """Keep a session from a token response and return the public part of it."""
    user = data.get("user") or {}
    if not data.get("access_token") or not user.get("id"):
        raise AuthError("The account service did not return a session. Try again.")
    expires_at = data.get("expires_at") or (time.time() + float(data.get("expires_in") or 3600))
    session = {
        "access_token": data["access_token"],
        "refresh_token": data.get("refresh_token", ""),
        "expires_at": float(expires_at),
        "user": {"id": user["id"], "email": user.get("email", "")},
    }
    with _lock:
        _save(session)
    return session["user"]


def sign_up(email: str, password: str) -> dict:
    """Create an account. Returns {"user": ...} when signed in at once, or {"confirm": True} when the project asks the
    user to confirm their email first."""
    r = request("POST", "/auth/v1/signup", json={"email": email.strip(), "password": password})
    if r.status_code >= 400:
        raise _error(r)
    data = r.json()
    if data.get("access_token"):
        return {"user": _store(data)}
    return {"confirm": True}


def sign_in(email: str, password: str) -> dict:
    r = request("POST", "/auth/v1/token?grant_type=password", json={"email": email.strip(), "password": password})
    if r.status_code >= 400:
        raise _error(r)
    return _store(r.json())


def _verifier_challenge() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(48)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    return verifier, challenge


def google_url(redirect_to: str) -> str:
    """The URL to open in the browser for Google sign-in. The PKCE verifier stays on this computer until the
    callback; one app has one user, so only the latest attempt is kept."""
    verifier, challenge = _verifier_challenge()
    with _lock:
        _pkce.clear()
        _pkce[verifier] = time.time()
    query = urlencode(
        {"provider": "google", "redirect_to": redirect_to, "code_challenge": challenge, "code_challenge_method": "s256"}
    )
    return _url(f"/auth/v1/authorize?{query}")


def finish_google(code: str) -> dict:
    with _lock:
        pending = [(v, t) for v, t in _pkce.items() if time.time() - t < PKCE_MAX_AGE_SECONDS]
        _pkce.clear()
    if not pending:
        raise AuthError("That sign-in link has expired. Start again from Belfort.")
    r = request("POST", "/auth/v1/token?grant_type=pkce", json={"auth_code": code, "code_verifier": pending[-1][0]})
    if r.status_code >= 400:
        raise _error(r)
    return _store(r.json())


def session() -> dict | None:
    """The current session, refreshed if the access token is about to expire. None when signed out, when accounts
    are off, or when the refresh token is no longer accepted (the user then signs in again)."""
    if not configured():
        return None
    with _lock:
        s = _load()
    if not s:
        return None
    if s["expires_at"] - REFRESH_MARGIN_SECONDS > time.time():
        return s
    try:
        r = request("POST", "/auth/v1/token?grant_type=refresh_token", json={"refresh_token": s["refresh_token"]})
    except AuthError:
        return s  # offline: keep the user signed in; calls that need the server will say so
    if r.status_code >= 400:
        with _lock:
            _save(None)
        return None
    _store(r.json())
    with _lock:
        return _load()


def user() -> dict | None:
    s = session()
    return s["user"] if s else None


def access_token() -> str:
    s = session()
    if not s:
        raise AuthError("Sign in first.")
    return s["access_token"]


def sign_out() -> None:
    with _lock:
        s = _load()
        _save(None)
    if s and configured():
        try:
            request("POST", "/auth/v1/logout", token=s["access_token"])
        except AuthError:
            pass  # signed out on this computer either way


def delete_account() -> None:
    """Delete the signed-in user's account and synced data on the server (SQL function delete_my_account)."""
    r = request("POST", "/rest/v1/rpc/delete_my_account", token=access_token(), json={})
    if r.status_code >= 400:
        raise _error(r)
    with _lock:
        _save(None)
