"""Practice: the stop-loss is optional. A trade without one has its whole value counted as risk and no R. No network."""

import sqlite3

from fastapi.testclient import TestClient

from belfort import settings
from belfort.core import compliance, db
from belfort.main import app
from belfort.practice import engine, service
from tests.helpers import price_frame
from tests.test_verticals import bars, trade


def _no_stop_trade(qty=10):
    acc = service.account()
    with db.connect() as con:
        return con.execute(
            "INSERT INTO trades (account_id, symbol, qty, entry_type, stop, thesis, placed_on, status, entry_price, entry_date) "
            "VALUES (?, 'TCS', ?, 'market', NULL, 'no stop on purpose', '2026-01-02', 'open', 100, '2026-01-05')",
            (acc["id"], qty),
        ).lastrowid


def test_a_trade_without_a_stop_is_not_closed_by_a_fall():
    df = bars([("2026-01-02", 100, 101, 99, 100), ("2026-01-05", 80, 81, 60, 70), ("2026-01-06", 70, 72, 50, 55)])
    f = engine.settle_trade(trade(stop=None, target=None), df)
    assert f.status == "open" and f.entry_price == 100 and f.stop is None


def test_a_stop_added_later_applies_from_the_next_session():
    df = bars([("2026-01-02", 100, 101, 99, 100), ("2026-01-05", 100, 101, 96, 99), ("2026-01-06", 99, 100, 94, 95)])
    t = trade(status="open", entry_price=100.0, entry_date="2026-01-02", stop=None, target=None)
    f = engine.settle_trade({**t, "stop_moves": '[{"on": "2026-01-05", "stop": 97}]'}, df)
    assert f.exit_date == "2026-01-06" and f.exit_price == 97.0  # the 96 low on the 5th came before the stop applied


def test_a_trailing_stop_works_without_an_initial_stop():
    df = bars([("2026-01-02", 100, 101, 99, 100), ("2026-01-05", 100, 111, 100, 110), ("2026-01-06", 110, 111, 98, 100)])
    t = trade(status="open", entry_price=100.0, entry_date="2026-01-02", stop=None, target=None)
    f = engine.settle_trade({**t, "trail_kind": "pct", "trail_value": 5, "trail_from": "2026-01-02"}, df)
    assert f.exit_reason == "stop-loss hit" and f.exit_price == 104.5  # 5% below the 110 close


def test_no_stop_means_no_r():
    assert engine.r_multiple(100, None, 120) is None


def test_order_without_a_stop_is_accepted_with_a_plain_warning(fresh_db):
    c = TestClient(app)
    r = c.post("/api/practice/trades", json={"symbol": "TCS", "qty": 5, "thesis": "Testing an order with no stop."})
    assert r.status_code == 200, r.text
    warnings = r.json()["warnings"]
    assert warnings and warnings[0].startswith("No stop-loss")
    assert compliance.find_banned(" ".join(warnings)) == []
    pending = c.get("/api/practice/portfolio").json()
    assert pending["pending"][0]["stop"] is None and pending["risk"]["unprotected"] == 1


def test_open_risk_counts_a_position_without_a_stop_in_full(fresh_db):
    _no_stop_trade(qty=10)
    last = float(price_frame(n=400, drift=0.001)["close"].iloc[-1])
    pf = service.portfolio()
    assert pf["risk"]["open_points"] == round(last * 10, 2) and pf["risk"]["unprotected"] == 1
    assert pf["open"][0]["current_stop"] is None and pf["open"][0]["open_r"] is None


def test_a_stop_can_be_set_on_a_position_that_had_none(fresh_db):
    tid = _no_stop_trade(qty=10)
    last = float(price_frame(n=400, drift=0.001)["close"].iloc[-1])
    msg = service.raise_stop(tid, round(last * 0.9, 2))["message"]
    assert msg.startswith("Stop set at")
    pf = service.portfolio()
    assert pf["risk"]["unprotected"] == 0
    assert pf["risk"]["open_points"] == round((last - round(last * 0.9, 2)) * 10, 2)


def test_migration_keeps_existing_trades_and_lets_the_stop_be_empty(tmp_path, monkeypatch):
    path = tmp_path / "old.db"
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE schema_version (version INTEGER NOT NULL)")
    for i, sql in enumerate(db.MIGRATIONS[:6], start=1):
        con.executescript(sql)
        con.execute("INSERT INTO schema_version (version) VALUES (?)", (i,))
    con.execute("INSERT INTO accounts (name, start_points) VALUES ('Paper', 1000000)")
    con.execute(
        "INSERT INTO trades (account_id, symbol, qty, entry_type, stop, thesis, placed_on, setup, mistakes) "
        "VALUES (1, 'INFY', 3, 'market', 1400, 'an old trade', '2026-01-02', 'pullback', '[\"chased\"]')"
    )
    con.commit()
    con.close()
    monkeypatch.setattr(settings, "DB_FILE", path)
    with db.connect() as c:
        old = dict(c.execute("SELECT * FROM trades").fetchone())
        c.execute(
            "INSERT INTO trades (account_id, symbol, qty, entry_type, stop, thesis, placed_on) "
            "VALUES (1, 'TCS', 1, 'market', NULL, 'new', '2026-01-03')"
        )
        version = c.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]
    assert (old["symbol"], old["qty"], old["stop"], old["setup"], old["mistakes"]) == ("INFY", 3, 1400, "pullback", '["chased"]')
    assert version == len(db.MIGRATIONS)
