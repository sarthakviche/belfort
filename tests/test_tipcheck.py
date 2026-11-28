"""Tip Check (T44): every rule is a pure function, checked here with fixtures. No network."""

import base64
from pathlib import Path

import httpx
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from belfort import settings
from belfort.assistant import chat, vision
from belfort.core import compliance
from belfort.data import market
from belfort.main import app
from belfort.research.analysis import pipeline
from belfort.tipcheck import register, rules, service, sources, strings

FIX = Path(__file__).parent / "fixtures"
COMPANIES = [
    ("TCS", "Tata Consultancy Services Limited"),
    ("INFY", "Infosys Limited"),
    ("RELIANCE", "Reliance Industries Limited"),
    ("SUZLON", "Suzlon Energy Limited"),
    ("IRFC", "Indian Railway Finance Corporation Limited"),
    ("PAKKA", "Pakka Limited"),
    ("PUMPCO", "Pump Company Limited"),
    ("SOCIALCO", "Social Company Limited"),
]
SCAM = (
    "🚀 SUZLON 100% SURE SHOT CALL 🚀 Buy above 52, Target 60/68 in 3 days. Jaldi entry lo, operator game chal raha "
    "hai. Join our VIP premium group, pay 4999 via UPI. SEBI registered. Kisi ko mat batana!"
)


def surveillance_fixture():
    return sources.parse_reg_ind((FIX / "reg1_ind_sample.csv").read_text(encoding="utf-8"))


def bars(n=400, spike_at=None, spike=8.0, run=0.0, run_bars=20, seed=3):
    """Calm synthetic bars; optionally a volume spike and a price run-up ending at index `spike_at` (default: last)."""
    rng = np.random.default_rng(seed)
    close = 100 * np.exp(np.cumsum(rng.normal(0, 0.005, n)))
    volume = rng.lognormal(12, 0.1, n)
    if spike_at is not None or run:
        end = n - 1 if spike_at is None else spike_at
        close[end - run_bars + 1 : end + 1] *= np.linspace(1, 1 + run, run_bars)
        close[end + 1 :] *= 1 + run
        volume[end] *= spike
    idx = pd.bdate_range(end="2026-11-27", periods=n)
    return pd.DataFrame({"open": close, "high": close * 1.01, "low": close * 0.99, "close": close, "volume": volume}, index=idx)


# ---------------- phrases ----------------


def test_english_hinglish_and_hindi_phrases_are_found():
    assert "100% sure shot" in rules.phrase_check("promises", SCAM).evidence
    assert rules.phrase_check("urgency", SCAM).evidence == ["jaldi entry lo"]  # the longest phrase wins
    assert set(rules.phrase_check("secrecy", SCAM).evidence) == {"operator game", "kisi ko mat batana"}
    assert rules.phrase_check("target_days", SCAM).status == "flag"
    assert rules.phrase_check("money_ask", SCAM).status == "flag"
    hindi = "NSE:IRFC पक्का मुनाफा, 2 दिन में टारगेट 180। जल्दी खरीदें। अंदर की खबर है।"
    for flag in ("promises", "target_days", "urgency", "secrecy"):
        assert rules.phrase_check(flag, hindi).status == "flag", flag
    assert rules.phrase_check("target_days", "Target 2 din mein 180").status == "flag"


def test_a_plain_note_raises_no_phrase_flags():
    note = "Infosys reports results on 15 January. Revenue grew 6% last year. This is not a recommendation."
    assert all(rules.phrase_check(f, note).status == "clear" for f in rules.PHRASE_CHECKS)


def test_phrases_match_whole_words_only():
    assert rules.find_phrases("money_ask", "The groupie was otpimistic") == []  # 'otp' inside a word is not a match
    assert rules.find_phrases("urgency", "Hurry!") == ["hurry"]


def test_every_phrase_compiles_and_every_flag_has_three_languages():
    for flag, patterns in rules.phrase_rules().items():
        assert patterns, flag
    import json

    data = json.loads(rules.PHRASES_FILE.read_text(encoding="utf-8"))
    for flag in rules.PHRASE_CHECKS:
        assert set(data[flag]) == {"en", "hinglish", "hi"}, flag


