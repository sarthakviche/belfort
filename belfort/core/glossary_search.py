"""Ranked search over the glossary: pure functions, no network.

Order of preference: exact term, exact match phrase, term prefix, phrase prefix, a word of the term starting with the
query, substring of the term or a phrase, a close spelling (difflib), then a whole word in the explanation.
"""

import re
from difflib import SequenceMatcher
from urllib.parse import quote_plus

from .glossary import GLOSSARY

MAX_QUERY = 80
FUZZY_CUTOFF = 0.75
WEB_SEARCH = "https://www.google.com/search?q="


def clean(text: str) -> str:
    """Lower-case, hyphens and punctuation to single spaces, so 'stop-loss' equals 'stop loss'."""
    return re.sub(r"[^a-z0-9%&]+", " ", (text or "").lower()).strip()[:MAX_QUERY]


def web_search_url(term: str) -> str:
    return WEB_SEARCH + quote_plus(f"{(term or '').strip()[:MAX_QUERY]} stock market meaning")


def _score(q: str, entry: dict) -> float:
    term = clean(entry["term"])
    phrases = [clean(m) for m in entry["match"]]
    names = [term, *phrases]
    if q == term:
        return 100
    if q in phrases:
        return 95
    if term.startswith(q):
        return 85 - min(len(term) - len(q), 20) * 0.2
    if any(p.startswith(q) for p in phrases):
        return 78
    if any(w.startswith(q) for w in term.split()):
        return 72
    if q in term:
        return 62
    if any(q in p for p in phrases):
        return 55
    best = 0.0
    for n in names:
        best = max(best, SequenceMatcher(None, q, n).ratio())
        for w in n.split():
            if len(w) > 3:
                best = max(best, SequenceMatcher(None, q, w).ratio())
    if best >= FUZZY_CUTOFF and len(q) >= 3:
        return 30 + best * 20  # 45 to 50
    if len(q) >= 4 and re.search(rf"\b{re.escape(q)}\b", clean(entry["meaning"])):
        return 20
    return 0


def search(query: str, entries: list[dict] | None = None, limit: int = 20) -> list[dict]:
    """Ranked matches for `query`. An empty query returns every entry in dictionary order."""
    entries = GLOSSARY if entries is None else entries
    q = clean(query)
    if not q:
        return list(entries)
    scored = [(s, e) for e in entries if (s := _score(q, e)) > 0]
    scored.sort(key=lambda se: (-se[0], len(se[1]["term"]), se[1]["term"]))
    return [e for _, e in scored[:limit]]
