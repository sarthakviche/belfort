"""Languages (T50): catalogues, fallback, the settings endpoint, translated lessons and the banned-wording checks."""

import json
import re
import shutil
import subprocess

import pytest
from fastapi.testclient import TestClient

from belfort import settings
from belfort.assistant import chat
from belfort.core import compliance, i18n
from belfort.learn import curriculum
from belfort.main import app

client = TestClient(app)
STATIC = settings.ROOT / "belfort" / "static"
LESSONS = settings.CONTENT_DIR / "learn" / "lessons"
OTHER = [c for c in i18n.LANGUAGES if c != "en"]


def test_eight_languages_english_first():
    assert list(i18n.LANGUAGES)[0] == "en" and len(i18n.LANGUAGES) == 8
    assert i18n.LANGUAGES["hi"][1] == "हिन्दी" and i18n.LANGUAGES["kn"][1] == "ಕನ್ನಡ"
    cfg = client.get("/api/config").json()
    assert [x["code"] for x in cfg["languages"]] == list(i18n.LANGUAGES)


def test_placeholder_substitution_and_fallback(monkeypatch):
    assert i18n.tr("en", "learn.min", n=7) == "7 min"
    assert i18n.tr("hi", "learn.min", n=7) != "7 min" and "7" in i18n.tr("hi", "learn.min", n=7)
    assert i18n.tr("en", "no.such.key") == "no.such.key"
    assert i18n.tr("xx", "nav.learn") == "Learn"  # an unknown language is English
    # a key missing from a language falls back to English
    real = i18n.catalogue
    monkeypatch.setattr(i18n, "catalogue", lambda lang: {} if lang == "ta" else real(lang))
    assert i18n.tr("ta", "nav.learn") == "Learn"
    # a var that starts with @ is itself a key
    assert i18n.tr("en", "server.locked", stage="@stage.advanced", before="@stage.intermediate", pct=80).startswith(
        "The Advanced stage is locked"
    )


def test_normalize_language_codes():
    assert i18n.normalize("hi-IN") == "hi" and i18n.normalize("ta_IN") == "ta"
    assert i18n.normalize("fr-FR,mr;q=0.8") == "mr"
    assert i18n.normalize(None) == "en" and i18n.normalize("zz") == "en"


@pytest.mark.parametrize("lang", OTHER)
def test_catalogue_matches_english(lang):
    data = json.loads((STATIC / "i18n" / f"{lang}.json").read_text(encoding="utf-8"))
    assert data["_meta"]["status"].startswith("machine-draft")
    assert i18n.problems(lang) == []
    en = i18n.catalogue("en")
    assert len(i18n.catalogue(lang)) >= 0.95 * len(en)
    for key, text in i18n.catalogue(lang).items():
        assert not re.search(r"[०-९০-৯௦-௯౦-౯૦-૯೦-೯]", text), f"{lang} {key}: use Latin digits"
        assert not i18n.find_banned(text, "hi" if lang == "hi" else None), key


def test_english_catalogue_is_the_source_for_the_code():
    en = i18n.catalogue("en")
    used = set()
    for f in STATIC.glob("*.js"):
        used |= set(re.findall(r'\bT\("([a-z0-9_.-]+)"\s*[,)]', f.read_text(encoding="utf-8")))
    html = (STATIC / "index.html").read_text(encoding="utf-8")
    used |= set(re.findall(r'data-i18n(?:-[a-z]+)?="([a-z0-9_.-]+)"', html))
    for f in (settings.ROOT / "belfort").rglob("*.py"):
        used |= set(re.findall(r'"(server\.[a-z_]+)"', f.read_text(encoding="utf-8")))
    missing = sorted(k for k in used if k not in en and not k.endswith("."))
    assert missing == []
    assert en["disclaimer"] == compliance.DISCLAIMER  # the translated notices are translations of this exact text


def test_settings_endpoint_stores_the_language(fresh_db):
    assert client.get("/api/settings/language").json()["language"] == "en"
    r = client.put("/api/settings/language", json={"language": "ta"})
    assert r.status_code == 200 and r.json()["language"] == "ta"
    assert client.get("/api/settings/language").json()["language"] == "ta"
    assert [x["code"] for x in r.json()["languages"]] == list(i18n.LANGUAGES)
    assert client.put("/api/settings/language", json={"language": "klingon"}).status_code == 400
    assert client.get("/api/settings/language").json()["language"] == "ta"


def test_locked_message_comes_in_the_chosen_language(fresh_db):
    r = client.get("/api/learn/lessons/capital-gains", headers={"X-Belfort-Lang": "hi"})
    locked = client.get("/api/learn/lessons/pullback-setup", headers={"X-Belfort-Lang": "hi"})
    assert r.status_code in (403, 404) and locked.status_code == 403
    assert locked.headers["x-error-key"] == "server.locked_testout"
    assert locked.json()["detail"] == i18n.tr(
        "hi", "server.locked_testout", stage="@stage.intermediate", before="@stage.beginner", pct=80
    )
    english = client.get("/api/learn/lessons/pullback-setup").json()["detail"]
    assert english.startswith("The Intermediate stage is locked")
    # ?lang= and Accept-Language also work
    assert client.get("/api/learn/lessons/pullback-setup?lang=mr").json()["detail"] != english
    assert client.get("/api/learn/lessons/pullback-setup", headers={"Accept-Language": "bn-IN"}).json()["detail"] != english