@pytest.mark.parametrize(
    "tip",
    [
        "Target 2x in 5 din",
        "Target 68, sirf 3 din",
        "XYZ target within 10 dino",
    ],
)
def test_a_short_deadline_is_found_without_mein(tip):
    assert rules.phrase_check("target_days", tip).status == "flag"


@pytest.mark.parametrize(
    "tip",
    [
        "VIP Telegram group join karne ke liye message",
        "Join the premium WhatsApp channel",
        "Paid stock tips group open",
        "Entry ke liye ₹999 bhejo",
        "Rs. 4,999/- send karo",
        "999 rupees transfer karo",
    ],
)
def test_a_money_or_private_group_ask_is_found_with_words_in_between(tip):
    assert rules.phrase_check("money_ask", tip).status == "flag"


@pytest.mark.parametrize(
    "note",
    [
        "Results are due in 5 days.",
        "Office 5 din band rahega.",
        "The company reported a profit of ₹999 crore.",
        "Dividend of Rs 5 per share, record date next week.",
        "The group channel strategy was discussed at the premium segment review.",
    ],
)
def test_ordinary_sentences_raise_no_deadline_or_money_flag(note):
    assert rules.phrase_check("target_days", note).status == "clear"
    assert rules.phrase_check("money_ask", note).status == "clear"


# ---------------- registration ----------------


def test_registration_rules():
    reg = {"INH000012345": {"name": "Example Research Analysts LLP"}}
    none = rules.registration("Buy XYZ now", reg, "2026-11-01")
    assert none.status == "flag" and "no SEBI registration number" in none.detail
    claimed = rules.registration("SEBI registered analyst. Buy XYZ", reg, "2026-11-01")
    assert claimed.status == "flag" and "gives no registration number" in claimed.detail
    found = rules.registration("Research by INH000012345", reg, "2026-11-01")
    assert found.status == "clear" and "Example Research Analysts LLP" in found.detail and "copy real" in found.detail
    missing = rules.registration("Reg: INH000099999", reg, "2026-11-01")
    assert missing.status == "flag" and "not in Belfort's copy" in missing.detail
    short = rules.registration("Reg no INH12345", reg, "2026-11-01")
    assert short.status == "flag" and "not a valid SEBI number" in short.detail
    broker = rules.registration("Our broker INZ000123456", reg, "2026-11-01")
    assert broker.status == "flag" and "stock broker" in broker.detail
    offline = rules.registration("INA000067890", None, None)
    assert offline.status == "unknown" and "no copy of SEBI's register" in offline.detail
    approved = rules.registration("SEBI approved tips. INH000012345", reg, "2026-11-01")
    assert approved.status == "flag" and "never approves" in approved.detail


def test_registration_numbers_are_normalised():
    assert rules.registration_numbers("inh 000012345 and INA-000067890, INH000012345") == ["INH000012345", "INA000067890"]


def test_register_import_reads_a_saved_list(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "DATA_DIR", tmp_path)
    entries = register.read_csv(FIX / "sebi_register_sample.csv")
    assert entries == {
        "INH000012345": {"name": "Example Research Analysts LLP", "kind": "analyst"},
        "INA000067890": {"name": "Sample Advisory Services", "kind": "adviser"},
    }
    register.main([str(FIX / "sebi_register_sample.csv"), "--as-of", "2026-11-20"])
    reg, as_of = sources.sebi_register()
    assert as_of == "2026-11-20" and "INA000067890" in reg


def test_no_register_snapshot_means_none(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "DATA_DIR", tmp_path)
    assert sources.sebi_register() == (None, None)


# ---------------- which stock ----------------


def test_symbols_are_found_by_symbol_name_and_explicit_mention():
    assert rules.extract_symbols(SCAM, COMPANIES) == ["SUZLON"]
    assert rules.extract_symbols("Infosys results on 15 Jan", COMPANIES) == ["INFY"]
    assert rules.extract_symbols("reliance industries looks strong", COMPANIES) == ["RELIANCE"]
    assert rules.extract_symbols("NSE:IRFC target 180", COMPANIES) == ["IRFC"]


