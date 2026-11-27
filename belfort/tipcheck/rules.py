"""Tip Check rules. Pure functions: text, tables and price bars in, findings out. No network, no database.

Each check returns a Finding with a status:
  flag     a red flag was found
  clear    checked, and this red flag was not found
  unknown  could not be checked (no data, no stock recognised)
  info     context only, never counted as a flag
Belfort's own wording comes from strings.py; the tip's own words are only ever quoted back as evidence.
"""

import json
import re
import unicodedata
from dataclasses import asdict, dataclass, field
from functools import lru_cache
from pathlib import Path

import pandas as pd

from .. import settings
from .strings import t

PHRASES_FILE = Path(__file__).with_name("phrases.json")
PHRASE_CHECKS = ("promises", "target_days", "urgency", "secrecy", "money_ask")
COUNTED = ("registration",) + PHRASE_CHECKS + ("surveillance", "pump")
LESSONS = {
    "registration": "check-registration",
    "promises": "tip-scams",
    "target_days": "tip-scams",
    "urgency": "tip-scams",
    "secrecy": "myths",
    "money_ask": "tip-scams",
    "surveillance": "tip-scams",
    "pump": "tip-scams",
    "history": "myths",
}
REG_RE = re.compile(r"\b(IN[AHZP])[\s:\-]*(\d{5,13})\b", re.IGNORECASE)
EXPLICIT_SYMBOL_RE = re.compile(r"(?:\bNSE\s*[:\-]\s*|[#$])([A-Za-z][A-Za-z0-9&\-]{1,19})\b", re.IGNORECASE)
TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9&\-]{1,19}")
NAME_SUFFIXES = re.compile(r"\b(limited|ltd\.?|ltd|pvt|private|co\.?|corporation|corp\.?)\s*$", re.IGNORECASE)
MAX_EVIDENCE = 5


@dataclass
class Finding:
    id: str
    status: str
    detail: str
    evidence: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        d = asdict(self)
        d["title"] = t(f"{self.id}.title")
        d["lesson"] = LESSONS.get(self.id)
        return d


# ---------------- text ----------------


def normalise(text: str) -> str:
    """Fold case, width and curly quotes, and collapse whitespace, so phrase rules see one spelling."""
    text = unicodedata.normalize("NFKC", text or "")
    text = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", text).strip().casefold()


def _pattern(phrase: str) -> re.Pattern:
    if phrase.startswith("re:"):
        return re.compile(phrase[3:], re.IGNORECASE)
    if phrase.isascii():
        return re.compile(r"(?<![\w])" + re.escape(phrase.casefold()) + r"(?![\w])")
    return re.compile(re.escape(phrase))  # Devanagari: word edges are unreliable, match the phrase as written


@lru_cache(maxsize=1)
def phrase_rules() -> dict[str, list[re.Pattern]]:
    """Compiled phrase rules per flag, across every language in phrases.json."""
    data = json.loads(PHRASES_FILE.read_text(encoding="utf-8"))
    rules = {}
    for flag, by_lang in data.items():
        if flag.startswith("_"):
            continue
        rules[flag] = [_pattern(p) for phrases in by_lang.values() for p in phrases]
    return rules


def find_phrases(flag: str, text: str) -> list[str]:
    """The tip's own words that match a flag's phrases, in order. Overlapping matches merge into one quote, so
    "100% sure" and "sure shot" come back as "100% sure shot"."""
    norm = normalise(text)
    spans = sorted((m.start(), m.end()) for pat in phrase_rules()[flag] for m in pat.finditer(norm) if m.end() > m.start())
    merged: list[list[int]] = []
    for start, end in spans:
        if merged and start < merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    out = []
    for start, end in merged:
        quote = norm[start:end].strip()
        if quote and quote not in out:
            out.append(quote)
    return out[:MAX_EVIDENCE]


def phrase_check(flag: str, text: str) -> Finding:
    ev = find_phrases(flag, text)
    return Finding(flag, "flag" if ev else "clear", t(f"{flag}.{'flag' if ev else 'clear'}"), ev)


# ---------------- registration ----------------


