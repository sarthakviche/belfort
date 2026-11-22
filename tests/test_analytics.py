"""Journal analytics (belfort/practice/analytics.py) on hand-made closed trades, and the tags and analytics API."""

from fastapi.testclient import TestClient

from belfort.core import compliance, db
from belfort.main import app
from belfort.practice import analytics, service


def closed(r, setup="pullback", held=3, mistakes=()):
    return {
        "r": r,
        "setup": setup,
        "entry_date": "2026-03-02",
        "exit_date": f"2026-03-{2 + held:02d}",
        "mistakes": list(mistakes),
    }


TRADES = [
    closed(2.0),
    closed(1.5),
    closed(-1.0),
    closed(3.2, held=12),
    closed(-1.0, setup="breakout", mistakes=["chased"]),
    closed(-1.2, setup="breakout", mistakes=["chased", "sized-too-big"]),
    closed(-0.4, setup="breakout", mistakes=["chased"]),
    closed(0.5, setup=None, held=0),
]


def test_r_distribution_puts_each_trade_in_one_band():
    bands = analytics.r_distribution(TRADES)
    assert sum(b["count"] for b in bands) == len(TRADES)
    by_label = {b["label"]: b["count"] for b in bands}
    assert by_label["-2 to -1R"] == 1 and by_label["-1 to +0R"] == 3 and by_label["+3R or more"] == 1


def test_results_by_setup_and_holding_time():
    setups = {g["setup"]: g for g in analytics.by_setup(TRADES)}
    assert setups["pullback"]["count"] == 4 and setups["pullback"]["win_rate"] == 0.75
    assert setups["breakout"]["avg_r"] == round((-1.0 - 1.2 - 0.4) / 3, 2) and setups["untagged"]["label"] == "Not tagged"
    holding = {g["label"]: g["count"] for g in analytics.by_holding(TRADES)}
    assert holding["0 to 2 days"] == 1 and holding["3 to 5 days"] == 6 and holding["11 to 20 days"] == 1


def test_mistakes_and_habits_need_enough_trades():
    mistakes = {g["mistake"]: g for g in analytics.by_mistake(TRADES)}
    assert mistakes["chased"]["count"] == 3 and mistakes["chased"]["total_r"] == -2.6
    assert mistakes["sized-too-big"]["count"] == 1 and mistakes["none"]["count"] == 5
    habits = analytics.summarise(TRADES)["habits"]
    assert habits["worst"] == ['"Chased the entry" came up in 3 trades, which together lost 2.6R.']  # one trade is not a habit
    assert any(h.startswith("Pullback trades averaged +1.43R over 4 trades") for h in habits["best"])


def test_analytics_wording_is_descriptive_only():
    s = analytics.summarise(TRADES)
    text = " ".join(s["habits"]["best"] + s["habits"]["worst"] + [s["note"]])
    assert compliance.find_banned(text) == []
    assert analytics.summarise([])["closed"] == 0 and analytics.summarise([])["habits"] == {
        "best": [],
        "worst": [],
        "min_group": 3,
    }


def _closed_trade(r_exit: float) -> int:
    acc = service.account()
    with db.connect() as con:
        cur = con.execute(
            "INSERT INTO trades (account_id, symbol, qty, entry_type, stop, thesis, placed_on, status, entry_price, entry_date, "
            "exit_price, exit_date, exit_reason) VALUES (?, 'TCS', 1, 'market', 90, 'closed one', '2026-03-01', 'closed', 100, "
            "'2026-03-02', ?, '2026-03-06', 'target reached')",
            (acc["id"], r_exit),
        )
        return cur.lastrowid


def test_tags_api_and_analytics_endpoint(fresh_db):
    c = TestClient(app)
    tid = _closed_trade(120)
    assert c.post(f"/api/practice/trades/{tid}/tags", json={"setup": "breakout", "mistakes": ["exited-early"]}).status_code == 200
    bad = c.post(f"/api/practice/trades/{tid}/tags", json={"setup": "moonshot"})
    assert bad.status_code == 400 and "Choose a setup" in bad.json()["detail"]
    assert c.post(f"/api/practice/trades/{tid}/tags", json={"mistakes": ["guessing"]}).status_code == 400
    a = c.get("/api/practice/analytics").json()
    assert a["closed"] == 1 and a["by_setup"][0]["setup"] == "breakout" and a["by_setup"][0]["avg_r"] == 2.0
    assert next(g for g in a["by_mistake"] if g["mistake"] == "exited-early")["count"] == 1


def test_setup_is_saved_with_the_order_and_mistakes_wait_for_the_close(fresh_db):
    c = TestClient(app)
    r = c.post(
        "/api/practice/trades",
        json={"symbol": "TCS", "qty": 1, "stop": 1, "thesis": "Pullback in an uptrend.", "setup": "pullback"},
    )
    tid = r.json()["id"]
    assert next(t for t in service._trades(service.account()["id"]) if t["id"] == tid)["setup"] == "pullback"
    early = c.post(f"/api/practice/trades/{tid}/tags", json={"setup": "pullback", "mistakes": ["chased"]})
    assert early.status_code == 400 and "once the trade is closed" in early.json()["detail"]


def test_drawdown_finds_the_largest_fall_from_a_peak():
    pts = [{"day": d, "equity": v} for d, v in [("a", 100), ("b", 120), ("c", 90), ("d", 130), ("e", 117)]]
    assert analytics.drawdown(pts) == {"points": 30.0, "pct": 25.0, "peak_day": "b", "trough_day": "c"}
    assert analytics.drawdown([{"day": "a", "equity": 100}, {"day": "b", "equity": 110}])["points"] == 0.0


def test_equity_snapshots_one_per_trading_day_and_reset_clears_them(fresh_db, monkeypatch):
    from belfort.data import market

    c = TestClient(app)
    for day in ("2026-11-18", "2026-11-19", "2026-11-19", "2026-11-20"):
        monkeypatch.setattr(market, "data_day", lambda now=None, d=day: d)
        c.get("/api/practice/portfolio")
    curve = c.get("/api/practice/equity").json()
    assert [p["day"] for p in curve["points"]] == ["2026-11-18", "2026-11-19", "2026-11-20"]
    assert curve["start_points"] == curve["points"][0]["equity"] and curve["drawdown"]["points"] == 0.0
    assert "no money value" in curve["note"]
    c.post("/api/practice/reset")
    assert [p["day"] for p in c.get("/api/practice/equity").json()["points"]] == ["2026-11-20"]
