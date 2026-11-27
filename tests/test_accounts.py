"""Accounts and sync (T43). Every Supabase call goes to an in-memory fake; nothing touches the network."""

import json
import time
from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi.testclient import TestClient

from belfort import settings
from belfort.core import auth, db, sync, users
from belfort.core.users import LOCAL_USER, current_user_id
from belfort.main import app
from belfort.practice import service

URL = "https://example.supabase.co"


class Resp:
    def __init__(self, status, data):
        self.status_code, self._data = status, data

    def json(self):
        return self._data


class FakeSupabase:
    """Just enough of Supabase Auth and PostgREST for Belfort's calls, with a server clock that only moves forward."""

    def __init__(self):
        self.users = {}  # email -> {"id", "password"}
        self.rows = {}  # (user_id, kind) -> row
        self.tokens = {}  # access token -> user id
        self.refresh = {}  # refresh token -> user id
        self.clock = datetime(2026, 11, 28, tzinfo=UTC)
        self.calls = []
        self.expires_in = 3600

    def _session(self, uid):
        access, refresh = f"at-{uid}-{len(self.tokens)}", f"rt-{uid}-{len(self.refresh)}"
        self.tokens[access], self.refresh[refresh] = uid, uid
        email = next(e for e, u in self.users.items() if u["id"] == uid)
        return {
            "access_token": access,
            "refresh_token": refresh,
            "expires_in": self.expires_in,
            "user": {"id": uid, "email": email},
        }

    def _uid(self, headers):
        return self.tokens.get(headers.get("Authorization", "").removeprefix("Bearer "))

    def tick(self):
        self.clock += timedelta(seconds=10)
        return self.clock.isoformat()

    def __call__(self, method, url, headers=None, json=None, timeout=None):
        headers = headers or {}
        assert headers.get("apikey") == "anon-key"
        path = url.removeprefix(URL)
        self.calls.append((method, path))
        if path == "/auth/v1/signup":
            if json["email"] in self.users:
                return Resp(422, {"msg": "User already registered"})
            uid = f"00000000-0000-0000-0000-{len(self.users) + 1:012d}"
            self.users[json["email"]] = {"id": uid, "password": json["password"]}
            return Resp(200, self._session(uid))
        if path == "/auth/v1/token?grant_type=password":
            u = self.users.get(json["email"])
            if not u or u["password"] != json["password"]:
                return Resp(400, {"error": "invalid_grant", "error_description": "Invalid login credentials"})
            return Resp(200, self._session(u["id"]))
        if path == "/auth/v1/token?grant_type=refresh_token":
            uid = self.refresh.pop(json["refresh_token"], None)
            return Resp(200, self._session(uid)) if uid else Resp(400, {"error": "invalid_grant"})
        if path == "/auth/v1/token?grant_type=pkce":
            if json["auth_code"] != "good-code" or not json["code_verifier"]:
                return Resp(400, {"error_description": "invalid flow state"})
            if "g@example.com" not in self.users:
                self.users["g@example.com"] = {"id": "00000000-0000-0000-0000-0000000000aa", "password": ""}
            return Resp(200, self._session(self.users["g@example.com"]["id"]))
        if path == "/auth/v1/logout":
            return Resp(204, {})
        uid = self._uid(headers)
        if path.startswith("/rest/v1/user_state") and method == "GET":
            want = parse_qs(urlparse(path).query)["user_id"][0].removeprefix("eq.")
            assert want == uid, "row-level security: a user reads only their own rows"
            return Resp(200, [dict(r) for (u, _), r in self.rows.items() if u == uid])
        if path.startswith("/rest/v1/user_state") and method == "POST":
            out = []
            for row in json:
                assert row["user_id"] == uid
                saved = {"kind": row["kind"], "payload": row["payload"], "updated_at": self.tick()}
                self.rows[(uid, row["kind"])] = saved
                out.append(saved)
            return Resp(201, out)
        if path == "/rest/v1/rpc/delete_my_account":
            self.rows = {k: v for k, v in self.rows.items() if k[0] != uid}
            self.users = {e: u for e, u in self.users.items() if u["id"] != uid}
            return Resp(204, None)
        raise AssertionError(f"unexpected call {method} {path}")


@pytest.fixture
def supa(tmp_path, monkeypatch):
    """Accounts on, a fresh data folder, synthetic prices and the fake service."""
    from belfort.data import market
    from tests.helpers import price_frame

    monkeypatch.setenv("SUPABASE_URL", URL)
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon-key")
    monkeypatch.delenv("ACCESS_CODES", raising=False)
    monkeypatch.setattr(settings, "DATA_DIR", tmp_path)
    monkeypatch.setattr(settings, "DB_FILE", tmp_path / "belfort.db")
    monkeypatch.setattr(market, "bars", lambda symbol, years=5: price_frame(n=400, drift=0.001))
    fake = FakeSupabase()
    monkeypatch.setattr(auth.httpx, "request", fake)
    return fake


def _place_trade(symbol="TCS"):
    return service.place_trade(symbol, 5, 50.0, None, "testing sync", None)