def registration_numbers(text: str) -> list[str]:
    """Every SEBI-style number in the text (INA, INH, INZ, INP followed by digits), upper-cased, without spaces."""
    seen = []
    for m in REG_RE.finditer(unicodedata.normalize("NFKC", text or "")):
        n = m.group(1).upper() + m.group(2)
        if n not in seen:
            seen.append(n)
    return seen


def registration(text: str, register: dict | None, as_of: str | None) -> Finding:
    """Does the tip carry a valid adviser or analyst number that is in the register snapshot?

    `register` maps a number (INH000000000) to {"name": ...}; None when Belfort has no copy of SEBI's register.
    A number in the register is reported as found, never as proof: real numbers are copied by scammers.
    """
    numbers = registration_numbers(text)
    claims = find_phrases("authority", text)
    approvals = find_phrases("approval_claim", text)
    lines, statuses = [], []
    if approvals:
        lines.append(t("registration.approval"))
        statuses.append("flag")
    if not numbers:
        lines.append(t("registration.claimed_none" if claims else "registration.none"))
        statuses.append("flag")
    for n in numbers:
        prefix, digits = n[:3], n[3:]
        if len(digits) != 9:
            lines.append(t("registration.malformed", number=n))
            statuses.append("flag")
        elif prefix in ("INZ", "INP"):
            lines.append(t("registration.wrong_kind", number=n, kind=t(f"kind.{prefix}")))
            statuses.append("flag")
        elif register is None:
            lines.append(t("registration.no_register", number=n))
            statuses.append("unknown")
        elif n in register:
            lines.append(t("registration.found", number=n, as_of=as_of, name=register[n].get("name") or "a registered entity"))
            statuses.append("clear")
        else:
            lines.append(t("registration.not_found", number=n, as_of=as_of))
            statuses.append("flag")
    status = "flag" if "flag" in statuses else "unknown" if "unknown" in statuses else "clear"
    return Finding("registration", status, " ".join(lines), numbers + claims + approvals, {"numbers": numbers})


# ---------------- which stock ----------------


def _clean_name(name: str) -> str:
    name = re.sub(r"\s+", " ", name.strip())
    for _ in range(2):
        name = NAME_SUFFIXES.sub("", name).strip(" .,")
    return name.casefold()


def extract_symbols(text: str, companies: list[tuple[str, str]], limit: int = 3) -> list[str]:
    """NSE symbols named in the tip: explicit (NSE:XYZ, #XYZ, $XYZ), a symbol in capitals or of five letters or more,
    or a company's full name. Common words that happen to be symbols are skipped."""
    symbols = {s.upper() for s, _ in companies}
    not_symbols = set(json.loads(PHRASES_FILE.read_text(encoding="utf-8")).get("_not_symbols", []))
    found: list[tuple[int, str]] = []
    raw = unicodedata.normalize("NFKC", text or "")
    for m in EXPLICIT_SYMBOL_RE.finditer(raw):
        if m.group(1).upper() in symbols:
            found.append((m.start(1), m.group(1).upper()))
    for m in TOKEN_RE.finditer(raw):
        tok = m.group(0)
        up = tok.upper()
        if up in symbols and up not in not_symbols and (tok.isupper() or len(tok) >= 5):
            found.append((m.start(), up))
    low = normalise(raw)
    for sym, name in companies:
        clean = _clean_name(name)
        if len(clean) < 6:
            continue
        if " " in clean:
            i = low.find(clean)
            if i >= 0:
                found.append((i, sym.upper()))
        elif clean.isalpha() and clean.upper() not in not_symbols:
            # a one-word name ("Infosys") counts only when written with a capital, as a name would be
            m = re.search(rf"\b(?:{re.escape(clean.capitalize())}|{re.escape(clean.upper())})\b", raw)
            if m:
                found.append((m.start(), sym.upper()))
    out = []
    for _, s in sorted(found):
        if s not in out:
            out.append(s)
    return out[:limit]


# ---------------- NSE surveillance ----------------