def test_words_that_are_also_symbols_need_an_explicit_mention():
    assert rules.extract_symbols("100% PAKKA PROFIT in tcs", COMPANIES) == []  # lower-case 'tcs' is too short to trust
    assert rules.extract_symbols("#PAKKA looks busy", COMPANIES) == ["PAKKA"]


# ---------------- surveillance ----------------


def test_surveillance_file_is_parsed_with_the_eq_row_winning():
    rows = surveillance_fixture()
    assert set(rows) == {"TCS", "PUMPCO", "ASMCO", "SOCIALCO"}
    assert rows["PUMPCO"]["Series"] == "EQ"


def test_surveillance_rules():
    rows = surveillance_fixture()
    clear = rules.surveillance("TCS", rows, "2026-11-27")
    assert clear.status == "clear" and "2026-11-27" in clear.detail
    esm = rules.surveillance("PUMPCO", rows, "2026-11-27")
    assert esm.status == "flag" and "Enhanced Surveillance Measure (ESM) stage 1" in esm.detail
    asm = rules.surveillance("ASMCO", rows, "2026-11-27")
    assert asm.status == "flag" and "GSM) stage 0" in asm.detail and "(ASM) stage 4" in asm.detail
    social = rules.surveillance("SOCIALCO", rows, "2026-11-27")
    assert social.status == "flag" and "social media tips" in social.detail
    assert rules.surveillance("NOSUCH", rows, "2026-11-27").status == "unknown"
    assert rules.surveillance("TCS", None, None).status == "unknown"
    assert rules.surveillance(None, rows, "2026-11-27").status == "unknown"


def test_surveillance_rows_walk_back_to_the_last_published_file(monkeypatch):
    text = (FIX / "reg1_ind_sample.csv").read_text(encoding="utf-8")
    asked = []

    def fetch(day):
        asked.append(day.isoformat())
        return text if day.isoformat() == "2026-11-25" else None

    monkeypatch.setattr(sources, "_fetch_reg_ind", fetch)
    monkeypatch.setattr(sources.market, "data_day", lambda: "2026-11-27")
    monkeypatch.setattr(sources, "cached", lambda key, ttl, fn: fn())
    rows, as_of = sources.surveillance_rows()
    assert as_of == "2026-11-25" and "TCS" in rows and asked == ["2026-11-27", "2026-11-26", "2026-11-25"]


def test_surveillance_rows_stop_when_offline(monkeypatch):
    def fetch(day):
        raise httpx.ConnectError("offline")

    monkeypatch.setattr(sources, "_fetch_reg_ind", fetch)
    monkeypatch.setattr(sources, "cached", lambda key, ttl, fn: fn())
    assert sources.surveillance_rows() == (None, None)


# ---------------- price and volume ----------------


def test_pump_needs_two_of_three_signals():
    spiked = bars(run=0.45)  # volume 8x on the last day after a 45% rise in 20 sessions
    f = rules.pump("PUMPCO", spiked, 300e7)
    assert f.status == "flag" and f.facts["signals"] == 3 and f.facts["volume_ratio"] >= 5
    assert "₹300 crore" in f.detail
    calm = rules.pump("TCS", bars(), 9e12)
    assert calm.status == "clear" and calm.facts["signals"] == 0 and "9,00,000 crore" in calm.detail
    small_only = rules.pump("TINY", bars(), 100e7)
    assert small_only.status == "clear" and small_only.facts["signals"] == 1
    unknown_size = rules.pump("PUMPCO", spiked, None)
    assert unknown_size.status == "flag" and "company size unknown" in unknown_size.detail


def test_pump_without_data_is_unknown():
    assert rules.pump("TCS", None, None).status == "unknown"
    assert rules.pump("TCS", bars(n=30), None).status == "unknown"
    assert rules.pump(None, bars(), None).status == "unknown"


def test_past_signature_uses_only_bars_at_least_30_days_old():
    df = bars(n=400, spike_at=250, run=0.5)
    f = rules.past_signature("PUMPCO", df, today=pd.Timestamp("2026-11-27"))
    assert f.status == "info" and f.facts["day"] == df.index[250].date().isoformat()
    assert "after_20" in f.facts and "after_60" in f.facts and "not what will happen now" in f.detail
    recent_only = bars(n=400, spike_at=395, run=0.5)  # the only spike is days ago: too recent to show
    g = rules.past_signature("PUMPCO", recent_only, today=pd.Timestamp("2026-11-27"))
    assert "No session like that" in g.detail


