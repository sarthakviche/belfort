"""Practice, Learn, News and Assistant: rules tested on synthetic data, with the network replaced."""

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from belfort import settings
from belfort.assistant import chat
from belfort.core import compliance, db
from belfort.data import market
from belfort.learn import curriculum
from belfort.main import app
from belfort.news import feeds
from belfort.practice import engine, service
from tests.helpers import price_frame


def bars(rows):
    """rows: list of (date, open, high, low, close)."""
    df = pd.DataFrame(rows, columns=["date", "open", "high", "low", "close"]).set_index("date")
    df.index = pd.to_datetime(df.index)
    df["volume"] = 1000
    return df


# ---------------- settlement rules ----------------


def trade(**kw):
    t = {
        "status": "pending",
        "entry_type": "market",
        "limit_price": None,
        "stop": 95.0,
        "target": 110.0,
        "placed_on": "2026-01-01",
        "entry_price": None,
        "entry_date": None,
        "exit_price": None,
        "exit_date": None,
        "exit_reason": None,
        "close_requested_on": None,
    }
    t.update(kw)
    return t


def test_market_order_fills_next_open_and_hits_target():
    df = bars([("2026-01-01", 99, 101, 98, 100), ("2026-01-02", 100.5, 104, 99, 103), ("2026-01-05", 103, 111, 102, 109)])
    f = engine.settle_trade(trade(), df)
    assert (f.entry_price, f.entry_date) == (100.5, "2026-01-02")
    assert f.status == "closed" and f.exit_price == 110.0 and f.exit_reason == "target reached"


def test_gap_below_stop_exits_at_open_not_stop():
    df = bars([("2026-01-02", 100, 101, 99, 100), ("2026-01-05", 90, 92, 89, 91)])
    f = engine.settle_trade(trade(), df)
    assert f.exit_price == 90 and f.exit_reason == "gapped below the stop"


def test_stop_assumed_first_when_one_bar_touches_both():
    df = bars([("2026-01-02", 100, 101, 99, 100), ("2026-01-05", 100, 112, 94, 105)])
    f = engine.settle_trade(trade(), df)
    assert f.exit_price == 95.0 and f.exit_reason == "stop-loss hit"


def test_limit_order_fills_at_limit_or_expires():
    df = bars([("2026-01-02", 101, 102, 100, 101), ("2026-01-05", 100.5, 101, 97.5, 99)])
    f = engine.settle_trade(trade(entry_type="limit", limit_price=98.0), df)
    assert f.status == "open" and f.entry_price == 98.0
    never = bars([(f"2026-01-{d:02d}", 101, 102, 100, 101) for d in range(2, 12)])
    assert engine.settle_trade(trade(entry_type="limit", limit_price=98.0), never).status == "expired"


def test_close_request_exits_next_open():
    df = bars([("2026-01-02", 100, 101, 99, 100), ("2026-01-05", 101, 102, 100, 101), ("2026-01-06", 102, 103, 101, 102)])
    f = engine.settle_trade(trade(close_requested_on="2026-01-05"), df)
    assert f.exit_price == 102 and f.exit_reason == "closed by you"


# ---------------- T07: raised stops, trailing stops, partial exits ----------------


def _opened(**kw):
    """A trade that filled at 100 on 2026-01-02 with the stop at 95."""
    return trade(status="open", entry_price=100.0, entry_date="2026-01-02", target=None, **kw)


def test_raised_stop_applies_from_the_next_session():
    df = bars([("2026-01-02", 100, 101, 99, 100), ("2026-01-05", 100, 103, 97.5, 102), ("2026-01-06", 102, 103, 97, 99)])
    f = engine.settle_trade(_opened(stop_moves='[{"on": "2026-01-05", "stop": 98}]'), df)
    assert f.exit_date == "2026-01-06" and f.exit_price == 98.0  # on the 5th the low of 97.5 was still above the old 95
    assert f.exit_reason == "raised stop hit at ₹98.00"


def test_raised_stop_gap_exits_at_the_open():
    df = bars([("2026-01-02", 100, 101, 99, 100), ("2026-01-05", 101, 102, 100, 101), ("2026-01-06", 97, 98, 96, 97)])
    f = engine.settle_trade(_opened(stop_moves='[{"on": "2026-01-02", "stop": 99}]'), df)
    assert f.exit_price == 97 and f.exit_reason == "gapped below the raised stop"