MEASURES = (  # (column name starts with, string key, staged?)
    ("GSM", "measure.gsm", True),
    ("Long_Term_Additional_Surveillance_Measure", "measure.asm_long", True),
    ("Short_Term_Additional_Surveillance_Measure", "measure.asm_short", True),
    ("ESM", "measure.esm", True),
    ("Unsolicited_SMS", "measure.sms", False),
    ("Social Media Platforms", "measure.social", False),
    ("Insolvency_Resolution_Process", "measure.irp", False),
)
NOT_UNDER = {"", "100", "nan", "na", "-"}


def surveillance(symbol: str | None, rows: dict | None, as_of: str | None) -> Finding:
    """Is the stock on NSE's surveillance lists? `rows` maps a symbol to its row of NSE's REG1_IND file (column name to
    value). In that file 100 means the measure does not apply; any other value is the stage or flag."""
    if not symbol:
        return Finding("surveillance", "unknown", t("surveillance.no_symbol"))
    if rows is None:
        return Finding("surveillance", "unknown", t("surveillance.unavailable"))
    row = rows.get(symbol.upper())
    if row is None:
        return Finding("surveillance", "unknown", t("surveillance.not_listed", symbol=symbol, as_of=as_of))
    active, tip_flags = [], []
    for prefix, key, staged in MEASURES:
        for col, value in row.items():
            if col.strip().startswith(prefix):
                v = str(value).strip()
                if v.casefold() not in NOT_UNDER:
                    active.append(t(key, stage=v) if staged else t(key))
                    if key in ("measure.sms", "measure.social"):
                        tip_flags.append(key.split(".")[1])
                break
    facts = {"measures": active, "as_of": as_of, "tip_flags": tip_flags}
    if active:
        return Finding(
            "surveillance", "flag", t("surveillance.flag", symbol=symbol, measures="; ".join(active), as_of=as_of), facts=facts
        )
    return Finding("surveillance", "clear", t("surveillance.clear", symbol=symbol, as_of=as_of), facts=facts)


# ---------------- price and volume ----------------


def indian(n: float) -> str:
    """A whole number with Indian digit grouping: 930753 -> 9,30,753."""
    s = str(round(abs(n)))
    head, tail = s[:-3], s[-3:]
    groups = []
    while len(head) > 2:
        groups.insert(0, head[-2:])
        head = head[:-2]
    out = ",".join(([head] if head else []) + groups + [tail]) if head or groups else tail
    return ("-" if n < 0 else "") + out


def _pct(x: float) -> str:
    return f"{x * 100:.0f}"


def volume_ratio(df: pd.DataFrame) -> pd.Series:
    """Each session's volume as a multiple of the average of the 50 sessions before it."""
    base = df["volume"].rolling(settings.TIP_VOLUME_BASE_BARS).mean().shift(1)
    return df["volume"] / base


def pump(symbol: str | None, df: pd.DataFrame | None, market_cap: float | None) -> Finding:
    """A pump pattern: at least two of (a volume spike in the last few sessions, a sharp run-up, a small company)."""
    if not symbol:
        return Finding("pump", "unknown", t("pump.no_symbol"))
    need = settings.TIP_VOLUME_BASE_BARS + settings.TIP_VOLUME_RECENT_BARS + 1
    if df is None or len(df) < need or "volume" not in df:
        return Finding("pump", "unknown", t("pump.no_data", symbol=symbol))
    recent = volume_ratio(df).iloc[-settings.TIP_VOLUME_RECENT_BARS :].dropna()
    ratio = float(recent.max()) if len(recent) else 0.0
    spike_day = recent.idxmax().date().isoformat() if len(recent) else None
    spike = ratio >= settings.TIP_VOLUME_SPIKE
    runs = []
    for bars, limit in (settings.TIP_RUNUP_SHORT, settings.TIP_RUNUP_LONG):
        if len(df) > bars:
            change = float(df["close"].iloc[-1] / df["close"].iloc[-1 - bars] - 1)
            runs.append((bars, change, change >= limit))
    run = next((r for r in runs if r[2]), runs[0] if runs else None)
    crore = market_cap / 1e7 if market_cap else None
    small = crore is not None and crore < settings.TIP_SMALL_CAP_CRORE
    facts_text = [
        t("pump.spike", ratio=f"{ratio:.1f}", day=spike_day) if spike else t("pump.no_spike", ratio=f"{ratio:.1f}"),
        (t("pump.runup", pct=_pct(run[1]), bars=run[0]) if run[2] else t("pump.no_runup", pct=_pct(run[1]), bars=run[0]))
        if run
        else "",
        t("pump.size_unknown") if crore is None else t("pump.small" if small else "pump.large", crore=indian(crore)),
    ]
    signals = [spike, bool(run and run[2]), small]
    facts = {
        "volume_ratio": round(ratio, 2),
        "spike_day": spike_day,
        "runup_pct": round(run[1] * 100, 1) if run else None,
        "runup_bars": run[0] if run else None,
        "market_cap_crore": round(crore) if crore is not None else None,
        "signals": sum(signals),
    }
    joined = "; ".join(f for f in facts_text if f)
    status = "flag" if sum(signals) >= 2 else "clear"
    return Finding("pump", status, t(f"pump.{status}", symbol=symbol, facts=joined), facts=facts)