def test_indian_grouping():
    assert [rules.indian(x) for x in (999, 50010, 930753, 1234567890)] == ["999", "50,010", "9,30,753", "1,23,45,67,890"]


# ---------------- summary and service ----------------


def test_level_counts_only_counted_checks():
    f = [rules.Finding("promises", "flag", ""), rules.Finding("history", "info", ""), rules.Finding("pump", "unknown", "")]
    assert rules.level(f) == ("some", 1)
    assert rules.level([rules.Finding(i, "flag", "") for i in rules.COUNTED])[0] == "many"
    assert rules.level([])[0] == "low"


@pytest.fixture
def offline(monkeypatch):
    monkeypatch.setattr(service, "companies", lambda: COMPANIES)
    monkeypatch.setattr(sources, "surveillance_rows", lambda: (surveillance_fixture(), "2026-11-27"))
    monkeypatch.setattr(
        sources, "sebi_register", lambda: ({"INH000012345": {"name": "Example Research Analysts LLP"}}, "2026-11-20")
    )
    monkeypatch.setattr(market, "bars", lambda symbol, years=5: bars(run=0.45) if symbol == "PUMPCO" else bars())
    monkeypatch.setattr(pipeline.prices, "info", lambda symbol: {"marketCap": 300e7 if symbol == "PUMPCO" else 9e12})


def _strings(result):
    """Belfort's own wording in a result: everything except the tip's quoted evidence."""
    out = [result["summary"], result["limits"], result["share_line"], result["level_text"], result["learn_intro"]]
    out += [s["text"] for s in result["next_steps"]] + [x["title"] for x in result["lessons"]]
    out += [f["detail"] + f["title"] for f in result["findings"]]
    return out


def test_a_scam_tip_shows_many_flags_and_belfort_never_uses_tip_wording(offline):
    r = service.check(SCAM.replace("SUZLON", "PUMPCO"))
    assert r["symbol"] == "PUMPCO" and r["level"] == "many" and r["flags"] >= 7
    ids = [f["id"] for f in r["findings"]]
    assert ids == [
        "registration",
        "promises",
        "target_days",
        "urgency",
        "secrecy",
        "money_ask",
        "surveillance",
        "pump",
        "history",
    ]
    assert all(f["title"] and f["lesson"] for f in r["findings"])
    for text in _strings(r):
        assert compliance.find_banned(text) == [], text
    assert "never says a stock is good, safe" in r["limits"]


def test_a_clean_note_shows_few_flags(offline):
    r = service.check("Research note by INH000012345 on TCS: results due 15 January. Not a recommendation.")
    assert r["symbol"] == "TCS" and r["flags"] == 0 and r["level"] == "low"
    assert "does not make the tip safe" in r["summary"]


def test_nse_tip_campaign_flag_leads_the_results(offline):
    r = service.check("SOCIALCO will fly, hurry")
    assert r["findings"][0]["id"] == "surveillance" and r["findings"][0]["facts"]["tip_flags"] == ["social"]
    assert r["lead"] == "NSE itself has flagged SOCIALCO as a stock named in social media tips."
    assert service.check("TCS hurry")["lead"] is None


def test_the_user_can_pick_the_stock(offline):
    r = service.check("This one will fly, hurry", symbol="pumpco")
    assert r["symbol"] == "PUMPCO" and r["name"] == "Pump Company Limited"


def test_slow_data_is_reported_as_not_checked(offline, monkeypatch):
    import time

    monkeypatch.setattr(settings, "TIP_TIME_BUDGET_SECONDS", 0.05)
    monkeypatch.setattr(market, "bars", lambda symbol, years=5: time.sleep(0.5) or bars())
    r = service.check("TCS hurry")
    pump = next(f for f in r["findings"] if f["id"] == "pump")
    assert pump["status"] == "unknown"


def test_empty_tip_is_refused(offline):
    with pytest.raises(service.TipError):
        service.check("   ")