def test_a_lower_stop_move_never_lowers_the_stop():
    df = bars([("2026-01-02", 100, 101, 99, 100), ("2026-01-05", 100, 101, 95.5, 100)])
    f = engine.settle_trade(_opened(stop_moves='[{"on": "2026-01-02", "stop": 90}]'), df)
    assert f.status == "open" and f.stop == 95.0


def test_percent_trailing_stop_ratchets_on_closes_and_never_falls():
    rows = [
        ("2026-01-02", 100, 101, 99, 100),
        ("2026-01-05", 100, 106, 100, 105),  # close 105 -> trail 99.75
        ("2026-01-06", 105, 111, 104, 110),  # close 110 -> trail 104.50
        ("2026-01-07", 110, 110, 105, 106),  # close 106 -> candidate 100.70, the stop stays 104.50
    ]
    f = engine.settle_trade(_opened(trail_kind="pct", trail_value=5, trail_from="2026-01-02"), bars(rows))
    assert f.status == "open" and f.stop == 104.5
    rows.append(("2026-01-08", 105, 106, 104, 105))
    hit = engine.settle_trade(_opened(trail_kind="pct", trail_value=5, trail_from="2026-01-02"), bars(rows))
    assert hit.exit_date == "2026-01-08" and hit.exit_price == 104.5 and "raised stop" in hit.exit_reason


def test_atr_trailing_stop_uses_the_atr_at_each_close():
    df = bars([(f"2026-02-{d:02d}", 100 + d, 102 + d, 99 + d, 101 + d) for d in range(2, 12)])
    t = trade(
        status="open",
        entry_price=103.0,
        entry_date="2026-02-02",
        target=None,
        trail_kind="atr",
        trail_value=2,
        trail_from="2026-02-02",
    )
    f = engine.settle_trade(t, df)
    ranges = engine.atr(df)
    expected = round(float(df["close"].iloc[-1]) - 2 * float(ranges.iloc[-1]), 2)
    assert f.status == "open" and f.stop == expected


def test_trail_waits_for_the_session_after_it_was_set():
    df = bars([("2026-01-02", 100, 101, 99, 100), ("2026-01-05", 100, 121, 100, 120)])
    f = engine.settle_trade(_opened(trail_kind="pct", trail_value=5, trail_from="2026-01-05"), df)
    assert f.stop == 95.0  # the close on the day it was set does not count


def _filled_trade(qty=10):
    acc = service.account()
    with db.connect() as con:
        cur = con.execute(
            "INSERT INTO trades (account_id, symbol, qty, entry_type, stop, thesis, placed_on, status, entry_price, entry_date) "
            "VALUES (?, 'TCS', ?, 'market', 50, 'managed position', '2026-01-02', 'open', 100, '2026-01-05')",
            (acc["id"], qty),
        )
        return cur.lastrowid


def test_manage_api_raises_trails_and_sells_part(fresh_db):
    c = TestClient(app)
    tid = _filled_trade()
    last = float(price_frame(n=400, drift=0.001)["close"].iloc[-1])
    lower = c.post(f"/api/practice/trades/{tid}/stop", json={"stop": 40})
    assert lower.status_code == 400 and "only moves up" in lower.json()["detail"]
    above = c.post(f"/api/practice/trades/{tid}/stop", json={"stop": last + 1})
    assert above.status_code == 400 and "below the last close" in above.json()["detail"]
    assert c.post(f"/api/practice/trades/{tid}/stop", json={"stop": 60}).status_code == 200
    assert service.current_stop(dict(next(t for t in service._trades(service.account()["id"]) if t["id"] == tid))) == 60
    bad_trail = c.post(f"/api/practice/trades/{tid}/trail", json={"kind": "pct", "value": 40})
    assert bad_trail.status_code == 400 and "between" in bad_trail.json()["detail"]
    assert "Trailing stop on" in c.post(f"/api/practice/trades/{tid}/trail", json={"kind": "atr", "value": 2}).json()["message"]
    assert c.post(f"/api/practice/trades/{tid}/sell", json={"qty": 10}).status_code == 400  # all of it is an Exit
    assert "The other 6 stay open" in c.post(f"/api/practice/trades/{tid}/sell", json={"qty": 4}).json()["message"]
    rows = service._trades(service.account()["id"])
    child = next(t for t in rows if t["parent_id"] == tid)
    parent = next(t for t in rows if t["id"] == tid)
    assert (parent["qty"], child["qty"]) == (6, 4) and child["close_requested_on"] and child["entry_price"] == 100
    assert child["trail_kind"] == "atr" and child["stop"] == 50  # the part sold keeps the plan and the original risk
    assert c.post(f"/api/practice/trades/{tid}/trail", json={"kind": "off"}).status_code == 200


