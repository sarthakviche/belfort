"""Fundamental read: yearly metrics, pros and cons, ranked concerns, peer comparison.

Every statement is tied to a figure and a period. Nothing is estimated: a figure that the source
does not return is reported as missing.
"""

import math

import numpy as np
import pandas as pd

from ...settings import FUND_SOURCE, QUARTER_STALE_DAYS

CR = 1e7  # rupees per crore
SEV_ORDER = {"high": 0, "medium": 1, "low": 2, "info": 3}


def _series(df, *names):
    if df is None or getattr(df, "empty", True):
        return None
    for n in names:
        if n in df.index:
            return df.loc[n]
    return None


def _v(series, period):
    if series is None or period not in series.index:
        return None
    x = series[period]
    try:
        x = float(x)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(x) else x


def _fy(p) -> str:
    return f"FY{pd.Timestamp(p).year}" if pd.Timestamp(p).month == 3 else pd.Timestamp(p).strftime("%b %Y")


def _cr(x) -> str:
    return f"₹{x / CR:,.0f} cr"


def _div(a, b):
    return a / b if a is not None and b not in (None, 0) else None


def _pct(x) -> str:
    return f"{x * 100:.1f}%"


def compute_metrics(raw: dict) -> dict:
    inc, bal, cf = raw.get("income"), raw.get("balance"), raw.get("cashflow")
    if inc is None or getattr(inc, "empty", True):
        return {"periods": [], "rows": {}}
    rev_s = _series(inc, "Total Revenue", "Operating Revenue")
    if rev_s is None:
        return {"periods": [], "rows": {}}
    periods = sorted([p for p in inc.columns if _v(rev_s, p) is not None])[-5:]
    series_by_metric = {
        "rev": rev_s,
        "op": _series(inc, "Operating Income", "EBIT"),
        "ebit": _series(inc, "EBIT", "Operating Income"),
        "ni": _series(inc, "Net Income", "Net Income Common Stockholders"),
        "pretax": _series(inc, "Pretax Income"),
        "int": _series(inc, "Interest Expense", "Interest Expense Non Operating"),
        "unusual": _series(inc, "Total Unusual Items", "Special Income Charges"),
        "other": _series(inc, "Other Non Operating Income Expenses"),
        "debt": _series(bal, "Total Debt"),
        "eq": _series(bal, "Stockholders Equity", "Common Stock Equity"),
        "recv": _series(bal, "Accounts Receivable", "Receivables"),
        "shares": _series(bal, "Ordinary Shares Number", "Share Issued"),
        "cfo": _series(cf, "Operating Cash Flow"),
    }
    rows = {
        k: []
        for k in (
            "revenue",
            "revenue_growth",
            "operating_margin",
            "net_margin",
            "net_income",
            "roe",
            "debt_to_equity",
            "interest_cover",
            "cfo_to_profit",
            "receivable_days",
            "receivables",
            "shares",
            "unusual_share",
            "other_income_share",
            "total_debt",
            "equity",
            "cfo",
        )
    }
    prev_rev = None
    for p in periods:
        g = {k: _v(s, p) for k, s in series_by_metric.items()}
        rows["revenue"].append(g["rev"])
        rows["revenue_growth"].append(_div(g["rev"] - prev_rev, prev_rev) if prev_rev else None)
        prev_rev = g["rev"]
        rows["operating_margin"].append(_div(g["op"], g["rev"]))
        rows["net_margin"].append(_div(g["ni"], g["rev"]))
        rows["net_income"].append(g["ni"])
        rows["roe"].append(_div(g["ni"], g["eq"]) if g["eq"] and g["eq"] > 0 else None)
        rows["debt_to_equity"].append(_div(g["debt"], g["eq"]) if g["eq"] and g["eq"] > 0 else None)
        rows["interest_cover"].append(_div(g["ebit"], abs(g["int"])) if g["int"] else None)
        rows["cfo_to_profit"].append(_div(g["cfo"], g["ni"]) if g["ni"] and g["ni"] > 0 else None)
        rows["receivable_days"].append(_div(g["recv"], g["rev"]) * 365 if g["recv"] is not None and g["rev"] else None)
        rows["receivables"].append(g["recv"])
        rows["shares"].append(g["shares"])
        rows["unusual_share"].append(_div(g["unusual"], g["pretax"]) if g["pretax"] and g["pretax"] > 0 else None)
        rows["other_income_share"].append(_div(g["other"], g["pretax"]) if g["pretax"] and g["pretax"] > 0 else None)
        rows["total_debt"].append(g["debt"])
        rows["equity"].append(g["eq"])
        rows["cfo"].append(g["cfo"])
    return {"periods": periods, "rows": rows}


