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


@pytest.fixture
def fresh_db(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "DB_FILE", tmp_path / "t.db")
    monkeypatch.setattr(market, "bars", lambda symbol, years=5: price_frame(n=400, drift=0.001))
    return tmp_path


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
    entry = r["candles"][r["visible"] - 1]["close"]
    s = service.replay_score(r["candles"], r["visible"], "long", entry * 0.95, entry * 1.1)
    assert s["outcome"] in {"stop", "target", "open"}
    assert service.replay_score(r["candles"], r["visible"], "skip", None, None)["outcome"] == "skipped"


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
    assert c.get("/api/learn/lessons/risk-of-ruin").status_code == 404  # on the syllabus, not written yet


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
    ],
)
def test_tip_style_headlines_are_flagged(title, tip):
    assert feeds.tip_style(title, "") is tip


def test_news_tags_companies(monkeypatch):
    monkeypatch.setattr(feeds, "cached", lambda key, ttl, fn: {"RELIANCE": "RELIANCE", "Reliance": "RELIANCE", "TCS": "TCS"})
    items = feeds.parse(RSS, {"id": "x", "name": "Example"})
    feeds.tag(items)
    assert items[0]["symbols"] == ["RELIANCE"] and items[1]["symbols"] == []


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
