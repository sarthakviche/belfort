"""Languages (T50): catalogue lookup for server-side messages, and the current request's language.

The catalogues are the same JSON files the web app and the Android app read: belfort/static/i18n/<lang>.json, flat
keys with dot namespaces, `{name}` placeholders, English as the source of truth and the fallback for any missing key.
See docs/ARCHITECTURE.md ("Languages").
"""

import json
import re
from contextvars import ContextVar
from functools import lru_cache
from pathlib import Path

from ..settings import CONTENT_DIR

DEFAULT = "en"
# code -> (name in English, name in its own script). English is first and the default.
LANGUAGES = {
    "en": ("English", "English"),
    "hi": ("Hindi", "हिन्दी"),
    "mr": ("Marathi", "मराठी"),
    "bn": ("Bengali", "বাংলা"),
    "ta": ("Tamil", "தமிழ்"),
    "te": ("Telugu", "తెలుగు"),
    "gu": ("Gujarati", "ગુજરાતી"),
    "kn": ("Kannada", "ಕನ್ನಡ"),
}
CATALOGUE_DIR = Path(__file__).resolve().parent.parent / "static" / "i18n"
COMPLIANCE_DIR = CONTENT_DIR / "compliance"

_current: ContextVar[str] = ContextVar("belfort_lang", default=DEFAULT)


def normalize(code: str | None) -> str:
    """A supported language code from a code, a tag like 'hi-IN' or an Accept-Language header; else English."""
    for part in (code or "").split(","):
        base = re.split(r"[-_;]", part.strip().lower())[0]
        if base in LANGUAGES:
            return base
    return DEFAULT


def current() -> str:
    return _current.get()


def set_current(lang: str | None):
    return _current.set(normalize(lang))


def reset_current(token):
    _current.reset(token)


@lru_cache(maxsize=16)
def catalogue(lang: str) -> dict[str, str]:
    """Every string of a language (keys starting with '_' are metadata)."""
    f = CATALOGUE_DIR / f"{normalize(lang)}.json"
    if not f.exists():
        return {}
    data = json.loads(f.read_text(encoding="utf-8"))
    return {k: v for k, v in data.items() if not k.startswith("_") and isinstance(v, str)}


def tr(lang: str | None, key: str, **vars) -> str:
    """Translate a key; fall back to English, then to the key itself. {name} placeholders are filled from vars.

    A var whose value starts with '@' is itself a catalogue key, translated first (for example stage='@stage.beginner').
    """
    lang = normalize(lang)
    text = catalogue(lang).get(key) or catalogue(DEFAULT).get(key) or key
    filled = {k: (tr(lang, v[1:]) if isinstance(v, str) and v.startswith("@") else v) for k, v in vars.items()}
    return re.sub(r"\{(\w+)\}", lambda m: str(filled.get(m.group(1), m.group(0))), text)


def language_name(lang: str | None) -> str:
    """The English name of a language, for prompts such as 'Reply in Hindi.'"""
    return LANGUAGES[normalize(lang)][0]


def reply_instruction(lang: str | None) -> str:
    """The sentence added to an assistant question so the answer comes in the chosen language ('' for English)."""
    lang = normalize(lang)
    if lang == DEFAULT:
        return ""
    return f"Reply in {language_name(lang)}. Keep market terms such as stop-loss, SEBI and NSE in English."


class LanguageMiddleware:
    """Pure ASGI middleware: reads X-Belfort-Lang, then ?lang=, then Accept-Language, and sets the request language."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        headers = {k.decode("latin-1").lower(): v.decode("latin-1") for k, v in scope.get("headers", [])}
        qs = scope.get("query_string", b"").decode("latin-1")
        m = re.search(r"(?:^|&)lang=([A-Za-z_-]+)", qs)
        raw = headers.get("x-belfort-lang") or (m.group(1) if m else None) or headers.get("accept-language")
        token = set_current(raw)
        try:
            return await self.app(scope, receive, send)
        finally:
            reset_current(token)


@lru_cache(maxsize=16)
def banned_phrases(lang: str) -> tuple[str, ...]:
    """The banned promise-style phrases for a language, kept as data in content/compliance/banned.<lang>.json."""
    f = COMPLIANCE_DIR / f"banned.{normalize(lang)}.json"
    if not f.exists():
        return ()
    return tuple(p.lower() for p in json.loads(f.read_text(encoding="utf-8")).get("phrases", []))


def find_banned(text: str, lang: str | None) -> list[str]:
    """Banned phrases of that language found in the text. English phrases live in core/compliance.py (unchanged)."""
    low = (text or "").lower()
    return [p for p in banned_phrases(lang or DEFAULT) if p in low]


def problems(lang: str) -> list[str]:
    """Problems in a catalogue compared with English: unknown keys, changed {placeholders} or changed HTML tags.

    Missing keys are allowed (they fall back to English). Run: python -m belfort.core.i18n hi
    """
    en = catalogue(DEFAULT)
    out = []
    for key, text in catalogue(lang).items():
        if key not in en:
            out.append(f"{key}: not in en.json")
            continue
        if sorted(re.findall(r"\{\w+\}", text)) != sorted(re.findall(r"\{\w+\}", en[key])):
            out.append(f"{key}: placeholders differ")
        if sorted(re.findall(r"</?\w+[^>]*>", text)) != sorted(re.findall(r"</?\w+[^>]*>", en[key])):
            out.append(f"{key}: HTML tags differ")
    return out


if __name__ == "__main__":
    import sys

    for code in sys.argv[1:] or [c for c in LANGUAGES if c != DEFAULT]:
        found = problems(code)
        print(f"{code}: {len(catalogue(code))}/{len(catalogue(DEFAULT))} keys, {len(found)} problems")
        for line in found:
            print("  " + line)