def test_manage_api_refuses_pending_and_closing_trades(fresh_db):
    c = TestClient(app)
    tid = _filled_trade()
    c.post(f"/api/practice/trades/{tid}/close")
    again = c.post(f"/api/practice/trades/{tid}/stop", json={"stop": 60})
    assert again.status_code == 400 and "already requested" in again.json()["detail"]
    assert c.post("/api/practice/trades/99999/sell", json={"qty": 1}).status_code == 400


def test_brier_rewards_honest_confidence():
    assert engine.brier(0.5, True) == engine.brier(0.5, False) == 0.25
    assert engine.forecast_points(engine.brier(0.5, True)) == 0
    assert engine.forecast_points(engine.brier(0.9, True)) == 96
    assert engine.forecast_points(engine.brier(0.9, False)) < -200  # confident and wrong costs far more


def test_prediction_resolves_after_horizon():
    df = bars([("2026-01-01", 100, 100, 100, 100)] + [(f"2026-01-{d:02d}", 101, 102, 100, 101 + d) for d in range(2, 9)])
    p = {"ref_date": "2026-01-01", "ref_close": 100.0, "horizon_days": 5, "direction": "up", "confidence": 0.7}
    r = engine.resolve_prediction(p, df)
    assert r["correct"] == 1 and r["outcome_date"] == "2026-01-06"
    assert engine.resolve_prediction({**p, "horizon_days": 20}, df) is None


# ---------------- practice service and API ----------------


def test_paper_account_flow(fresh_db):
    c = TestClient(app)
    pf = c.get("/api/practice/portfolio").json()
    assert pf["equity"] == settings.PAPER_START_POINTS and "no money value" in pf["note"]
    last = float(price_frame(n=400, drift=0.001)["close"].iloc[-1])
    bad = c.post("/api/practice/trades", json={"symbol": "TCS", "qty": 10, "stop": last * 0.95, "thesis": "short"})
    assert bad.status_code == 400 and "why" in bad.json()["detail"]
    ok = c.post(
        "/api/practice/trades",
        json={
            "symbol": "TCS",
            "qty": 10,
            "stop": last * 0.95,
            "target": last * 1.1,
            "thesis": "Pullback to the 20-day average in an uptrend.",
        },
    )
    assert ok.status_code == 200
    pf = c.get("/api/practice/portfolio").json()
    assert len(pf["pending"]) == 1 and pf["reserved"] > 0  # fills after the last bar we have
    too_big = c.post(
        "/api/practice/trades",
        json={"symbol": "TCS", "qty": 10_000_000, "stop": last * 0.95, "thesis": "Testing the points limit here."},
    )
    assert too_big.status_code == 400 and "Not enough points" in too_big.json()["detail"]
    tid = pf["pending"][0]["id"]
    assert "cancelled" in c.post(f"/api/practice/trades/{tid}/close").json()["message"]


def test_ticket_quote_shows_price_chart_support_and_stop(fresh_db):
    q = TestClient(app).get("/api/practice/quote", params={"symbol": "tcs"}).json()
    last = float(price_frame(n=400, drift=0.001)["close"].iloc[-1])
    assert q["symbol"] == "TCS" and q["last_close"] == round(last, 2) and q["as_of"]
    assert len(q["candles"]) == settings.TICKET_CHART_BARS and {"time", "open", "high", "low", "close"} <= set(q["candles"][0])
    assert q["suggested_stop"] < q["last_close"] and q["stop_basis"]
    assert q["support"] is None or q["support"]["price"] < q["last_close"]
    assert compliance.find_banned(q["note"] + q["stop_basis"]) == []


