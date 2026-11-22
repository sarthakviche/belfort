"""Journal analytics for closed practice trades. Pure functions: a list of trades in, plain numbers and sentences out.

Every figure describes the user's own past practice trades. Nothing here says what to trade next.
"""

from datetime import date

from ..settings import ANALYTICS_HOLDING_BUCKETS, ANALYTICS_MIN_GROUP, ANALYTICS_R_BUCKETS

MISTAKES = {
    "moved-stop": "Moved the stop",
    "no-plan": "No plan written",
    "chased": "Chased the entry",
    "sized-too-big": "Sized too big",
    "exited-early": "Exited early",
}
SETUPS = {
    "pullback": "Pullback",
    "breakout": "Breakout",
    "event": "Results or event",
    "other": "Other",
}


def holding_days(entry_date: str | None, exit_date: str | None) -> int | None:
    """Calendar days between entry and exit (0 for a same-day exit)."""
    if not entry_date or not exit_date:
        return None
    return (date.fromisoformat(exit_date) - date.fromisoformat(entry_date)).days


def _group(trades: list[dict]) -> dict:
    rs = [t["r"] for t in trades if t.get("r") is not None]
    wins = [r for r in rs if r > 0]
    return {
        "count": len(trades),
        "win_rate": round(len(wins) / len(rs), 3) if rs else None,
        "avg_r": round(sum(rs) / len(rs), 2) if rs else None,
        "total_r": round(sum(rs), 2) if rs else 0.0,
    }


def r_distribution(trades: list[dict]) -> list[dict]:
    """How many closed trades fell in each R band, from big losses to big wins."""
    edges = list(ANALYTICS_R_BUCKETS)
    out = [{"label": f"below {edges[0]:+g}R", "low": None, "high": edges[0], "count": 0}]
    out += [
        {"label": f"{lo:+g} to {hi:+g}R", "low": lo, "high": hi, "count": 0} for lo, hi in zip(edges, edges[1:], strict=False)
    ]
    out += [{"label": f"{edges[-1]:+g}R or more", "low": edges[-1], "high": None, "count": 0}]
    for t in trades:
        r = t.get("r")
        if r is None:
            continue
        for band in out:
            if (band["low"] is None or r >= band["low"]) and (band["high"] is None or r < band["high"]):
                band["count"] += 1
                break
    return out


def by_setup(trades: list[dict]) -> list[dict]:
    groups: dict[str, list[dict]] = {}
    for t in trades:
        groups.setdefault(t.get("setup") or "untagged", []).append(t)
    return sorted(
        ({"setup": k, "label": SETUPS.get(k, "Not tagged"), **_group(v)} for k, v in groups.items()), key=lambda g: -g["count"]
    )


def by_holding(trades: list[dict]) -> list[dict]:
    out = []
    for lo, hi in ANALYTICS_HOLDING_BUCKETS:
        members = [
            t for t in trades if (d := holding_days(t.get("entry_date"), t.get("exit_date"))) is not None and lo <= d <= hi
        ]
        label = f"{lo}+ days" if hi >= 10_000 else f"{lo} to {hi} days"
        out.append({"label": label, "low": lo, "high": hi, **_group(members)})
    return out


def by_mistake(trades: list[dict]) -> list[dict]:
    out = [
        {"mistake": k, "label": v, **_group([t for t in trades if k in (t.get("mistakes") or [])])} for k, v in MISTAKES.items()
    ]
    clean = [t for t in trades if not t.get("mistakes")]
    out.append({"mistake": "none", "label": "No mistake tagged", **_group(clean)})
    return out


def habits(setups: list[dict], holdings: list[dict], mistakes: list[dict]) -> dict:
    """The best and worst patterns in the user's own results, each backed by at least ANALYTICS_MIN_GROUP trades."""
    best, worst = [], []
    candidates = [("setup", g) for g in setups if g["setup"] != "untagged"] + [("holding", g) for g in holdings]
    candidates += [("clean", g) for g in mistakes if g["mistake"] == "none"]
    enough = [(kind, g) for kind, g in candidates if g["count"] >= ANALYTICS_MIN_GROUP and g["avg_r"] is not None]
    for kind, g in sorted(enough, key=lambda x: -x[1]["avg_r"])[:2]:
        if g["avg_r"] > 0:
            what = {
                "setup": f"{g['label']} trades",
                "holding": f"Trades held {g['label']}",
                "clean": "Trades with no mistake tagged",
            }[kind]
            best.append(f"{what} averaged {g['avg_r']:+.2f}R over {g['count']} trades.")
    for g in sorted(
        (g for g in mistakes if g["mistake"] != "none" and g["count"] >= ANALYTICS_MIN_GROUP), key=lambda g: g["total_r"]
    ):
        if g["total_r"] < 0:
            worst.append(f'"{g["label"]}" came up in {g["count"]} trades, which together lost {abs(g["total_r"]):.1f}R.')
    return {"best": best, "worst": worst[:3], "min_group": ANALYTICS_MIN_GROUP}


def summarise(trades: list[dict]) -> dict:
    """Everything the review screen shows, from closed trades that carry r, dates, setup and mistakes."""
    setups, holdings, mistakes = by_setup(trades), by_holding(trades), by_mistake(trades)
    return {
        "closed": len(trades),
        "overall": _group(trades),
        "r_distribution": r_distribution(trades),
        "by_setup": setups,
        "by_holding": holdings,
        "by_mistake": mistakes,
        "habits": habits(setups, holdings, mistakes),
        "setups": SETUPS,
        "mistakes": MISTAKES,
        "note": "These figures describe your own closed practice trades. A handful of trades is not enough to judge a habit; "
        f"patterns need at least {ANALYTICS_MIN_GROUP} trades before they are listed.",
    }
