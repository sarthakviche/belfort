"""Dictionary search ranking and the Ask / web fallback endpoints. The assistant provider is faked: no network."""

import pytest
from fastapi.testclient import TestClient

from belfort.assistant import chat, glossary_router
from belfort.core.glossary import GLOSSARY
from belfort.core.glossary_search import clean, close_only, search, web_search_url
from belfort.main import app

client = TestClient(app)


def terms(q, **kw):
    return [g["term"] for g in search(q, **kw)]


def test_exact_term_ranks_first_and_ignores_case_and_hyphens():
    assert terms("stop-loss")[0] == "Stop-loss"
    assert terms("STOP LOSS")[0] == "Stop-loss"


def test_exact_phrase_beats_prefix_matches():
    assert terms("stop distance")[0] == "Stop distance"


def test_prefix_finds_term():
    r = terms("swing")
    assert "Swing trade" in r and "Swing high" in r


def test_substring_of_a_word_in_the_term():
    assert "Risk per trade" in terms("per trade")


def test_typo_is_tolerated():
    assert terms("stoploss")[0] == "Stop-loss"
    assert "Position size" in terms("postion size")


def test_no_match_returns_nothing():
    assert search("qzxwvu") == []
    assert search("blockchain mining rigs") == []


def test_empty_query_returns_whole_glossary_in_order():
    assert search("") == GLOSSARY
    assert search("   ") == GLOSSARY


def test_limit_and_clean():
    assert len(search("a", limit=3)) <= 3
    assert clean("  Stop-Loss! ") == "stop loss"


def test_web_url_is_encoded():
    assert web_search_url("p/e & more") == "https://www.google.com/search?q=p%2Fe+%26+more+stock+market+meaning"


def test_search_endpoint():
    r = client.get("/api/glossary/search", params={"q": "stop loss"}).json()
    assert r["results"][0]["term"] == "Stop-loss" and r["count"] == len(r["results"])
    assert r["web_url"].endswith("stock+market+meaning")
    miss = client.get("/api/glossary/search", params={"q": "qzxwvu"}).json()
    assert miss["results"] == [] and "qzxwvu" in miss["web_url"]
    allr = client.get("/api/glossary/search", params={"q": "", "limit": 500}).json()
    assert allr["count"] == len(GLOSSARY) and allr["web_url"] is None


def test_close_only_when_the_best_match_is_a_close_spelling():
    # "swing trade index" is not in the dictionary; "Swing trade" is only a close spelling of it
    assert close_only("swing trade index") is True
    assert close_only("swing trade") is False  # exact term
    assert close_only("swing") is False  # prefix
    assert close_only("qzxwvu") is False  # no match at all: the page shows its own not-found screen
    assert close_only("") is False


def test_search_endpoint_marks_close_only_results():
    weak = client.get("/api/glossary/search", params={"q": "swing trade index"}).json()
    assert weak["results"] and weak["close_only"] is True and "swing+trade+index" in weak["web_url"]
    strong = client.get("/api/glossary/search", params={"q": "swing trade"}).json()
    assert strong["close_only"] is False
    miss = client.get("/api/glossary/search", params={"q": "qzxwvu"}).json()
    assert miss["close_only"] is False


@pytest.fixture
def no_key(monkeypatch):
    for k in ("GEMINI_API_KEY", "OPENAI_API_KEY", "AI_PROVIDER", "OPENAI_BASE_URL"):
        monkeypatch.delenv(k, raising=False)


def test_ask_without_a_key_explains_how_to_add_one(no_key):
    r = client.post("/api/glossary/ask", json={"term": "theta decay"})
    assert r.status_code == 503 and "Settings" in r.json()["detail"]


def test_ask_uses_the_assistant_in_general_mode(no_key, monkeypatch):
    seen = {}

    def fake_ask(question, history=None, context="", mode="report", provider=None):
        seen.update(question=question, context=context, mode=mode, key=provider.key)
        return "Theta decay is the loss of an option's time value as expiry nears."

    monkeypatch.setattr(chat, "ask", fake_ask)
    r = client.post("/api/glossary/ask", json={"term": " theta   decay "}, headers={"X-AI-Provider": "gemini", "X-AI-Key": "k"})
    body = r.json()
    assert r.status_code == 200 and body["term"] == "theta decay"
    assert body["answer"].startswith("Theta decay") and body["label"] == "AI explanation — may be wrong"
    assert seen["mode"] == "general" and seen["key"] == "k"
    assert '"theta decay"' in seen["question"] and "2 to 4" in seen["question"] and "Do not give advice" in seen["question"]


def test_ask_passes_through_the_compliance_filter(monkeypatch):
    # Real chat.ask with only the network call faked: a banned promise-style reply is replaced.
    monkeypatch.setattr(chat, "_call", lambda p, turns: "This stock is a sure shot and will double. Guaranteed returns.")
    r = client.post("/api/glossary/ask", json={"term": "multibagger"}, headers={"X-AI-Provider": "gemini", "X-AI-Key": "k"})
    assert r.status_code == 200 and "guaranteed" not in r.json()["answer"].lower()
    assert "can't answer" in r.json()["answer"]


def test_ask_validates_the_term():
    assert client.post("/api/glossary/ask", json={"term": ""}).status_code == 422
    assert client.post("/api/glossary/ask", json={"term": "x" * 200}).status_code == 422


def test_web_search_opens_the_system_browser(monkeypatch):
    opened = []
    monkeypatch.setattr(glossary_router.webbrowser, "open", lambda u: opened.append(u) or True)
    r = client.post("/api/glossary/web-search", json={"term": "theta decay"}).json()
    assert r["opened"] is True and opened == [r["url"]]
    assert r["url"] == "https://www.google.com/search?q=theta+decay+stock+market+meaning"