def test_size_never_risks_more_than_the_limit(fresh_db):
    c = TestClient(app)
    for risk_pct in (0.5, 1.0, 2.0):
        s = c.get("/api/practice/size", params={"symbol": "TCS", "entry": 100, "stop": 95, "risk_pct": risk_pct}).json()
        budget = settings.PAPER_START_POINTS * risk_pct / 100
        assert s["risk_amount"] <= budget and s["quantity"] == int(budget // 5)
        assert s["risk_share_pct"] <= risk_pct and s["over_limit"] is False
    assert c.get("/api/practice/size", params={"symbol": "TCS", "entry": 100, "stop": 95, "risk_pct": 3}).json()["over_limit"]


def test_size_is_capped_by_available_points(fresh_db):
    s = TestClient(app).get("/api/practice/size", params={"symbol": "TCS", "entry": 1000, "stop": 999, "risk_pct": 2}).json()
    assert s["capped_by_points"] is True
    assert s["position_value"] * (1 + settings.PAPER_COST_PCT) <= settings.PAPER_START_POINTS
    assert s["risk_amount"] <= settings.PAPER_START_POINTS * 0.02


def test_size_rejects_a_stop_above_entry_and_tiny_budgets(fresh_db):
    c = TestClient(app)
    bad = c.get("/api/practice/size", params={"symbol": "TCS", "entry": 100, "stop": 105})
    assert bad.status_code == 400 and "below the entry" in bad.json()["detail"]
    zero = c.get("/api/practice/size", params={"symbol": "TCS", "entry": 100000, "stop": 1, "risk_pct": 0.01}).json()
    assert zero["quantity"] == 0 and zero["message"]
    uses_last_close = c.get("/api/practice/size", params={"symbol": "TCS", "stop": 1}).json()
    assert uses_last_close["entry"] == round(float(price_frame(n=400, drift=0.001)["close"].iloc[-1]), 2)


def test_predictions_api(fresh_db):
    c = TestClient(app)
    r = c.post(
        "/api/practice/predictions",
        json={
            "symbol": "INFY",
            "direction": "up",
            "horizon": "4 weeks",
            "confidence": 0.65,
            "reason": "Higher lows since the results.",
        },
    )
    assert r.status_code == 200
    assert (
        c.post(
            "/api/practice/predictions", json={"symbol": "INFY", "direction": "up", "horizon": "4 weeks", "confidence": 0.3}
        ).status_code
        == 422
    )
    d = c.get("/api/practice/predictions").json()
    assert len(d["open"]) == 1 and d["badges"][0]["name"] == "First call"


def test_replay_uses_only_lagged_data_and_scores(fresh_db):
    r = service.replay_new(seed=3)
    cutoff = (pd.Timestamp.today() - pd.Timedelta(days=settings.EDU_LAG_DAYS)).strftime("%Y-%m-%d")
    assert r["candles"][-1]["time"] <= cutoff
    entry = r["candles"][-1]["close"]
    s = service.replay_score(r["id"], "long", entry * 0.95, entry * 1.1)
    assert s["outcome"] in {"stop", "target", "open"} and s["end_date"] <= cutoff
    skipped = service.replay_new(seed=4)
    assert service.replay_score(skipped["id"], "skip", None, None)["outcome"] == "skipped"


def test_replay_never_sends_hidden_bars_before_the_decision(fresh_db):
    c = TestClient(app)
    new = c.get("/api/practice/replay/new").json()
    assert len(new["candles"]) == new["visible"] == settings.REPLAY_VISIBLE_BARS
    assert "symbol" not in new and "end_date" not in new
    entry = new["candles"][-1]["close"]
    scored = c.post(
        "/api/practice/replay/score", json={"id": new["id"], "decision": "long", "stop": entry * 0.9, "target": entry * 1.2}
    )
    body = scored.json()
    assert scored.status_code == 200 and body["symbol"] and body["stats"]["count"] == 1
    assert len(body["hidden"]) == settings.REPLAY_WINDOW_BARS - settings.REPLAY_VISIBLE_BARS
    assert body["hidden"][0]["time"] > new["candles"][-1]["time"] and body["end_date"] == body["hidden"][-1]["time"]
    assert isinstance(body["start_date"], str) and body["start_date"] == new["candles"][0]["time"]


def test_replay_session_scores_once_and_rejects_unknown_ids(fresh_db):
    c = TestClient(app)
    new = c.get("/api/practice/replay/new").json()
    assert c.post("/api/practice/replay/score", json={"id": new["id"], "decision": "skip"}).status_code == 200
    again = c.post("/api/practice/replay/score", json={"id": new["id"], "decision": "skip"})
    assert again.status_code == 400 and "already played" in again.json()["detail"]
    unknown = c.post("/api/practice/replay/score", json={"id": "not-a-real-session", "decision": "skip"})
    assert unknown.status_code == 400 and "Start a new chart" in unknown.json()["detail"]


# ---------------- learn ----------------


def test_every_written_lesson_parses_and_has_a_valid_quiz():
    idx = curriculum._lesson_index()
    written = [k for k in idx if (curriculum.LEARN / "lessons" / f"{k}.md").exists()]
    assert len(written) >= 8
    for k in written:
        les = curriculum.lesson(k)
        assert les["html"] and les["objectives"] and len(les["quiz"]) >= 3, k
        assert "answer" not in les["quiz"][0]  # answers never reach the page before grading
        assert not compliance.find_banned(les["text"]), k


def test_markdown_is_escaped():
    out = curriculum.render_markdown("Hello <script>alert(1)</script> **bold**\n\n::chart TCS 90")
    assert "<script>" not in out and "<b>bold</b>" in out and 'data-symbol="TCS"' in out


def test_quiz_grading_and_progress(fresh_db):
    c = TestClient(app)
    les = c.get("/api/learn/lessons/position-sizing").json()
    wrong = c.post("/api/learn/lessons/position-sizing/quiz", json={"answers": [0] * len(les["quiz"])}).json()
    assert not wrong["passed"]
    right = c.post("/api/learn/lessons/position-sizing/quiz", json={"answers": [r["answer"] for r in wrong["results"]]}).json()
    assert right["passed"] and right["score"] == 1
    prog = c.get("/api/learn/syllabus").json()
    assert prog["completed"] == 1 and prog["streak_days"] == 1
    assert c.get("/api/learn/lessons/../../etc").status_code == 404
    planned = next(
        (
            les["id"]
            for track in prog["syllabus"]["tracks"]
            for module in track["modules"]
            for les in module["lessons"]
            if les.get("status") == "planned" and module["stage"] == "beginner"
        ),
        "not-a-real-lesson",  # every lesson is written now, so fall back to an id that is not on the syllabus
    )
    assert c.get(f"/api/learn/lessons/{planned}").status_code == 404


def test_example_chart_is_lagged(fresh_db):
    d = TestClient(app).get("/api/learn/example", params={"symbol": "TCS", "bars": 60}).json()
    assert len(d["candles"]) == 60
    assert pd.Timestamp(d["ends"]) <= pd.Timestamp.today() - pd.Timedelta(days=settings.EDU_LAG_DAYS)


# ---------------- news ----------------

RSS = """<?xml version="1.0"?><rss xmlns:media="http://search.yahoo.com/mrss/"><channel>
<item><title>Sensex rises 400 points as FIIs return; Reliance Industries leads</title>
<link>https://example.com/a</link><pubDate>Fri, 20 Nov 2026 10:00:00 +0530</pubDate>
<description><![CDATA[<img src="https://example.com/i.jpg"> Banks and <b>energy</b> stocks gained.]]></description></item>
<item><title>RBI keeps repo rate unchanged</title><link>https://example.com/b</link>
<media:content url="https://example.com/r.jpg"/><description>The monetary policy committee voted 5-1.</description></item>
<item><title></title><link>https://example.com/c</link></item>
</channel></rss>"""


def test_rss_parse_clean_and_categorise():
    items = feeds.parse(RSS, {"id": "x", "name": "Example"})
    assert len(items) == 2
    a, b = items
    assert a["summary"] == "Banks and energy stocks gained." and a["image"] == "https://example.com/i.jpg"
    assert a["category"] == "Markets" and b["category"] == "Regulation" and b["image"] == "https://example.com/r.jpg"
    assert a["published"].startswith("2026-11-20")


@pytest.mark.parametrize(
    "title,tip",
    [
        ("Which metal stocks to buy for good returns? Target, SL", True),
        ("Buy Infosys, target ₹2,100: brokerage", True),
        ("Top picks for the week from analysts", True),
        ("RBI keeps repo rate unchanged", False),
        ("RBI to conduct a repo auction. Sl. No. 1, notified amount", False),
        ("SEBI recommends a framework for research analysts", False),
        ("Sensex closes 400 points higher as banks rally", False),
        ("Broker’s call: Ventive Hospitality (Buy)", True),
        ("Broker's Call: UTI Asset Management Co (Buy)", True),
        ("Tata Motors (Hold) after the demerger", True),
        ("Brokers call off strike at the port", False),
        ("Buy now, pay later lender raises funds", False),
    ],
)
def test_tip_style_headlines_are_flagged(title, tip):
    assert feeds.tip_style(title, "") is tip


def test_news_tags_companies(monkeypatch):
    monkeypatch.setattr(
        feeds, "cached", lambda key, ttl, fn, derived=False: {"RELIANCE": "RELIANCE", "Reliance": "RELIANCE", "TCS": "TCS"}
    )
    items = feeds.parse(RSS, {"id": "x", "name": "Example"})
    feeds.tag(items)
    assert items[0]["symbols"] == ["RELIANCE"] and items[1]["symbols"] == []


@pytest.mark.parametrize(
    "title,tagged",
    [
        ("BSE shares jump 48% in 2026 on record volumes", True),
        ("HSBC prefers BSE over NSE in its coverage", True),
        ("Six BSE 100 stocks hit 52-week highs", False),
        ("Press release filed with BSE and NSE under SEBI rules", False),
        ("Shares list at a 3% premium on the BSE", False),
        ("Market cap ranking among BSE-listed companies", False),
        ("Sensex: the BSE Sensex closed 300 points higher", False),
    ],
)
def test_news_does_not_tag_bse_when_it_means_the_exchange(monkeypatch, title, tagged):
    monkeypatch.setattr(feeds, "cached", lambda key, ttl, fn, derived=False: {"BSE": "BSE"})
    story = {"title": title, "summary": ""}
    feeds.tag([story])
    assert (story["symbols"] == ["BSE"]) is tagged


def test_news_companies_name_each_tagged_stock_without_fetching(monkeypatch, tmp_path):
    from belfort.data import symbols
    from belfort.research.analysis import pipeline

    monkeypatch.setattr(symbols.settings, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(symbols, "_closes", None)
    monkeypatch.setattr(pipeline.nse, "listed", lambda: [("TCS", "Tata Consultancy Services Limited")])
    symbols.remember_close("TCS", 2640.3, "2026-11-26")
    out = feeds.companies(["TCS", "NOTLISTED", "TCS"])
    assert list(out) == ["TCS", "NOTLISTED"]
    assert (
        out["TCS"]["last_close"] == 2640.3
        and out["TCS"]["as_of"] == "2026-11-26"
        and out["TCS"]["name"] == "Tata Consultancy Services"
    )
    assert out["NOTLISTED"] == {"name": "NOTLISTED"}


def test_news_route_adds_the_companies_map(monkeypatch):
    from belfort.news import router as news_router

    data = {"stories": [{"title": "x", "symbols": ["INFY"]}], "generated": "", "sources": [], "categories": [], "note": ""}
    monkeypatch.setattr(news_router.feeds, "get", lambda refresh=False: data)
    monkeypatch.setattr(news_router.feeds, "companies", lambda syms: {s: {"name": s} for s in syms})
    assert TestClient(app).get("/api/news").json()["companies"] == {"INFY": {"name": "INFY"}}


# ---------------- assistant ----------------


def test_openai_compatible_provider_and_local_needs_no_key(monkeypatch):
    for k in ("GEMINI_API_KEY", "OPENAI_API_KEY", "AI_PROVIDER", "OPENAI_BASE_URL"):
        monkeypatch.delenv(k, raising=False)
    p = chat.Provider.resolve("openai", "", "llama3", "http://localhost:11434/v1")
    seen = {}

    class R:
        status_code = 200

        def json(self):
            return {"choices": [{"message": {"content": "Support is a price where buyers stepped in before."}}]}

    def post(url, headers=None, json=None, timeout=None):
        seen.update(url=url, headers=headers, body=json)
        return R()

    monkeypatch.setattr(chat.httpx, "post", post)
    assert "buyers" in chat.ask("What is support?", provider=p, context="headline", mode="news")
    assert seen["url"] == "http://localhost:11434/v1/chat/completions" and seen["headers"] == {}
    assert seen["body"]["messages"][0]["role"] == "system"
    with pytest.raises(chat.ChatError):
        chat.Provider.resolve("openai", "", None, None)  # hosted service without a key


def test_chat_key_comes_from_headers(monkeypatch):
    for k in ("GEMINI_API_KEY", "OPENAI_API_KEY", "AI_PROVIDER"):
        monkeypatch.delenv(k, raising=False)
    got = {}
    monkeypatch.setattr(chat, "_call", lambda p, turns: got.setdefault("p", p) and "An explanation.")
    r = TestClient(app).post(
        "/api/chat", json={"question": "Explain", "mode": "news"}, headers={"X-AI-Provider": "gemini", "X-AI-Key": "user-key"}
    )
    assert r.status_code == 200 and got["p"].key == "user-key" and got["p"].kind == "gemini"


class _ErrorReply:
    def __init__(self, status_code, message):
        self.status_code, self._message = status_code, message

    def json(self):
        return {"error": {"message": self._message}}


@pytest.mark.parametrize(
    ("kind", "status", "message", "expected"),
    [
        ("gemini", 400, "API key not valid. Please pass a valid API key.", "did not accept your key"),
        ("openai", 401, "Incorrect API key provided: sk-secret-123.", "did not accept your key"),
        ("openai", 403, "Forbidden", "did not accept your key"),
        ("gemini", 404, "models/x is not found", 'model "test-model" was not found'),
        ("gemini", 429, "Resource has been exhausted", "rate or quota limit"),
        ("openai", 503, "overloaded", "having trouble right now"),
    ],
)
def test_chat_provider_errors_tell_the_user_what_to_do(monkeypatch, kind, status, message, expected):
    p = chat.Provider(kind, "sk-secret-123", "test-model", "https://api.example.com/v1")
    monkeypatch.setattr(chat.httpx, "post", lambda *a, **k: _ErrorReply(status, message))
    with pytest.raises(chat.ChatError) as caught:
        chat.ask("What is support?", provider=p)
    assert expected in str(caught.value)
    assert "sk-secret-123" not in str(caught.value)


def test_chat_other_errors_never_echo_the_key(monkeypatch):
    p = chat.Provider("openai", "sk-secret-123", "m", "https://api.example.com/v1")
    monkeypatch.setattr(chat.httpx, "post", lambda *a, **k: _ErrorReply(418, "Key sk-secret-123 is a teapot"))
    with pytest.raises(chat.ChatError) as caught:
        chat.ask("Hi", provider=p)
    assert "(418)" in str(caught.value) and "sk-secret-123" not in str(caught.value) and "[your key]" in str(caught.value)


def test_chat_network_failures_name_the_fix(monkeypatch):
    def offline(*a, **k):
        raise chat.httpx.ConnectError("no route")

    def slow(*a, **k):
        raise chat.httpx.ReadTimeout("slow")

    local = chat.Provider("openai", "", "llama3", "http://localhost:11434/v1")
    hosted = chat.Provider("gemini", "k", "m", "")
    monkeypatch.setattr(chat.httpx, "post", offline)
    with pytest.raises(chat.ChatError, match="Start Ollama"):
        chat.ask("Hi", provider=local)
    with pytest.raises(chat.ChatError, match="internet connection"):
        chat.ask("Hi", provider=hosted)
    monkeypatch.setattr(chat.httpx, "post", slow)
    with pytest.raises(chat.ChatError, match="took too long"):
        chat.ask("Hi", provider=hosted)


def test_db_migrations_are_idempotent(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "DB_FILE", tmp_path / "m.db")
    with db.connect() as con:
        con.execute("SELECT * FROM trades")
    db._ready.clear()
    with db.connect() as con:
        assert con.execute("SELECT COUNT(*) FROM schema_version").fetchone()[0] == len(db.MIGRATIONS)


# ---------------- T05: bar cache and once-per-day settlement ----------------


def _ist(*args):
    return market.datetime(*args, tzinfo=market.IST)


def test_bar_cache_lasts_until_the_next_end_of_day_release():
    monday_morning, monday_evening, friday_evening = _ist(2026, 11, 16, 10), _ist(2026, 11, 16, 19), _ist(2026, 11, 20, 19)
    assert market.last_release(monday_morning) == _ist(2026, 11, 13, 18)  # Friday's data is still the newest
    assert market.next_release(monday_morning) == _ist(2026, 11, 16, 18)
    assert market.next_release(monday_evening) == _ist(2026, 11, 17, 18)
    assert market.next_release(friday_evening) == _ist(2026, 11, 23, 18)  # nothing new over the weekend
    assert market.data_day(_ist(2026, 11, 22, 12)) == "2026-11-20"


class _CountingPrices:
    def __init__(self, delay=0.0):
        self.calls, self.delay = 0, delay

    def history(self, symbol, years=5):
        import time as clock

        self.calls += 1
        clock.sleep(self.delay)
        return price_frame(n=300, drift=0.001)


class _NoNse:
    def recent_bars(self, symbol, after):
        return pd.DataFrame()


def test_bars_are_fetched_once_until_the_cache_expires(monkeypatch):
    from belfort.research.analysis import pipeline

    prices = _CountingPrices()
    monkeypatch.setattr(pipeline, "prices", prices)
    monkeypatch.setattr(pipeline, "nse", _NoNse())
    first = market.bars("TCS", 1)
    first.iloc[-1, 0] = -1  # callers get a copy and cannot spoil the cache
    assert market.bars("TCS", 1)["open"].iloc[-1] != -1 and prices.calls == 1
    monkeypatch.setattr(market, "next_release", lambda now=None: _ist(2000, 1, 3, 18))  # everything cached is stale
    market.clear_cache()
    market.bars("TCS", 1)
    market.bars("TCS", 1)
    assert prices.calls == 3  # stale entries are refetched every time


def _open_positions(symbols):
    acc = service.account()
    with db.connect() as con:
        for sym in symbols:
            con.execute(
                "INSERT INTO trades (account_id, symbol, qty, entry_type, stop, thesis, placed_on, status, entry_price, entry_date) "
                "VALUES (?, ?, 1, 'market', 1, 'test position', '2026-01-02', 'open', 100, '2026-01-05')",
                (acc["id"], sym),
            )


def test_settlement_runs_once_per_trading_day(fresh_db, monkeypatch):
    _open_positions(["TCS", "INFY"])
    runs = []
    real = engine.settle_trade
    monkeypatch.setattr(engine, "settle_trade", lambda t, df: runs.append(t["symbol"]) or real(t, df))
    service.portfolio()
    service.portfolio()
    assert sorted(runs) == ["INFY", "TCS"]  # the second view did not settle again
    monkeypatch.setattr(market, "data_day", lambda now=None: "2099-01-01")  # a new session's data arrived
    service.portfolio()
    assert len(runs) == 4


def test_settlement_retries_when_a_symbol_failed_to_load(fresh_db, monkeypatch):
    _open_positions(["TCS"])
    monkeypatch.setattr(market, "bars", lambda symbol, years=5: (_ for _ in ()).throw(RuntimeError("offline")))
    service.portfolio()
    assert service.account()["settled_for"] is None


def test_portfolio_with_twenty_symbols_is_fast_on_the_second_visit(fresh_db, monkeypatch):
    import time as clock

    from belfort.research.analysis import pipeline

    monkeypatch.undo()  # use the real cached market.bars, not the fixture's fake
    monkeypatch.setattr(settings, "DB_FILE", fresh_db / "t.db")
    monkeypatch.setattr(pipeline, "prices", _CountingPrices(delay=0.05))
    monkeypatch.setattr(pipeline, "nse", _NoNse())
    _open_positions([f"SYM{i}" for i in range(20)])
    service.portfolio()
    started = clock.perf_counter()
    pf = service.portfolio()
    assert clock.perf_counter() - started < 1.0 and len(pf["open"]) == 20
    assert pipeline.prices.calls == 20


# ---------------- T09: total open risk and size warnings ----------------


def test_portfolio_reports_open_risk_from_the_current_stop(fresh_db):
    tid = _filled_trade(qty=10)  # entry 100, stop 50
    last = float(price_frame(n=400, drift=0.001)["close"].iloc[-1])
    risk = service.portfolio()["risk"]
    assert risk["open_points"] == round((last - 50) * 10, 2) and risk["pending_points"] == 0
    assert risk["total_pct"] == round(risk["total_points"] / service.portfolio()["equity"] * 100, 2)
    service.raise_stop(tid, 60)
    assert service.portfolio()["risk"]["open_points"] == round((last - 60) * 10, 2)  # a raised stop lowers the risk


def test_order_warnings_for_one_big_trade_and_for_total_open_risk(fresh_db):
    c = TestClient(app)
    last = float(price_frame(n=400, drift=0.001)["close"].iloc[-1])
    small = c.post(
        "/api/practice/trades", json={"symbol": "TCS", "qty": 10, "stop": last * 0.95, "thesis": "Small and planned trade."}
    )
    assert small.json()["warnings"] == []
    qty = int(settings.PAPER_START_POINTS * 0.035 / (last * 0.1))  # about 3.5% of the account at risk
    big = c.post(
        "/api/practice/trades", json={"symbol": "INFY", "qty": qty, "stop": last * 0.9, "thesis": "Deliberately too big."}
    )
    assert any("per trade" in w for w in big.json()["warnings"])
    more = c.post(
        "/api/practice/trades", json={"symbol": "SBIN", "qty": qty, "stop": last * 0.9, "thesis": "Pushes open risk over."}
    )
    assert any("open risk would be" in w for w in more.json()["warnings"])
    risk = c.get("/api/practice/portfolio").json()["risk"]
    assert risk["pending_points"] > 0 and risk["over_limit"] is True
    assert compliance.find_banned(" ".join(more.json()["warnings"]) + risk["note"]) == []
