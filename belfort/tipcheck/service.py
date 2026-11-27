"""Tip Check: read a forwarded stock tip and report the red flags found and not found.

The text checks run offline. The stock checks (NSE surveillance lists, prices, company size) run in parallel and
anything still running after TIP_TIME_BUDGET_SECONDS is reported as "could not check", so an answer comes back in
about ten seconds even on a slow connection.
"""

from concurrent.futures import ThreadPoolExecutor, wait
from pathlib import Path

from .. import settings
from ..data import market, symbols
from ..research.analysis import pipeline
from . import rules, sources
from .strings import SCORES_URL, SEBI_ADVISER_URL, SEBI_REGISTER_URL, t

_pool = ThreadPoolExecutor(max_workers=6, thread_name_prefix="tipcheck")
LESSON_IDS = ("tip-scams", "check-registration", "myths")


class TipError(Exception):
    pass


def companies() -> list[tuple[str, str]]:
    """(symbol, name) for every NSE equity, or the built-in list when NSE's file cannot be fetched."""
    try:
        rows = pipeline.nse.listed()
    except Exception:
        rows = []
    return rows or symbols.builtin_companies()


def _market_cap(symbol: str) -> float | None:
    cap = (pipeline.prices.info(symbol) or {}).get("marketCap")
    return float(cap) if cap else None


def _lessons() -> list[dict]:
    lessons_dir = Path(settings.CONTENT_DIR) / "learn" / "lessons"
    return [{"id": i, "title": t(f"lesson.{i}"), "available": (lessons_dir / f"{i}.md").exists()} for i in LESSON_IDS]


def _link(key: str, url: str) -> dict:
    return {"label": t(f"link.{key}"), "url": url}


def check(text: str, symbol: str | None = None) -> dict:
    text = (text or "").strip()[: settings.TIP_MAX_CHARS]
    if not text:
        raise TipError(t("error.empty"))
    register, register_as_of = sources.sebi_register()
    findings = rules.text_checks(text, register, register_as_of)

    rows = companies()
    found = rules.extract_symbols(text, rows)
    chosen = (symbol or "").strip().upper() or (found[0] if found else None)
    names = {s.upper(): n for s, n in rows}

    jobs = {"surveillance": _pool.submit(sources.surveillance_rows)}
    if chosen:
        jobs["bars"] = _pool.submit(market.bars, chosen, 5)
        jobs["cap"] = _pool.submit(_market_cap, chosen)
    wait(jobs.values(), timeout=settings.TIP_TIME_BUDGET_SECONDS)

    def result(name, default=None):
        f = jobs.get(name)
        if f is None or not f.done() or f.exception() is not None:
            return default
        return f.result()

    surv_rows, surv_as_of = result("surveillance", (None, None))
    bars = result("bars")
    findings.append(rules.surveillance(chosen, surv_rows, surv_as_of))
    findings.append(rules.pump(chosen, bars, result("cap")))
    findings.append(rules.past_signature(chosen, bars))

    lvl, n = rules.level(findings)
    return {
        "symbol": chosen,
        "name": names.get(chosen) if chosen else None,
        "symbols_found": found,
        "level": lvl,
        "level_text": t(f"level.{lvl}"),
        "flags": n,
        "checked": sum(1 for f in findings if f.id in rules.COUNTED and f.status != "unknown"),
        "summary": t("summary.flags", n=n) if n else t("summary.none"),
        "share_line": t("share.line", n=n),
        "limits": t("summary.limits"),
        "findings": [f.as_dict() for f in findings],
        "next_steps": [
            {"text": t("next.verify"), "links": [_link("advisers", SEBI_ADVISER_URL), _link("analysts", SEBI_REGISTER_URL)]},
            {"text": t("next.report"), "links": [_link("scores", SCORES_URL)]},
            {"text": t("next.never"), "links": []},
        ],
        "learn_intro": t("next.learn"),
        "lessons": _lessons(),
        "register_as_of": register_as_of,
    }
