"""Find a company the way people type it: part of a name, initials, a nickname or a typo.

The index is built from the NSE listing (about 2,600 companies) with a built-in fallback, plus an alias table kept as
data in `content/symbols/aliases.json`. Ranking: exact symbol or alias, then symbol prefix, then name prefix, then
word prefixes, then initials, then substrings, then typo-tolerant matches. Inside each tier, large caps come first.
"""

import json
import re
import threading
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from functools import lru_cache

from .. import settings
from .universe import SECTOR_OF

SYMBOLS_DIR = settings.CONTENT_DIR / "symbols"
_TOKEN_RE = re.compile(r"[a-z0-9&]+")
_NAME_FILLER = {"limited", "ltd", "the", "of", "and", "india", "company", "co"}
_QUERY_FILLER = {"ltd", "limited"}
_INITIALS_SKIP = {"limited", "ltd", "the", "of", "and", "&", "co"}

# Ranking tiers, lowest first.
EXACT, SYMBOL_PREFIX, NAME_PREFIX, WORD_PREFIX, INITIALS, SUBSTRING, FUZZY = range(7)


@dataclass
class Company:
    symbol: str
    name: str
    sector: str | None
    is_large_cap: bool
    words: list[str] = field(default_factory=list)
    initials: str = ""
    name_lower: str = ""


def display_name(name: str) -> str:
    """The company name without a trailing "Limited" or "Ltd"."""
    return re.sub(r"\s+(Limited|Ltd\.?)$", "", name.strip(), flags=re.IGNORECASE)