# ---------------- translated lessons ----------------
HINDI = sorted(p.stem for p in (LESSONS / "hi").glob("*.md"))


def _beginner_ids():
    return [x["id"] for m in curriculum.stage_modules() if m["stage"] == "beginner" for x in m["lessons"] if x["written"]]


def test_every_beginner_lesson_has_a_hindi_translation():
    assert sorted(_beginner_ids()) == HINDI and len(HINDI) == 16


@pytest.mark.parametrize("lesson_id", HINDI)
def test_hindi_lesson_matches_the_english_one(lesson_id):
    en_text = (LESSONS / f"{lesson_id}.md").read_text(encoding="utf-8")
    hi_text = (LESSONS / "hi" / f"{lesson_id}.md").read_text(encoding="utf-8")
    en, hi = curriculum.parse_lesson(en_text), curriculum.parse_lesson(hi_text)
    assert hi["meta"]["translation"] == "machine-draft" and hi["meta"]["minutes"] == en["meta"]["minutes"]
    assert len(hi["meta"]["objectives"]) == len(en["meta"]["objectives"])
    # directives and structure are unchanged
    directives = lambda t: re.findall(r"^::(?:chart|try).*$", t, re.M)  # noqa: E731
    assert directives(hi["body"]) == directives(en["body"])
    assert len(re.findall(r"^## ", hi["body"], re.M)) == len(re.findall(r"^## ", en["body"], re.M))
    assert len(re.findall(r"^\|", hi["body"], re.M)) == len(re.findall(r"^\|", en["body"], re.M))
    # the quiz has the same shape and the same answers
    assert len(hi["quiz"]) == len(en["quiz"]) > 0
    for h, e in zip(hi["quiz"], en["quiz"], strict=True):
        assert h["type"] == e["type"]
        assert h["q"] != e["q"]
        if e["type"] == "mc":
            assert len(h["options"]) == len(e["options"]) and h["answer"] == e["answer"]
        elif e["type"] == "tf":
            assert h["answer"] == e["answer"]
        elif e["type"] == "order":
            assert len(h["items"]) == len(e["items"])
        else:
            assert h["answer"] == e["answer"] and h["tolerance"] == e["tolerance"]
    # no banned promise-style wording, in Hindi or in the English words that may remain
    text = hi["text"] + json.dumps(hi["quiz"], ensure_ascii=False) + hi_text
    assert i18n.find_banned(text, "hi") == []
    assert compliance.find_banned(text) == []
    assert re.search(r"[ऀ-ॿ]", hi["body"])


def test_hindi_lessons_are_served_and_english_is_the_fallback(fresh_db):
    hi = client.get("/api/learn/lessons/stop-loss", headers={"X-Belfort-Lang": "hi"}).json()
    en = client.get("/api/learn/lessons/stop-loss").json()
    assert hi["translated"] and hi["lang"] == "hi" and hi["translation_status"] == "machine-draft" and hi["title"] != en["title"]
    assert not en["translated"] and en["lang"] == "en" and en["translations"] == ["hi"]
    assert [q["type"] for q in hi["quiz"]] == [q["type"] for q in en["quiz"]]
    # no Marathi lesson: English is shown, flagged as not translated
    mr = client.get("/api/learn/lessons/stop-loss", headers={"X-Belfort-Lang": "mr"}).json()
    assert not mr["translated"] and mr["title"] == en["title"] and mr["lang"] == "en"
    assert "Try it in Belfort" in en["html"] and "Belfort" in hi["html"] and "Try it in Belfort" not in hi["html"]


def test_hindi_quiz_is_graded_on_the_server_with_the_same_answers(fresh_db):
    hi = {"X-Belfort-Lang": "hi"}
    les = client.get("/api/learn/lessons/position-sizing", headers=hi).json()
    res = client.post("/api/learn/lessons/position-sizing/quiz", json={"answers": [0] * len(les["quiz"])}, headers=hi).json()
    right = client.post(
        "/api/learn/lessons/position-sizing/quiz", json={"answers": [r["answer"] for r in res["results"]]}, headers=hi
    ).json()
    assert right["passed"] and right["score"] == 1


def test_path_shows_translated_lesson_titles(fresh_db):
    en = client.get("/api/learn/path").json()
    hi = client.get("/api/learn/path", headers={"X-Belfort-Lang": "hi"}).json()
    title = lambda d: d["stages"][0]["modules"][0]["nodes"][0]["title"]  # noqa: E731
    assert title(en) != title(hi) and re.search(r"[ऀ-ॿ]", title(hi))