def _concern(sev, title, detail, period):
    return {"severity": sev, "title": title, "detail": detail, "period": period, "source": FUND_SOURCE}


def analyse(raw: dict, is_lender: bool, peers: dict | None = None) -> dict:
    """Return the fundamental section. `raw` is the provider payload (statements + info)."""
    info = raw.get("info") or {}
    m = compute_metrics(raw)
    periods, metric_rows = m["periods"], m["rows"]
    if len(periods) < 2:
        return {
            "available": False,
            "verdict": None,
            "concerns": [],
            "pros": [],
            "cons": [],
            "missing_reason": "The data source returned fewer than two years of annual statements for this company.",
            "source": FUND_SOURCE,
            "as_of": None,
        }
    latest, previous = -1, -2
    two_back = -3 if len(periods) >= 3 else None
    fy, fy_p = _fy(periods[latest]), _fy(periods[previous])
    fy_p2 = _fy(periods[two_back]) if two_back else None
    g = lambda key, i: metric_rows[key][i] if i is not None else None  # noqa: E731
    concerns, pros, notes = [], [], []

    ni, rev = g("net_income", latest), g("revenue", latest)
    if ni is not None and ni < 0:
        concerns.append(
            _concern("high", "The company made a net loss", f"Net loss of {_cr(-ni)} in {fy} on sales of {_cr(rev)}.", fy)
        )

    rg = g("revenue_growth", latest)
    if rg is not None and rg < -0.05:
        concerns.append(
            _concern(
                "medium",
                "Sales are falling",
                f"Sales fell {_pct(-rg)} in {fy} versus {fy_p} ({_cr(g('revenue', previous))} to {_cr(rev)}).",
                fy,
            )
        )
    elif rg is not None and rg < 0:
        concerns.append(_concern("low", "Sales dipped slightly", f"Sales fell {_pct(-rg)} in {fy} versus {fy_p}.", fy))

    if is_lender:
        notes.append(
            "Debt, interest cover, receivables, operating margin and cash-flow checks are skipped for "
            "banks and lenders: borrowing is their raw material, so these ratios mean something different. "
            "Asset quality (bad loans) is not available from this data source."
        )
    else:
        de, de_old = g("debt_to_equity", latest), g("debt_to_equity", two_back if two_back else previous)
        old_fy = fy_p2 or fy_p
        if de is not None:
            rising = de_old is not None and de - de_old > 0.3
            if de > 1.5 and rising:
                concerns.append(
                    _concern(
                        "high",
                        "Debt is high and rising",
                        f"Debt to equity rose from {de_old:.2f} in {old_fy} to {de:.2f} in {fy} "
                        f"(total debt {_cr(g('total_debt', latest))}).",
                        fy,
                    )
                )
            elif de > 1.5:
                concerns.append(
                    _concern(
                        "medium",
                        "Debt is high",
                        f"Debt to equity is {de:.2f} in {fy} "
                        f"(total debt {_cr(g('total_debt', latest))}, equity {_cr(g('equity', latest))}).",
                        fy,
                    )
                )
            elif rising and de > 0.8:
                concerns.append(
                    _concern(
                        "medium",
                        "Debt is rising faster than equity",
                        f"Debt to equity rose from {de_old:.2f} in {old_fy} to {de:.2f} in {fy}.",
                        fy,
                    )
                )
            elif de < 0.5:
                pros.append({"title": "Low debt", "detail": f"Debt to equity is {de:.2f} in {fy}.", "period": fy})
        ic = g("interest_cover", latest)
        if ic is not None:
            if ic < 1.5:
                concerns.append(
                    _concern(
                        "high",
                        "Profit barely covers interest",
                        f"Operating profit was {ic:.1f} times interest cost in {fy}. Below 1.5 leaves little room.",
                        fy,
                    )
                )
            elif ic < 3:
                concerns.append(
                    _concern(
                        "medium", "Interest cover is thin", f"Operating profit was {ic:.1f} times interest cost in {fy}.", fy
                    )
                )
            elif ic > 6:
                pros.append(
                    {
                        "title": "Interest is comfortably covered",
                        "detail": f"Operating profit was {ic:.1f} times interest cost in {fy}.",
                        "period": fy,
                    }
                )
        om, om_p, om_p2 = g("operating_margin", latest), g("operating_margin", previous), g("operating_margin", two_back)
        if None not in (om, om_p, om_p2) and om < om_p < om_p2 and om_p2 - om >= 0.03:
            concerns.append(
                _concern(
                    "medium",
                    "Operating margin has fallen two years running",
                    f"Operating margin went {_pct(om_p2)} ({fy_p2}), {_pct(om_p)} ({fy_p}), {_pct(om)} ({fy}).",
                    fy,
                )
            )
        elif None not in (om, om_p) and om - om_p >= 0.015:
            pros.append(
                {
                    "title": "Operating margin improved",
                    "detail": f"Operating margin rose from {_pct(om_p)} in {fy_p} to {_pct(om)} in {fy}.",
                    "period": fy,
                }
            )
        rc, rc_p = g("receivables", latest), g("receivables", previous)
        if None not in (rc, rc_p, rg) and rc_p > 0:
            rc_g = rc / rc_p - 1
            if rc_g - rg > 0.15 and rc / rev > 0.12:  # ignore when receivables are under ~45 days of sales
                rc_p2, rg_p = g("receivables", two_back), g("revenue_growth", previous)
                twice = None not in (rc_p2, rg_p) and rc_p2 > 0 and (rc_p / rc_p2 - 1) - rg_p > 0.15
                concerns.append(
                    _concern(
                        "high" if twice and rc / rev > 0.25 else "medium",
                        "Money owed by customers is growing faster than sales",
                        f"Receivables grew {_pct(rc_g)} in {fy} while sales grew {_pct(rg)}"
                        + (" (second year running)" if twice else "")
                        + f". Receivable days: {g('receivable_days', previous):.0f} to {g('receivable_days', latest):.0f}.",
                        fy,
                    )
                )
        cfo, c2p = g("cfo", latest), g("cfo_to_profit", latest)
        if ni is not None and ni > 0 and cfo is not None:
            hist = [x for x in metric_rows["cfo_to_profit"][-3:] if x is not None]
            if cfo < 0:
                concerns.append(
                    _concern(
                        "high",
                        "Profit is not turning into cash",
                        f"Reported profit was {_cr(ni)} in {fy} but cash from operations was negative ({_cr(cfo)}).",
                        fy,
                    )
                )
            elif c2p is not None and c2p < 0.5 and hist and np.mean(hist) < 0.6:
                concerns.append(
                    _concern(
                        "medium",
                        "Cash from operations lags reported profit",
                        f"Cash from operations was {_pct(c2p)} of profit in {fy} "
                        f"({_cr(cfo)} against {_cr(ni)}); {len(hist)}-year average {_pct(float(np.mean(hist)))}.",
                        fy,
                    )
                )
            elif c2p is not None and c2p >= 0.8:
                pros.append(
                    {
                        "title": "Profit is backed by cash",
                        "detail": f"Cash from operations was {_pct(c2p)} of profit in {fy}.",
                        "period": fy,
                    }
                )

    un = g("unusual_share", latest)
    if un is not None and un > 0.30:
        concerns.append(
            _concern(
                "medium",
                "One-time gains lifted profit",
                f"Unusual items were {_pct(un)} of pre-tax profit in {fy}. Profit without them is lower.",
                fy,
            )
        )
    oth = g("other_income_share", latest)
    if not is_lender and oth is not None and oth > 0.40:
        concerns.append(
            _concern(
                "low",
                "A large share of profit is non-operating income",
                f"Other income was {_pct(oth)} of pre-tax profit in {fy}.",
                fy,
            )
        )
    sh, sh_old = g("shares", latest), g("shares", two_back if two_back else previous)
    if None not in (sh, sh_old) and sh_old > 0 and sh / sh_old - 1 > 0.10:
        concerns.append(
            _concern(
                "low",
                "Share count has risen (dilution)",
                f"Shares outstanding rose {_pct(sh / sh_old - 1)} between {fy_p2 or fy_p} and {fy}. "
                "Bonus issues and splits also raise this number.",
                fy,
            )
        )

    growth = [x for x in metric_rows["revenue_growth"] if x is not None]
    if growth and np.mean(growth) > 0.10 and (rg or 0) > 0:
        pros.append(
            {
                "title": "Sales are growing",
                "detail": f"Sales grew {_pct(float(np.mean(growth)))} a year on average over {len(growth)} years; "
                f"{_pct(rg)} in {fy}.",
                "period": fy,
            }
        )
    roe = g("roe", latest)
    if roe is not None and roe > 0.15:
        pros.append(
            {
                "title": "Good return on shareholder money",
                "detail": f"Return on equity was {_pct(roe)} in {fy} (profit divided by year-end equity).",
                "period": fy,
            }
        )
    elif roe is not None and 0 <= roe < 0.08:
        concerns.append(_concern("low", "Low return on shareholder money", f"Return on equity was {_pct(roe)} in {fy}.", fy))

    pe = info.get("trailingPE")
    peer_block = peers or {"available": False, "missing_reason": "This company is outside the built-in peer list."}
    if peer_block.get("available") and pe and peer_block.get("median_pe"):
        if pe > 1.5 * peer_block["median_pe"]:
            concerns.append(
                _concern(
                    "low",
                    "Priced well above peers",
                    f"P/E of {pe:.1f} against a peer median of {peer_block['median_pe']:.1f} "
                    f"({peer_block['sector']}). A high price leaves less room for disappointment.",
                    "latest",
                )
            )
        elif pe < 0.75 * peer_block["median_pe"]:
            pros.append(
                {
                    "title": "Priced below peers",
                    "detail": f"P/E of {pe:.1f} against a peer median of {peer_block['median_pe']:.1f}. "
                    "Cheap can also mean the market sees a problem.",
                    "period": "latest",
                }
            )

    concerns.append(
        {
            "severity": "info",
            "title": "Promoter pledge was not checked",
            "detail": "No pledge data is available from the current sources. Check the latest shareholding "
            "pattern filing on the exchange website before relying on this summary.",
            "period": None,
            "source": "not available",
        }
    )
    concerns.sort(key=lambda c: SEV_ORDER[c["severity"]])
    real = [c for c in concerns if c["severity"] != "info"]
    highs = sum(c["severity"] == "high" for c in real)
    meds = sum(c["severity"] == "medium" for c in real)
    if highs or meds >= 3:
        verdict = "cautious"
    elif meds <= 1 and len(pros) >= 3:
        verdict = "constructive"
    else:
        verdict = "neutral"

    labels = [_fy(p) for p in periods]
    fmt_pct = lambda xs: [None if x is None else round(x * 100, 1) for x in xs]  # noqa: E731
    table = [
        {"metric": "Sales (₹ cr)", "values": [None if x is None else round(x / CR) for x in metric_rows["revenue"]]},
        {"metric": "Sales growth %", "values": fmt_pct(metric_rows["revenue_growth"])},
        {"metric": "Net profit (₹ cr)", "values": [None if x is None else round(x / CR) for x in metric_rows["net_income"]]},
        {"metric": "Net margin %", "values": fmt_pct(metric_rows["net_margin"])},
        {"metric": "Return on equity %", "values": fmt_pct(metric_rows["roe"])},
    ]
    if not is_lender:
        table += [
            {"metric": "Operating margin %", "values": fmt_pct(metric_rows["operating_margin"])},
            {"metric": "Debt to equity", "values": [None if x is None else round(x, 2) for x in metric_rows["debt_to_equity"]]},
            {
                "metric": "Interest cover (times)",
                "values": [None if x is None else round(x, 1) for x in metric_rows["interest_cover"]],
            },
            {"metric": "Cash from operations / profit %", "values": fmt_pct(metric_rows["cfo_to_profit"])},
            {"metric": "Receivable days", "values": [None if x is None else round(x) for x in metric_rows["receivable_days"]]},
        ]
    return {
        "available": True,
        "verdict": verdict,
        "pros": pros,
        "cons": [{"title": c["title"], "detail": c["detail"], "period": c["period"]} for c in real],
        "concerns": concerns,
        "notes": notes,
        "is_lender": is_lender,
        "table": {"periods": labels, "rows": table},
        "valuation": {
            "pe": round(pe, 1) if pe else None,
            "price_to_book": info.get("priceToBook"),
            "market_cap_cr": round(info["marketCap"] / CR) if info.get("marketCap") else None,
            "missing_reason": None if pe else "P/E not returned by the source (often because earnings are negative)",
        },
        "peers": peer_block,
        "quarter": quarter_trend(raw.get("q_income")),
        "source": FUND_SOURCE,
        "as_of": pd.Timestamp(periods[latest]).strftime("%Y-%m-%d"),
        "history_note": f"Own-history comparison covers {labels[0]} to {labels[-1]}, the years the source returns.",
    }