def _tokens(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def _compact(text: str) -> str:
    return re.sub(r"[^A-Z0-9&\-]", "", text.upper())


def load_aliases() -> dict[str, str]:
    """Lower-case nickname -> NSE symbol."""
    raw = json.loads((SYMBOLS_DIR / "aliases.json").read_text(encoding="utf-8"))["aliases"]
    return {" ".join(_tokens(k)): v.upper() for k, v in raw.items()}


def builtin_companies() -> list[tuple[str, str]]:
    """(symbol, name) for the built-in list, used when the NSE listing cannot be fetched."""
    raw = json.loads((SYMBOLS_DIR / "companies.json").read_text(encoding="utf-8"))["companies"]
    return [(c["symbol"], c["name"]) for c in raw]


class SymbolIndex:
    """An in-memory search index over (symbol, name) rows."""

    def __init__(self, rows: list[tuple[str, str]], aliases: dict[str, str] | None = None):
        self.companies: list[Company] = []
        self.by_symbol: dict[str, Company] = {}
        self.word_index: dict[str, set[int]] = {}
        self.aliases = aliases if aliases is not None else load_aliases()
        well_known = set(SECTOR_OF) | {symbol for symbol, _ in builtin_companies()}
        for symbol, name in rows:
            symbol = symbol.strip().upper()
            if not symbol or symbol in self.by_symbol:
                continue
            words = _tokens(name)
            company = Company(
                symbol=symbol,
                name=display_name(name),
                sector=SECTOR_OF.get(symbol),
                is_large_cap=symbol in well_known,
                words=words,
                initials="".join(w[0] for w in words if w not in _INITIALS_SKIP),
                name_lower=" ".join(words),
            )
            i = len(self.companies)
            self.companies.append(company)
            self.by_symbol[symbol] = company
            for word in set(words) - _NAME_FILLER:
                self.word_index.setdefault(word, set()).add(i)
        self._position = {c.symbol: i for i, c in enumerate(self.companies)}
        self._fuzzy_pool = list(self.word_index.items()) + [(c.symbol.lower(), {i}) for i, c in enumerate(self.companies)]
        self.search = lru_cache(maxsize=512)(self._search)

    def _tier(self, company: Company, query: str, q_symbol: str, tokens: list[str]) -> int | None:
        if company.symbol == q_symbol:
            return EXACT
        if company.symbol.startswith(q_symbol):
            return SYMBOL_PREFIX
        if company.name_lower.startswith(query):
            return NAME_PREFIX
        if all(any(w.startswith(t) for w in company.words) for t in tokens):
            return WORD_PREFIX
        if len(q_symbol) >= settings.SEARCH_MIN_INITIALS and company.initials.startswith(q_symbol.lower()):
            return INITIALS
        if len(query) >= settings.SEARCH_MIN_SUBSTRING and (query in company.name_lower or q_symbol in company.symbol):
            return SUBSTRING
        return None

    def _fuzzy(self, tokens: list[str]) -> dict[int, float]:
        """Companies whose name words (or symbol) are close to every query token, with a 0-1 closeness score."""
        threshold = settings.SEARCH_FUZZY_MIN_RATIO
        totals: dict[int, float] | None = None
        for token in tokens:
            scores: dict[int, float] = {}
            if token in self.word_index:  # an exact word needs no fuzzing
                for i in self.word_index[token]:
                    scores[i] = 1.0
            else:
                matcher = SequenceMatcher(None, "", token)  # b is the query token: difflib caches work on b
                for word, ids in self._fuzzy_pool:
                    if abs(len(word) - len(token)) > 2:
                        continue
                    matcher.set_seq1(word)
                    if matcher.real_quick_ratio() < threshold or matcher.quick_ratio() < threshold:
                        continue
                    ratio = matcher.ratio()
                    if ratio >= threshold:
                        for i in ids:
                            scores[i] = max(scores.get(i, 0.0), ratio)
            totals = scores if totals is None else {i: totals[i] + s for i, s in scores.items() if i in totals}
            if not totals:
                return {}
        return {i: s / len(tokens) for i, s in (totals or {}).items()}

    def _search(self, raw_query: str, limit: int) -> tuple[dict, ...]:
        tokens = _tokens(raw_query.removesuffix(".ns").removesuffix(".NS"))
        tokens = [t for t in tokens if t not in _QUERY_FILLER] or tokens  # "HDFC Bank Ltd" -> hdfc bank
        if not tokens:
            return ()
        query = " ".join(tokens)
        q_symbol = _compact(raw_query.removesuffix(".ns").removesuffix(".NS"))
        best: dict[int, tuple] = {}

        alias = self.aliases.get(query)
        if alias in self._position:
            best[self._position[alias]] = (EXACT, 0.0)
        if len(query) >= settings.SEARCH_MIN_SUBSTRING:
            for key, symbol in self.aliases.items():
                if key.startswith(query) and symbol in self._position:
                    best.setdefault(self._position[symbol], (NAME_PREFIX, 0.0))

        for i, company in enumerate(self.companies):
            tier = self._tier(company, query, q_symbol, tokens)
            if tier is not None and (i not in best or (tier, 0.0) < best[i]):
                best[i] = (tier, 0.0)

        if len(best) < limit and len(query) >= settings.SEARCH_MIN_FUZZY:
            for i, score in self._fuzzy(tokens).items():
                best.setdefault(i, (FUZZY, -score))

        def order(i: int) -> tuple:
            c = self.companies[i]
            tier, fuzz = best[i]
            return (tier, not c.is_large_cap, fuzz, len(c.name), c.symbol)

        picked = sorted(best, key=order)[:limit]
        return tuple(
            {"symbol": self.companies[i].symbol, "name": self.companies[i].name, "sector": self.companies[i].sector}
            for i in picked
        )


# ---------------- module-level index and last-close memory ----------------

_lock = threading.Lock()
_index: tuple[tuple, SymbolIndex] | None = None
_closes: dict[str, dict] | None = None


def index_for(rows: list[tuple[str, str]]) -> SymbolIndex:
    """A shared index for these rows, rebuilt only when the listing changes. Falls back to the built-in list."""
    global _index
    rows = rows or builtin_companies()
    signature = (len(rows), rows[0], rows[-1])
    with _lock:
        if _index is None or _index[0] != signature:
            _index = (signature, SymbolIndex(rows))
        return _index[1]


def _closes_file():
    return settings.CACHE_DIR / "last_closes.json"


def _load_closes() -> dict[str, dict]:
    global _closes
    if _closes is None:
        try:
            _closes = json.loads(_closes_file().read_text(encoding="utf-8"))
        except (OSError, ValueError):
            _closes = {}
    return _closes


def remember_close(symbol: str, close: float, as_of: str) -> None:
    """Keep the latest close we fetched for a symbol so search results can show it without a new fetch."""
    with _lock:
        closes = _load_closes()
        if closes.get(symbol, {}).get("as_of", "") > as_of:
            return
        closes[symbol] = {"last_close": round(float(close), 2), "as_of": as_of}
        try:
            settings.CACHE_DIR.mkdir(parents=True, exist_ok=True)
            _closes_file().write_text(json.dumps(closes), encoding="utf-8")
        except OSError:
            pass


def known_close(symbol: str) -> dict:
    """The last close Belfort remembered for a symbol ({last_close, as_of}), or {} if it has none."""
    with _lock:
        return dict(_load_closes().get(symbol, {}))


def search(rows: list[tuple[str, str]], query: str, limit: int | None = None) -> list[dict]:
    """Ranked matches for a query, each with symbol, name, sector and, when known, last_close and as_of."""
    results = index_for(rows).search((query or "").strip(), limit or settings.SEARCH_LIMIT)
    with _lock:
        closes = _load_closes()
    return [{**r, **closes.get(r["symbol"], {})} for r in results]