# ---------------- configuration ----------------


def test_accounts_are_off_without_configuration(monkeypatch):
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_ANON_KEY", raising=False)
    assert not auth.configured() and auth.user() is None and current_user_id() == LOCAL_USER
    assert TestClient(app).get("/api/config").json()["accounts"] is False


def test_accounts_are_off_while_shared_with_access_codes(supa, monkeypatch):
    monkeypatch.setenv("ACCESS_CODES", "abc")
    assert not auth.configured()


# ---------------- sign-in ----------------


def test_sign_up_sign_in_and_sign_out(supa):
    assert auth.sign_up("a@example.com", "secret1")["user"]["email"] == "a@example.com"
    uid = current_user_id()
    assert uid != LOCAL_USER and json.loads((settings.DATA_DIR / "session.json").read_text())["user"]["id"] == uid
    auth.sign_out()
    assert current_user_id() == LOCAL_USER and not (settings.DATA_DIR / "session.json").exists()
    assert auth.sign_in("a@example.com", "secret1")["id"] == uid


def test_wrong_password_and_duplicate_email_give_plain_sentences(supa):
    auth.sign_up("a@example.com", "secret1")
    with pytest.raises(auth.AuthError, match="do not match"):
        auth.sign_in("a@example.com", "wrong")
    with pytest.raises(auth.AuthError, match="already exists"):
        auth.sign_up("a@example.com", "secret1")


def test_an_expired_token_is_refreshed(supa):
    supa.expires_in = 1
    auth.sign_up("a@example.com", "secret1")
    first = auth.session()["access_token"]
    s = auth.session()  # within the refresh margin: refreshed
    assert s["access_token"] != first and s["user"]["email"] == "a@example.com"
    assert ("POST", "/auth/v1/token?grant_type=refresh_token") in supa.calls


def test_a_refused_refresh_signs_the_user_out(supa):
    supa.expires_in = 1
    auth.sign_up("a@example.com", "secret1")
    supa.refresh.clear()
    assert auth.user() is None and current_user_id() == LOCAL_USER


def test_offline_refresh_keeps_the_user_signed_in(supa, monkeypatch):
    supa.expires_in = 1
    auth.sign_up("a@example.com", "secret1")

    def offline(*a, **k):
        raise auth.httpx.ConnectError("offline")

    monkeypatch.setattr(auth.httpx, "request", offline)
    assert auth.user()["email"] == "a@example.com"


def test_google_sign_in_with_pkce(supa):
    url = auth.google_url("http://127.0.0.1:8766/auth/callback")
    q = parse_qs(urlparse(url).query)
    assert q["provider"] == ["google"] and q["code_challenge_method"] == ["s256"] and len(q["code_challenge"][0]) >= 43
    assert auth.finish_google("good-code")["email"] == "g@example.com"
    with pytest.raises(auth.AuthError, match="expired"):
        auth.finish_google("good-code")  # the verifier is used once


# ---------------- scoping ----------------


def test_each_user_has_their_own_database(supa):
    _place_trade()
    assert len(service.portfolio()["pending"]) == 1  # local user
    auth.sign_up("a@example.com", "secret1")
    assert db._path().parent.name == "users" and service.portfolio()["pending"] == []
    _place_trade("INFY")
    auth.sign_out()
    assert [t["symbol"] for t in service.portfolio()["pending"]] == ["TCS"]


def test_user_ids_cannot_escape_the_users_folder():
    p = db.path_for("../../etc/passwd")
    assert p.parent.name == "users" and ".." not in p.name


def test_users_contract_is_kept():
    assert users.current_user_id.__name__ == "current_user_id" and LOCAL_USER == "local"


# ---------------- sync ----------------


def test_first_sync_pushes_every_kind(supa):
    auth.sign_up("a@example.com", "secret1")
    _place_trade()
    sync.save_settings({"style": "positional", "capital": "250000", "aiKey": "never-synced", "key": "nor this"})
    r = sync.sync()
    assert r["kinds"] == {"practice": "pushed", "learn": "pushed", "settings": "pushed"}
    uid = current_user_id()
    assert supa.rows[(uid, "settings")]["payload"] == {"style": "positional", "capital": "250000"}
    assert supa.rows[(uid, "practice")]["payload"]["trades"][0]["symbol"] == "TCS"
    assert sync.sync()["kinds"] == {"practice": "same", "learn": "same", "settings": "same"}


def test_a_second_computer_gets_the_same_paper_account(supa, tmp_path, monkeypatch):
    auth.sign_up("a@example.com", "secret1")
    _place_trade()
    sync.sync()
    # a second computer: a new data folder, the same account
    other = tmp_path / "second"
    monkeypatch.setattr(settings, "DATA_DIR", other)
    monkeypatch.setattr(settings, "DB_FILE", other / "belfort.db")
    auth.sign_in("a@example.com", "secret1")
    assert sync.sync()["kinds"]["practice"] == "pulled"
    assert [t["symbol"] for t in service.portfolio()["pending"]] == ["TCS"]


