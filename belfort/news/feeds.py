"""News vertical: read public RSS feeds, normalise each item into a story, tag it, and keep it for 15 minutes.

Only feed-provided fields are used (title, description, image, link). Belfort never scrapes or stores full articles:
the reader goes to the publisher to read the story.
"""

import hashlib
import html
import json
import re
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime

import httpx

from ..data.cache import cached
from ..settings import CONTENT_DIR, DATA_DIR

UA = {"User-Agent": "Mozilla/5.0 (compatible; Belfort-RSS/0.1; news reader)"}
MEDIA = "{http://search.yahoo.com/mrss/}"
TAG_RE = re.compile(r"<[^>]+>")

CATEGORIES = [  # first match wins; plain keyword rules so contributors can tune them
    ("Regulation", ["sebi", "rbi", "regulator", "circular", "policy rate", "repo rate", "monetary policy", "ministry", "tax"]),
    ("Results", ["q1", "q2", "q3", "q4", "quarter", "results", "net profit", "earnings", "revenue", "ebitda"]),
    ("IPOs", ["ipo", "listing", "gmp", "subscription", "anchor investors"]),
    ("Economy", ["gdp", "inflation", "cpi", "wpi", "fiscal", "rupee", "economy", "exports", "imports", "pmi"]),
    ("Global", ["fed", "wall street", "nasdaq", "dow", "us market", "china", "crude", "brent", "global"]),
    ("Markets", ["sensex", "nifty", "market", "stocks", "shares", "index", "fii", "dii", "rally", "sell-off"]),
]


def feeds() -> list[dict]:
    for f in (DATA_DIR / "feeds.json", CONTENT_DIR / "news" / "feeds.json"):
        if f.exists():
            return json.loads(f.read_text(encoding="utf-8"))["feeds"]
    return []


def _text(el, *names) -> str:
    for n in names:
        x = el.find(n)
        if x is not None and (x.text or "").strip():
            return x.text.strip()
    return ""


def clean(s: str, limit: int = 320) -> str:
    s = html.unescape(TAG_RE.sub(" ", html.unescape(s or "")))
    s = " ".join(s.split())
    if len(s) > limit:
        s = s[:limit].rsplit(" ", 1)[0] + "…"
    return s


def _image(item) -> str | None:
    for tag in (MEDIA + "content", MEDIA + "thumbnail", "enclosure"):
        x = item.find(tag)
        if x is not None and x.get("url") and (tag != "enclosure" or (x.get("type") or "").startswith("image")):
            return x.get("url")
    m = re.search(r'<img[^>]+src="([^"]+)"', item.findtext("description") or "")
    return html.unescape(m.group(1)) if m else None


def _when(s: str) -> str | None:
    if not s:
        return None
    try:
        d = parsedate_to_datetime(s)
    except (TypeError, ValueError):
        try:
            d = datetime.fromisoformat(s.replace("Z", "+00:00"))
        except ValueError:
            return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=UTC)
    return d.astimezone(UTC).isoformat()


# Headlines that pass on someone's buy/sell call or price target. Belfort hides them by default: it does not
# relay stock tips, even when a publisher prints them.
TIP_RE = re.compile(
    r"(stocks? to (buy|sell|watch|pick)|buy or sell|should you buy|buy,? sell,? hold|\bbuy\b.*\btarget\b|"
    r"\btarget price\b|\btarget,? (sl|stop)|(?-i:\bSL\b)|stop[- ]loss|multibagger|top picks?|\bpicks? for\b|"
    r"recommends? (a )?(buy|sell)|\bbrokerage(s)? (say|bet|bullish|suggest)|technical picks|trading ideas?|"
    r"(buy|sell|accumulate)\s+(rating|call)|(upside|downside) of\s+\d)",
    re.I,
)


def tip_style(title: str, summary: str) -> bool:
    return bool(TIP_RE.search(f"{title} {summary}"))


def categorise(title: str, summary: str) -> str:
    low = f" {title} {summary} ".lower()
    for name, words in CATEGORIES:
        if any(re.search(r"(?<![a-z])" + re.escape(w) + r"(?![a-z])", low) for w in words):
            return name
    return "Markets"