def test_api_checks_a_tip(offline):
    c = TestClient(app)
    r = c.post("/api/tipcheck", json={"text": SCAM})
    assert r.status_code == 200 and r.json()["symbol"] == "SUZLON"
    assert c.post("/api/tipcheck", json={"text": ""}).status_code == 422


def test_strings_have_no_promise_wording():
    for key, text in strings.EN.items():
        assert compliance.find_banned(text) == [], key


# ---------------- screenshots ----------------

PNG = "data:image/png;base64," + base64.b64encode(b"\x89PNG\r\n\x1a\nfake").decode()


def test_image_decode_checks_type_and_size(monkeypatch):
    assert vision.decode(PNG)[0] == "image/png"
    with pytest.raises(vision.ImageError):
        vision.decode("data:image/gif;base64,R0lGOD")
    with pytest.raises(vision.ImageError):
        vision.decode("not a data url")
    monkeypatch.setattr(settings, "TIP_IMAGE_MAX_BYTES", 3)
    with pytest.raises(vision.ImageError, match="size"):
        vision.decode(PNG)


class FakeResponse:
    def __init__(self, status, data):
        self.status_code, self._data = status, data

    def json(self):
        return self._data


def test_gemini_reads_the_screenshot_with_the_users_key(monkeypatch):
    sent = {}

    def post(url, headers, json, timeout):
        sent.update(url=url, headers=headers, json=json)
        return FakeResponse(200, {"candidates": [{"content": {"parts": [{"text": "SUZLON sure shot, jaldi entry lo"}]}}]})

    monkeypatch.setattr(vision.httpx, "post", post)
    p = chat.Provider("gemini", "test-key", "gemini-flash-latest", "")
    assert vision.read_text("image/png", b"img", p) == "SUZLON sure shot, jaldi entry lo"  # not filtered: it is the tip's text
    assert sent["headers"] == {"x-goog-api-key": "test-key"}
    assert sent["json"]["contents"][0]["parts"][0]["inline_data"]["mime_type"] == "image/png"


def test_openai_compatible_reads_the_screenshot(monkeypatch):
    def post(url, headers, json, timeout):
        assert url.endswith("/chat/completions") and json["messages"][0]["content"][1]["type"] == "image_url"
        return FakeResponse(200, {"choices": [{"message": {"content": "text in image"}}]})

    monkeypatch.setattr(vision.httpx, "post", post)
    assert (
        vision.read_text("image/jpeg", b"img", chat.Provider("openai", "k", "gpt-4o-mini", "https://api.openai.com/v1"))
        == "text in image"
    )


def test_vision_errors_become_sentences(monkeypatch):
    monkeypatch.setattr(vision.httpx, "post", lambda *a, **k: FakeResponse(401, {"error": {"message": "bad key"}}))
    with pytest.raises(chat.ChatError, match="did not accept your key"):
        vision.read_text("image/png", b"img", chat.Provider("gemini", "k", "m", ""))

    def timeout(*a, **k):
        raise httpx.ReadTimeout("slow")

    monkeypatch.setattr(vision.httpx, "post", timeout)
    with pytest.raises(chat.ChatError, match="too long"):
        vision.read_text("image/png", b"img", chat.Provider("gemini", "k", "m", ""))


def test_image_api_needs_a_key_and_returns_text(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    c = TestClient(app)
    assert c.post("/api/tipcheck/image", json={"image": PNG}).status_code == 503
    assert c.post("/api/tipcheck/image", json={"image": "data:image/gif;base64,R0lGODlhAQABAAAAACw="}).status_code == 400
    monkeypatch.setattr(vision, "read_text", lambda mime, raw, p: "the tip text")
    r = c.post("/api/tipcheck/image", json={"image": PNG}, headers={"X-AI-Provider": "gemini", "X-AI-Key": "k"})
    assert r.status_code == 200 and r.json() == {"text": "the tip text"}
    monkeypatch.setattr(vision, "read_text", lambda mime, raw, p: "")
    assert (
        c.post("/api/tipcheck/image", json={"image": PNG}, headers={"X-AI-Provider": "gemini", "X-AI-Key": "k"}).status_code
        == 422
    )