def test_newer_remote_wins_and_the_local_copy_is_kept(supa, tmp_path, monkeypatch):
    auth.sign_up("a@example.com", "secret1")
    uid = current_user_id()
    sync.sync()
    _place_trade("INFY")  # a local change...
    old = time.time() - 3600
    import os

    os.utime(db.path_for(uid), (old, old))  # ...made an hour ago
    supa.rows[(uid, "practice")] = {**supa.rows[(uid, "practice")], "updated_at": datetime.now(UTC).isoformat()}
    supa.rows[(uid, "practice")]["payload"] = {**supa.rows[(uid, "practice")]["payload"], "trades": []}
    assert sync.sync()["kinds"]["practice"] == "pulled"
    assert service.portfolio()["pending"] == []
    kept = list((settings.DB_FILE.parent / "sync-backups").glob("*practice-replaced-local*"))
    assert kept and "INFY" in kept[0].read_text()


def test_newer_local_wins_and_the_remote_copy_is_kept(supa):
    auth.sign_up("a@example.com", "secret1")
    uid = current_user_id()
    sync.sync()
    supa.rows[(uid, "learn")] = {
        "kind": "learn",
        "payload": {"lessons": [], "activity": [{"day": "2020-01-01"}]},
        "updated_at": "2026-01-01T00:00:00+00:00",
    }
    db.touch_activity()  # a local change now, newer than the remote one
    assert sync.sync()["kinds"]["learn"] == "pushed"
    assert list((settings.DB_FILE.parent / "sync-backups").glob("*learn-replaced-remote*"))


def test_learn_parts_can_be_registered_by_other_modules(supa, monkeypatch):
    got = {}
    monkeypatch.setitem(sync.LEARN_PARTS, "game", (lambda: {"xp": 40}, lambda doc: got.update(doc)))
    assert sync.export_learn()["game"] == {"xp": 40}
    sync.import_learn({"lessons": [], "activity": [], "game": {"xp": 90}})
    assert got == {"xp": 90}


def test_sync_needs_a_signed_in_user(supa):
    with pytest.raises(sync.SyncError):
        sync.sync()


def test_import_local_data_into_a_new_account(supa):
    _place_trade()
    auth.sign_up("a@example.com", "secret1")
    assert sync.has_data(LOCAL_USER) and not sync.has_data(current_user_id())
    sync.import_local()
    assert [t["symbol"] for t in service.portfolio()["pending"]] == ["TCS"]


# ---------------- API ----------------


def test_api_sign_in_offers_to_bring_local_data_into_a_new_account(supa):
    _place_trade()
    c = TestClient(app)
    assert c.get("/api/auth/state").json()["user"] is None
    r = c.post("/api/auth/signup", json={"email": "a@example.com", "password": "secret1"}).json()
    assert r["user"]["email"] == "a@example.com" and r["offer_import"] is True
    r = c.post("/api/auth/import-local").json()
    assert r["sync"]["kinds"]["practice"] == "pushed"
    st = c.get("/api/auth/state").json()
    assert st["user"]["email"] == "a@example.com" and st["last_synced"] and "Digital Personal Data Protection" in st["privacy"]


def test_api_sign_in_on_an_account_with_data_syncs_straight_away(supa):
    c = TestClient(app)
    c.post("/api/auth/signup", json={"email": "a@example.com", "password": "secret1"})
    c.post("/api/auth/signout")
    r = c.post("/api/auth/signin", json={"email": "a@example.com", "password": "secret1"}).json()
    assert r["offer_import"] is False and "sync" in r
    assert c.post("/api/auth/signin", json={"email": "a@example.com", "password": "nope12"}).status_code == 400
    assert c.post("/api/auth/signin", json={"email": "not-an-email", "password": "secret1"}).status_code == 422


def test_api_settings_sync_and_delete_account(supa):
    c = TestClient(app)
    c.post("/api/auth/signup", json={"email": "a@example.com", "password": "secret1"})
    assert c.put("/api/sync/settings", json={"settings": {"risk": "1.5", "belfortAI": "x"}}).json()["settings"] == {"risk": "1.5"}
    assert c.get("/api/sync/settings").json()["settings"] == {"risk": "1.5"}
    assert c.post("/api/sync").status_code == 200
    assert c.post("/api/auth/delete").json()["user"] is None
    assert supa.rows == {} and supa.users == {}


def test_google_callback_route(supa):
    c = TestClient(app)
    url = c.get("/api/auth/google").json()["url"]
    assert "redirect_to=http%3A%2F%2Ftestserver%2Fauth%2Fcallback" in url
    r = c.get("/auth/callback?code=good-code", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"].startswith("/?signedin=1")
    assert c.get("/auth/callback?code=", follow_redirects=False).status_code == 400


def test_background_sync_is_quiet_when_signed_out_or_offline(supa, monkeypatch):
    sync.background.once()  # signed out: nothing happens
    auth.sign_up("a@example.com", "secret1")

    def offline(*a, **k):
        raise auth.AuthError("offline")

    monkeypatch.setattr(sync, "fetch_remote", offline)
    sync.background.once()  # offline: no error