def past_signature(symbol: str | None, df: pd.DataFrame | None, today: pd.Timestamp | None = None) -> Finding:
    """The latest past session (at least EDU_LAG_DAYS old) with a volume spike after a sharp short run-up, and what the
    price did in the sessions after it. Only bars that old are used, for the episode and for its outcome."""
    if not symbol or df is None or len(df) < settings.TIP_VOLUME_BASE_BARS + 30:
        return Finding("history", "info", t("history.no_data"))
    today = today or pd.Timestamp.today().normalize()
    old = df[df.index <= today - pd.Timedelta(days=settings.EDU_LAG_DAYS)]
    if len(old) < settings.TIP_VOLUME_BASE_BARS + 30:
        return Finding("history", "info", t("history.no_data"))
    bars, limit = settings.TIP_RUNUP_SHORT
    ratio = volume_ratio(old)
    runup = old["close"] / old["close"].shift(bars) - 1
    hits = old.index[(ratio >= settings.TIP_VOLUME_SPIKE) & (runup >= limit)]
    if not len(hits):
        return Finding("history", "info", t("history.none", symbol=symbol, lag=settings.EDU_LAG_DAYS))
    day = hits[-1]
    i = old.index.get_loc(day)
    base = float(old["close"].iloc[i])
    after = old["close"].iloc[i + 1 : i + 1 + settings.TIP_HISTORY_GAP_BARS]
    parts, facts = [], {"day": day.date().isoformat(), "volume_ratio": round(float(ratio.loc[day]), 1)}
    for n in (20, settings.TIP_HISTORY_GAP_BARS):
        if len(after) >= n:
            change = float(after.iloc[n - 1] / base - 1)
            facts[f"after_{n}"] = round(change * 100, 1)
            parts.append(
                t(
                    "history.after",
                    n=n,
                    pct=f"{abs(change) * 100:.0f}",
                    direction=t("history.higher" if change >= 0 else "history.lower"),
                )
            )
    if len(after):
        low = float(after.min() / base - 1)
        facts["lowest"] = round(low * 100, 1)
        if low < 0:
            parts.append(t("history.low", n=len(after), pct=f"{abs(low) * 100:.0f}"))
    sentence = "; ".join(parts)
    after_text = (sentence[0].upper() + sentence[1:] + ".") if sentence else ""
    detail = t(
        "history.found",
        day=day.strftime("%d %b %Y"),
        symbol=symbol,
        ratio=f"{float(ratio.loc[day]):.1f}",
        runup=f"{float(runup.loc[day]) * 100:.0f}",
        bars=bars,
        after=after_text,
    )
    return Finding("history", "info", f"{detail} {t('history.note')}".replace("  ", " "), facts=facts)


# ---------------- summary ----------------


def level(findings: list[Finding]) -> tuple[str, int]:
    """(low | some | many, number of red flags) over the counted checks."""
    n = sum(1 for f in findings if f.id in COUNTED and f.status == "flag")
    return ("low" if n == 0 else "some" if n <= 2 else "many"), n


def text_checks(text: str, register: dict | None = None, register_as_of: str | None = None) -> list[Finding]:
    """Every check that needs only the tip's text. Works offline."""
    return [registration(text, register, register_as_of)] + [phrase_check(f, text) for f in PHRASE_CHECKS]