# ---------------- assistants answer in the chosen language ----------------
def test_ask_belfort_and_the_dictionary_pass_the_language(monkeypatch):
    seen = []

    def fake_ask(question, history=None, context="", mode="report", provider=None):
        seen.append(question)
        return "ठीक है।"

    monkeypatch.setattr(chat, "ask", fake_ask)
    h = {"X-AI-Provider": "gemini", "X-AI-Key": "k"}
    client.post("/api/chat", json={"question": "What is a stop-loss?", "mode": "general"}, headers={**h, "X-Belfort-Lang": "hi"})
    client.post("/api/glossary/ask", json={"term": "theta"}, headers={**h, "X-Belfort-Lang": "ta"})
    client.post("/api/chat", json={"question": "What is a stop-loss?", "mode": "general"}, headers=h)
    assert "Reply in Hindi." in seen[0] and seen[0].startswith("What is a stop-loss?")
    assert "Reply in Tamil." in seen[1]
    assert "Reply in" not in seen[2]


def test_hindi_banned_phrases_replace_an_ai_answer(monkeypatch):
    monkeypatch.setattr(chat, "ask", lambda *a, **k: "यह गारंटीड रिटर्न देता है, अभी खरीदें।")
    h = {"X-AI-Provider": "gemini", "X-AI-Key": "k", "X-Belfort-Lang": "hi"}
    r = client.post("/api/chat", json={"question": "क्या खरीदूँ?", "mode": "general"}, headers=h)
    assert r.json()["answer"] == i18n.tr("hi", "chat.blocked")
    assert i18n.find_banned("यह पक्का मुनाफ़ा है", "hi") == ["पक्का मुनाफ़ा"]
    assert i18n.find_banned("शेयर टिप से सावधान", "hi") == ["शेयर टिप"]
    assert i18n.find_banned("Guaranteed", "mr") == []  # no list for that language: English check lives in compliance.py


# ---------------- the browser code, run in node (skipped when node is not installed) ----------------
NODE = shutil.which("node")


def _run_js(script: str):
    harness = r"""
const fs = require("fs"), vm = require("vm"), path = require("path");
const dir = process.argv[1];
const store = {};
const doc = { documentElement: { dataset: {} }, querySelectorAll: () => [], addEventListener() {}, dispatchEvent(e) { (doc.events = doc.events || []).push(e.type + ":" + e.detail.lang); } };
const ctx = { document: doc, localStorage: { getItem: (k) => store[k] || null, setItem: (k, v) => { store[k] = v; } }, CustomEvent: class { constructor(t, o) { this.type = t; this.detail = o.detail; } },
  fetch: async (u) => { if (u.startsWith("/api")) return { ok: false }; const f = path.join(dir, u.replace("i18n/", "")); return fs.existsSync(f) ? { ok: true, json: async () => JSON.parse(fs.readFileSync(f, "utf8")) } : { ok: false }; },
  Intl, console, JSON };
vm.createContext(ctx);
vm.runInContext(fs.readFileSync(path.join(dir, "..", "i18n.js"), "utf8") + "\n;globalThis.I18N = I18N;", ctx);
(async () => { await ctx.I18N.ready; %s })();
"""
    out = subprocess.run(
        [NODE, "-e", harness % script, str(STATIC / "i18n")], capture_output=True, text=True, encoding="utf-8", timeout=60
    )
    assert out.returncode == 0, out.stderr
    return json.loads(out.stdout)


@pytest.mark.skipif(not NODE, reason="node is not installed")
def test_indian_number_grouping_with_latin_digits_in_every_language():
    script = """
const r = {};
for (const l of ["en", "hi", "ta", "bn", "kn"]) { await ctx.I18N.setLanguage(l, { quiet: true }); r[l] = [ctx.I18N.formatNumber(100000), ctx.I18N.formatNumber(1234567.891, { max: 2 }), ctx.I18N.formatMoney(1250000, 0), ctx.I18N.formatMoney(1234.5), ctx.I18N.formatNumber(999)]; }
console.log(JSON.stringify(r));"""
    r = _run_js(script)
    for lang in r:
        assert r[lang] == ["1,00,000", "12,34,567.89", "₹12,50,000", "₹1,234.50", "999"], lang


@pytest.mark.skipif(not NODE, reason="node is not installed")
def test_js_t_fallback_substitution_and_language_switch():
    script = """
const I = ctx.I18N, r = {};
r.en = I.t("learn.min", { n: 7 }); r.missing = I.t("no.such", null, "fallback"); r.key = I.t("no.such");
r.plural = [I.t("pr.calls", { n: 1 }), I.t("pr.calls", { n: 3 })];
await I.setLanguage("hi", { quiet: true });
r.hi = I.t("nav.learn"); r.hiVars = I.t("learn.min", { n: 7 }); r.lang = [doc.documentElement.lang, doc.documentElement.dir, doc.events.slice(-1)[0], store["belfort.lang"]];
await I.setLanguage("klingon", { quiet: true }); r.bad = I.lang;
console.log(JSON.stringify(r));"""
    r = _run_js(script)
    assert r["en"] == "7 min" and r["missing"] == "fallback" and r["key"] == "no.such"
    assert r["plural"] == ["1 call", "3 calls"]
    assert r["hi"] == i18n.catalogue("hi")["nav.learn"] and "7" in r["hiVars"]
    assert r["lang"] == ["hi", "ltr", "belfort:language:hi", "hi"]
    assert r["bad"] == "en"