def parse(xml_text: str, feed: dict) -> list[dict]:
    root = ET.fromstring(xml_text.lstrip("﻿").strip())
    out = []
    for item in root.iter("item"):
        title = clean(_text(item, "title"), 220)
        link = _text(item, "link", "guid")
        if not title or not link.startswith("http"):
            continue
        summary = clean(item.findtext("description") or "")
        if summary.lower().startswith(title.lower()[:40]):
            summary = summary[len(title) :].strip(" -–:") if len(summary) > len(title) + 20 else ""
        out.append(
            {
                "id": hashlib.sha1(link.encode()).hexdigest()[:12],
                "title": title,
                "summary": summary,
                "url": link,
                "source": feed["name"],
                "source_id": feed["id"],
                "kind": feed.get("kind", "publisher"),
                "published": _when(_text(item, "pubDate", "{http://purl.org/dc/elements/1.1/}date")),
                "image": _image(item),
                "category": categorise(title, summary),
                "tip": tip_style(title, summary),
            }
        )
    return out


def _fetch(feed: dict) -> dict:
    try:
        r = httpx.get(feed["url"], headers=UA, timeout=10.0, follow_redirects=True)
        if r.status_code != 200:
            return {"feed": feed, "items": [], "error": f"HTTP {r.status_code}"}
        return {"feed": feed, "items": parse(r.text, feed), "error": None}
    except Exception as e:  # one bad feed must not break the page
        return {"feed": feed, "items": [], "error": type(e).__name__}


# ---- company tagging: the built-in stock lists, matched by symbol or by a short company name ----


def _aliases() -> dict[str, str]:
    from ..research.screens import BROADER, NIFTY

    names = {}
    try:
        from ..research.analysis.pipeline import nse

        listed = dict(nse.listed())
    except Exception:
        listed = {}
    for sym in set(NIFTY + BROADER):
        names[sym] = sym
        full = listed.get(sym)
        if full:
            short = re.sub(r"\b(limited|ltd\.?|corporation|company|co\.|india|industries)\b", "", full, flags=re.I)
            short = " ".join(short.replace("&", "and").split())
            if len(short) >= 4:
                names[short] = sym
    return names


def tag(stories: list[dict]) -> None:
    al = cached("news-aliases:v1", 7 * 86400, _aliases)
    pats = [
        (re.compile(r"(?<![A-Za-z])" + re.escape(k) + r"(?![A-Za-z])", 0 if k.isupper() else re.I), v)
        for k, v in sorted(al.items(), key=lambda kv: -len(kv[0]))
        if len(k) >= 3
    ]
    for s in stories:
        text = s["title"] + " " + s["summary"]
        found = []
        for p, sym in pats:
            if sym not in found and p.search(text):
                found.append(sym)
            if len(found) >= 4:
                break
        s["symbols"] = found


def build() -> dict:
    fs = feeds()
    with ThreadPoolExecutor(max_workers=6) as ex:
        results = list(ex.map(_fetch, fs))
    seen, stories = set(), []
    for res in results:
        for s in res["items"]:
            key = s["title"].lower()[:80]
            if key not in seen:
                seen.add(key)
                stories.append(s)
    stories.sort(key=lambda s: s["published"] or "", reverse=True)
    stories = stories[:150]
    try:
        tag(stories)
    except Exception:
        for s in stories:
            s.setdefault("symbols", [])
    return {
        "generated": datetime.now(UTC).isoformat(),
        "stories": stories,
        "sources": [
            {"name": r["feed"]["name"], "kind": r["feed"].get("kind"), "count": len(r["items"]), "error": r["error"]}
            for r in results
        ],
        "categories": [c for c, _ in CATEGORIES],
        "note": "Headlines and short descriptions as published in each source's public RSS feed. Open a story to read it "
        "on the publisher's site. News is not a signal to trade.",
    }


def get(refresh: bool = False) -> dict:
    key = "news:v2:" + datetime.now().strftime("%Y-%m-%d %H") + f":{datetime.now().minute // 15:02d}"
    if refresh:
        key += ":r" + datetime.now().strftime("%M%S")
    return cached(key, 15 * 60, build)