def quarter_trend(q, today: pd.Timestamp | None = None) -> dict:
    """The latest quarter against the same quarter a year earlier, or against the quarter before when the year-ago
    one is missing. `stale` is set when the newest quarter is older than QUARTER_STALE_DAYS, so the page can say the
    source is behind instead of presenting old results as the latest."""
    rev, ni = _series(q, "Total Revenue", "Operating Revenue"), _series(q, "Net Income")
    if rev is None:
        return {"available": False, "missing_reason": "Quarterly results not returned by the source."}
    cols = sorted([c for c in q.columns if _v(rev, c) is not None])
    if not cols:
        return {"available": False, "missing_reason": "Quarterly results not returned by the source."}
    last = cols[-1]
    age = ((today or pd.Timestamp.today()).normalize() - pd.Timestamp(last)).days
    stale = age > QUARTER_STALE_DAYS
    stale_note = (
        f"The newest quarter this source has is {pd.Timestamp(last).strftime('%b %Y')}, {age} days ago; later results "
        "are not in it yet. Check the company's results on the NSE or BSE website."
        if stale
        else None
    )
    year_ago = [c for c in cols if abs((pd.Timestamp(last) - pd.Timestamp(c)).days - 365) <= 10]
    previous = [c for c in cols[:-1] if 80 <= (pd.Timestamp(last) - pd.Timestamp(c)).days <= 100]
    if year_ago:
        p, basis = year_ago[0], "year"
    elif previous:
        p, basis = previous[-1], "quarter"
    else:
        return {
            "available": False,
            "quarter": pd.Timestamp(last).strftime("%b %Y"),
            "stale": stale,
            "stale_note": stale_note,
            "missing_reason": "The source has no earlier quarter to compare with, so no change is shown.",
        }
    out = {
        "available": True,
        "quarter": pd.Timestamp(last).strftime("%b %Y"),
        "compared_with": pd.Timestamp(p).strftime("%b %Y"),
        "basis": basis,
        "as_of": pd.Timestamp(last).strftime("%Y-%m-%d"),
        "sales_growth_pct": round((_v(rev, last) / _v(rev, p) - 1) * 100, 1),
        "stale": stale,
        "stale_note": stale_note,
        "source": FUND_SOURCE,
    }
    a, b = _v(ni, last), _v(ni, p)
    out["profit_growth_pct"] = round((a / b - 1) * 100, 1) if a is not None and b and b > 0 else None
    return out


def peer_block(sector: str | None, peer_infos: dict[str, dict]) -> dict:
    if not sector:
        return {"available": False, "missing_reason": "This company is outside the built-in peer list."}
    rows = []
    for sym, info in peer_infos.items():
        if not info:
            continue
        de = info.get("debtToEquity")
        rows.append(
            {
                "symbol": sym,
                "pe": info.get("trailingPE"),
                "roe_pct": None if info.get("returnOnEquity") is None else round(info["returnOnEquity"] * 100, 1),
                "debt_to_equity": None if de is None else round(de / 100, 2),
            }
        )
    pes = [r["pe"] for r in rows if r["pe"]]
    if not rows:
        return {"available": False, "missing_reason": "Peer figures could not be fetched."}
    med = lambda xs: round(float(np.median(xs)), 2) if xs else None  # noqa: E731
    return {
        "available": True,
        "sector": sector,
        "rows": rows,
        "median_pe": med(pes),
        "median_roe_pct": med([r["roe_pct"] for r in rows if r["roe_pct"] is not None]),
        "source": "Yahoo Finance key ratios (trailing)",
        "as_of": "latest available",
    }
