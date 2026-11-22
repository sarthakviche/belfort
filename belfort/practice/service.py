"""Practice vertical: a paper account, a prediction journal and a chart-replay trainer. Virtual points only."""

import json
import random
import secrets
from datetime import date

from ..core import db
from ..data import market
from ..data.providers import DataError, clean_symbol
from ..data.universe import ALL_SYMBOLS
from ..research.analysis.sizing import position_size, suggest_stop
from ..settings import (
    EDU_LAG_DAYS,
    PAPER_COST_PCT,
    PAPER_DEFAULT_RISK_PCT,
    PAPER_MAX_RISK_PCT,
    PAPER_START_POINTS,
    PREDICTION_HORIZONS,
    REPLAY_MIN_HISTORY_BARS,
    REPLAY_VISIBLE_BARS,
    REPLAY_WINDOW_BARS,
    STYLES,
    TICKET_CHART_BARS,
    TRAIL_ATR_RANGE,
    TRAIL_PCT_RANGE,
)
from . import engine


class PracticeError(Exception):
    pass


def _today() -> str:
    return date.today().isoformat()


# ---------------- paper account ----------------


def account() -> dict:
    with db.connect() as con:
        row = con.execute("SELECT * FROM accounts ORDER BY id LIMIT 1").fetchone()
        if not row:
            con.execute("INSERT INTO accounts (name, start_points) VALUES (?, ?)", ("Practice account", PAPER_START_POINTS))
            row = con.execute("SELECT * FROM accounts ORDER BY id LIMIT 1").fetchone()
        return dict(row)


def _trades(account_id: int) -> list[dict]:
    with db.connect() as con:
        return db.rows(con.execute("SELECT * FROM trades WHERE account_id = ? ORDER BY id DESC", (account_id,)))


def settle_all(force: bool = False) -> None:
    """Replay end-of-day bars against every pending and open trade, at most once per new trading day.

    New bars only arrive once a day, and orders placed or exits requested today act on the next session's bar, so a
    second settlement on the same data day cannot change anything. A day is marked settled only if every symbol loaded.
    """
    acc = account()
    day = market.data_day()
    if acc.get("settled_for") == day and not force:
        return
    live = [t for t in _trades(acc["id"]) if t["status"] in ("pending", "open")]
    frames = {}
    complete = True
    for t in live:
        if t["symbol"] not in frames:
            try:
                frames[t["symbol"]] = market.bars(t["symbol"], 1)
            except Exception:
                frames[t["symbol"]] = None
        df = frames[t["symbol"]]
        if df is None:
            complete = False
            continue
        f = engine.settle_trade(t, df)
        current = f.stop if f.stop is not None else t.get("current_stop")
        if f.status != t["status"] or f.entry_price != t["entry_price"] or current != t.get("current_stop"):
            with db.connect() as con:
                con.execute(
                    "UPDATE trades SET status=?, entry_price=?, entry_date=?, exit_price=?, exit_date=?, exit_reason=?, "
                    "current_stop=? WHERE id=?",
                    (f.status, f.entry_price, f.entry_date, f.exit_price, f.exit_date, f.exit_reason, current, t["id"]),
                )
    if complete:
        with db.connect() as con:
            con.execute("UPDATE accounts SET settled_for = ? WHERE id = ?", (day, acc["id"]))


def _last_closes(symbols: set[str]) -> dict[str, tuple[float, str]]:
    out = {}
    for s in symbols:
        try:
            df = market.bars(s, 1)
            out[s] = (float(df["close"].iloc[-1]), df.index[-1].strftime("%Y-%m-%d"))
        except Exception:
            pass
    return out


def _cost(value: float) -> float:
    return round(value * PAPER_COST_PCT, 2)


def portfolio() -> dict:
    settle_all()
    acc = account()
    trades = _trades(acc["id"])
    marks = _last_closes({t["symbol"] for t in trades if t["status"] in ("open", "pending")})
    cash, reserved, invested, market_value = acc["start_points"], 0.0, 0.0, 0.0
    open_rows, pending_rows, closed_rows = [], [], []
    for t in trades:
        if t["status"] in ("open", "closed"):
            buy = t["entry_price"] * t["qty"]
            cash -= buy + _cost(buy)
        if t["status"] == "closed":
            sell = t["exit_price"] * t["qty"]
            cash += sell - _cost(sell)
            pnl = (t["exit_price"] - t["entry_price"]) * t["qty"] - _cost(buy) - _cost(sell)
            closed_rows.append({**t, "pnl": round(pnl, 2), "r": engine.r_multiple(t["entry_price"], t["stop"], t["exit_price"])})
        elif t["status"] == "open":
            last, as_of = marks.get(t["symbol"], (t["entry_price"], t["entry_date"]))
            invested += buy
            market_value += last * t["qty"]
            open_rows.append(
                {
                    **t,
                    "current_stop": current_stop(t),
                    "last": last,
                    "as_of": as_of,
                    "pnl": round((last - t["entry_price"]) * t["qty"], 2),
                    "open_r": engine.r_multiple(t["entry_price"], t["stop"], last),
                }
            )
        elif t["status"] == "pending":
            est = (t["limit_price"] or marks.get(t["symbol"], (0, None))[0]) * t["qty"]
            reserved += est + _cost(est)
            pending_rows.append(t)
    wins = [t for t in closed_rows if t["pnl"] > 0]
    rs = [t["r"] for t in closed_rows if t["r"] is not None]
    equity = cash + market_value
    return {
        "account": acc,
        "cash": round(cash, 2),
        "available": round(cash - reserved, 2),
        "reserved": round(reserved, 2),
        "invested": round(invested, 2),
        "market_value": round(market_value, 2),
        "equity": round(equity, 2),
        "return_pct": round((equity / acc["start_points"] - 1) * 100, 2),
        "open": open_rows,
        "pending": pending_rows,
        "closed": closed_rows[:50],
        "stats": {
            "closed": len(closed_rows),
            "win_rate": round(len(wins) / len(closed_rows), 3) if closed_rows else None,
            "avg_r": round(sum(rs) / len(rs), 2) if rs else None,
            "expectancy_note": "Average R is the average result per trade in units of the risk you took. Above 0 "
            "means the process made more than it lost, on these trades, after rough costs.",
        },
        "note": "Virtual points only (1 point stands for ₹1). They have no money value and cannot be redeemed. "
        "Fills use end-of-day prices: orders fill at the next session's open.",
    }


def quote(symbol: str) -> dict:
    """What the order ticket shows for a stock: last close, day change, a 3-month chart, nearest support, a stop idea."""
    from ..research.analysis.pipeline import technical

    symbol = clean_symbol(symbol)
    try:
        df = market.bars(symbol, 1)
    except DataError as e:
        raise PracticeError(str(e)) from e
    if len(df) < 2:
        raise PracticeError(f"Not enough price history for {symbol} yet.")
    last, prev = float(df["close"].iloc[-1]), float(df["close"].iloc[-2])
    tech = technical(df, STYLES["swing"])
    supports = [s for s in tech["levels"]["supports"] if s["price"] < last]
    stop = suggest_stop(last, tech["atr"], supports, STYLES["swing"])
    recent = df.tail(TICKET_CHART_BARS)
    return {
        "symbol": symbol,
        "last_close": round(last, 2),
        "as_of": df.index[-1].strftime("%Y-%m-%d"),
        "change_pct": round((last / prev - 1) * 100, 2),
        "candles": [
            {
                "time": d.strftime("%Y-%m-%d"),
                "open": float(r.open),
                "high": float(r.high),
                "low": float(r.low),
                "close": float(r.close),
            }
            for d, r in recent.iterrows()
        ],
        "support": {"price": round(supports[0]["price"], 2), "touches": supports[0]["touches"]} if supports else None,
        "suggested_stop": stop["stop"],
        "stop_basis": stop["basis"],
        "source": "Daily prices (Yahoo Finance, NSE end-of-day file), computed by this app",
        "default_risk_pct": PAPER_DEFAULT_RISK_PCT,
        "max_risk_pct": PAPER_MAX_RISK_PCT,
        "note": "A stop idea from the swing rule, not a recommendation. Where the stop goes is your decision.",
    }


def size(symbol: str, risk_pct: float, stop: float, entry: float | None = None) -> dict:
    """Shares that risk at most risk_pct of the account between entry and stop, capped by the points available."""
    symbol = clean_symbol(symbol)
    if entry is None:
        try:
            entry = float(market.bars(symbol, 1)["close"].iloc[-1])
        except DataError as e:
            raise PracticeError(str(e)) from e
    pf = portfolio()
    sized = position_size(pf["equity"], risk_pct, entry, stop)
    if sized["error"] and sized["quantity"] == 0 and sized["risk_per_share"] is None:
        raise PracticeError(sized["error"])
    by_points = int(max(0.0, pf["available"]) // (entry * (1 + PAPER_COST_PCT)))
    qty = min(sized["quantity"], by_points)
    risk = round(qty * (entry - stop), 2)
    return {
        "symbol": symbol,
        "entry": round(entry, 2),
        "stop": stop,
        "risk_pct": risk_pct,
        "quantity": qty,
        "risk_amount": risk,
        "risk_share_pct": round(risk / pf["equity"] * 100, 2) if pf["equity"] > 0 else None,
        "position_value": round(qty * entry, 2),
        "account_value": pf["equity"],
        "available": pf["available"],
        "capped_by_points": by_points < sized["quantity"],
        "over_limit": risk_pct > PAPER_MAX_RISK_PCT,
        "message": sized["error"] if qty == 0 else None,
    }


def place_trade(
    symbol: str,
    qty: int,
    stop: float,
    target: float | None,
    thesis: str,
    confidence: float | None,
    entry_type: str = "market",
    limit_price: float | None = None,
) -> dict:
    symbol = clean_symbol(symbol)
    if qty < 1:
        raise PracticeError("Quantity must be at least 1 share.")
    if entry_type not in ("market", "limit"):
        raise PracticeError("Order type must be market or limit.")
    if entry_type == "limit" and not limit_price:
        raise PracticeError("A limit order needs a limit price.")
    if len((thesis or "").strip()) < 10:
        raise PracticeError(
            "Write one line on why you are taking this trade (at least 10 characters). "
            "Reviewing that reason later is most of the learning."
        )
    try:
        df = market.bars(symbol, 1)
    except DataError as e:
        raise PracticeError(str(e)) from e
    last = float(df["close"].iloc[-1])
    ref = float(limit_price) if entry_type == "limit" else last
    if stop >= ref:
        raise PracticeError(f"The stop must be below the entry price (about ₹{ref:.2f}). Practice is long only for now.")
    if target is not None and target <= ref:
        raise PracticeError("The target must be above the entry price.")
    pf = portfolio()
    need = ref * qty * (1 + PAPER_COST_PCT)
    if need > pf["available"]:
        raise PracticeError(f"Not enough points: this needs about {need:,.0f}, you have {pf['available']:,.0f} available.")
    with db.connect() as con:
        cur = con.execute(
            "INSERT INTO trades (account_id, symbol, qty, entry_type, limit_price, stop, target, thesis, confidence, placed_on) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                pf["account"]["id"],
                symbol,
                int(qty),
                entry_type,
                limit_price,
                float(stop),
                target,
                thesis.strip(),
                confidence,
                _today(),
            ),
        )
        tid = cur.lastrowid
    db.touch_activity("practice")
    return {
        "id": tid,
        "symbol": symbol,
        "status": "pending",
        "message": f"Order saved. It fills at the open of the next session after {df.index[-1].strftime('%Y-%m-%d')}.",
    }


def close_trade(trade_id: int) -> dict:
    with db.connect() as con:
        t = con.execute("SELECT * FROM trades WHERE id=?", (trade_id,)).fetchone()
        if not t:
            raise PracticeError("No such trade.")
        if t["status"] == "pending":
            con.execute("UPDATE trades SET status='cancelled', exit_reason='cancelled by you' WHERE id=?", (trade_id,))
            return {"message": "Order cancelled."}
        if t["status"] != "open":
            raise PracticeError("This trade is already finished.")
        con.execute("UPDATE trades SET close_requested_on=? WHERE id=?", (_today(), trade_id))
    return {"message": "Exit requested. It fills at the next session's open."}


def _open_trade(con, trade_id: int):
    t = con.execute("SELECT * FROM trades WHERE id=?", (trade_id,)).fetchone()
    if not t:
        raise PracticeError("No such trade.")
    if t["status"] != "open":
        raise PracticeError("Only an open position can be managed. Orders still waiting to fill can be cancelled.")
    if t["close_requested_on"]:
        raise PracticeError("An exit is already requested for this position.")
    return dict(t)


def current_stop(t: dict) -> float:
    """The stop that applies now: the latest raise, or what the last settlement trailed it to."""
    moves = engine.stop_moves(t)
    return max([float(t["stop"]), t.get("current_stop") or 0.0] + [float(m["stop"]) for m in moves])


def raise_stop(trade_id: int, new_stop: float) -> dict:
    """Move an open position's stop up. It never moves down, and it applies from the next session."""
    with db.connect() as con:
        t = _open_trade(con, trade_id)
    now = current_stop(t)
    if new_stop <= now:
        raise PracticeError(f"A stop only moves up. The stop is ₹{now:.2f}; set a higher one, or leave it.")
    last = _last_closes({t["symbol"]}).get(t["symbol"], (None, None))[0]
    if last is not None and new_stop >= last:
        raise PracticeError(f"The stop must stay below the last close (₹{last:.2f}). To leave now, use Exit.")
    moves = engine.stop_moves(t) + [{"on": _today(), "stop": round(float(new_stop), 2)}]
    with db.connect() as con:
        con.execute("UPDATE trades SET stop_moves=?, current_stop=? WHERE id=?", (json.dumps(moves), new_stop, trade_id))
    return {"message": f"Stop raised to ₹{new_stop:.2f}. It applies from the next session."}


def set_trail(trade_id: int, kind: str, value: float | None) -> dict:
    """Turn a trailing stop on (a percentage or an ATR multiple below each close) or off."""
    if kind == "off":
        with db.connect() as con:
            _open_trade(con, trade_id)
            con.execute("UPDATE trades SET trail_kind=NULL, trail_value=NULL, trail_from=NULL WHERE id=?", (trade_id,))
        return {"message": "Trailing stop turned off. The stop stays where it is now."}
    limits = {"pct": TRAIL_PCT_RANGE, "atr": TRAIL_ATR_RANGE}
    if kind not in limits:
        raise PracticeError("A trailing stop is a percentage (pct) or an ATR multiple (atr).")
    low, high = limits[kind]
    if value is None or not low <= value <= high:
        unit = "%" if kind == "pct" else " x ATR"
        raise PracticeError(f"Choose a trailing distance between {low:g}{unit} and {high:g}{unit}.")
    with db.connect() as con:
        _open_trade(con, trade_id)
        con.execute("UPDATE trades SET trail_kind=?, trail_value=?, trail_from=? WHERE id=?", (kind, value, _today(), trade_id))
    what = f"{value:g}% below" if kind == "pct" else f"{value:g} x ATR below"
    return {"message": f"Trailing stop on: {what} each close, ratcheting up only, from the next session."}


def sell_part(trade_id: int, qty: int) -> dict:
    """Sell part of an open position at the next open; the rest keeps its plan."""
    with db.connect() as con:
        t = _open_trade(con, trade_id)
        if not 1 <= qty < t["qty"]:
            raise PracticeError(f"Sell between 1 and {t['qty'] - 1} shares. To sell all {t['qty']}, use Exit.")
        con.execute("UPDATE trades SET qty=? WHERE id=?", (t["qty"] - qty, trade_id))
        columns = (
            "account_id, symbol, entry_type, limit_price, stop, target, thesis, confidence, placed_on, status, "
            "entry_price, entry_date, stop_moves, current_stop, trail_kind, trail_value, trail_from"
        )
        con.execute(
            f"INSERT INTO trades ({columns}, qty, close_requested_on, parent_id) "
            f"SELECT {columns}, ?, ?, id FROM trades WHERE id=?",
            (qty, _today(), trade_id),
        )
    return {"message": f"Selling {qty} of {t['qty']} shares at the next session's open. The other {t['qty'] - qty} stay open."}


def review_trade(trade_id: int, review: str) -> dict:
    with db.connect() as con:
        con.execute("UPDATE trades SET review=? WHERE id=?", (review.strip()[:2000], trade_id))
    db.touch_activity("practice")
    return {"message": "Review saved."}


def reset_account() -> dict:
    with db.connect() as con:
        con.execute("DELETE FROM trades")
        con.execute("DELETE FROM accounts")
    account()
    return {"message": "Practice account reset to its starting points."}


# ---------------- predictions ----------------


def add_prediction(symbol: str, direction: str, horizon: str, confidence: float, reason: str) -> dict:
    symbol = clean_symbol(symbol)
    if direction not in ("up", "down"):
        raise PracticeError("Direction must be up or down.")
    if horizon not in PREDICTION_HORIZONS:
        raise PracticeError("Pick one of the listed horizons.")
    if not 0.5 <= confidence <= 0.99:
        raise PracticeError("Confidence must be between 50% and 99%. Below 50% means you expect the other direction.")
    try:
        df = market.bars(symbol, 1)
    except DataError as e:
        raise PracticeError(str(e)) from e
    ref_date, ref_close = df.index[-1].strftime("%Y-%m-%d"), float(df["close"].iloc[-1])
    with db.connect() as con:
        cur = con.execute(
            "INSERT INTO predictions (symbol, direction, horizon_days, confidence, reason, made_on, ref_date, ref_close) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (
                symbol,
                direction,
                PREDICTION_HORIZONS[horizon],
                round(confidence, 3),
                (reason or "").strip()[:1000],
                _today(),
                ref_date,
                ref_close,
            ),
        )
        pid = cur.lastrowid
    db.touch_activity("practice")
    return {
        "id": pid,
        "message": f"Logged against the close of ₹{ref_close:.2f} on {ref_date}. "
        f"It resolves after {PREDICTION_HORIZONS[horizon]} sessions.",
    }


def predictions() -> dict:
    with db.connect() as con:
        ps = db.rows(con.execute("SELECT * FROM predictions ORDER BY id DESC"))
    frames = {}
    for p in [p for p in ps if p["status"] == "open"]:
        if p["symbol"] not in frames:
            try:
                frames[p["symbol"]] = market.bars(p["symbol"], 1)
            except Exception:
                frames[p["symbol"]] = None
        df = frames[p["symbol"]]
        res = engine.resolve_prediction(p, df) if df is not None else None
        if res:
            p.update(res)
            with db.connect() as con:
                con.execute(
                    "UPDATE predictions SET status=?, outcome_date=?, outcome_close=?, correct=?, brier=?, score=? WHERE id=?",
                    (
                        res["status"],
                        res["outcome_date"],
                        res["outcome_close"],
                        res["correct"],
                        res["brier"],
                        res["score"],
                        p["id"],
                    ),
                )
    done = [p for p in ps if p["status"] == "resolved"]
    avg_brier = round(sum(p["brier"] for p in done) / len(done), 4) if done else None
    return {
        "open": [p for p in ps if p["status"] == "open"],
        "resolved": done,
        "score": sum(p["score"] for p in done),
        "avg_brier": avg_brier,
        "hit_rate": round(sum(p["correct"] for p in done) / len(done), 3) if done else None,
        "calibration": engine.calibration(done),
        "badges": badges(ps, done),
        "horizons": list(PREDICTION_HORIZONS),
        "note": "Scoring uses the Brier score: honest confidence scores best over time. A 50% call scores 0 points; "
        "a confident wrong call loses more than a confident right call gains. Points are for practice only.",
    }


def badges(ps: list[dict], done: list[dict]) -> list[dict]:
    b = []
    if ps:
        b.append({"name": "First call", "detail": "Logged your first prediction."})
    if len(done) >= 10:
        b.append({"name": "Ten resolved", "detail": "Ten predictions have played out."})
    if len(done) >= 20 and sum(p["brier"] for p in done) / len(done) < 0.2:
        b.append({"name": "Well calibrated", "detail": "Average Brier score under 0.20 across 20 or more calls."})
    if any(p["reason"] and len(p["reason"]) >= 40 for p in ps):
        b.append({"name": "Shows the working", "detail": "Wrote a real reason with a prediction."})
    return b


# ---------------- chart replay trainer ----------------


def _candles(df) -> list[dict]:
    return [
        {
            "time": ts.strftime("%Y-%m-%d"),
            "open": round(float(r["open"]), 2),
            "high": round(float(r["high"]), 2),
            "low": round(float(r["low"]), 2),
            "close": round(float(r["close"]), 2),
        }
        for ts, r in df.iterrows()
    ]


def _replay_window(symbol: str, start_date: str, end_date: str) -> list[dict]:
    df = market.lagged(market.bars(symbol, 5), EDU_LAG_DAYS)
    return _candles(df[(df.index >= start_date) & (df.index <= end_date)])


def replay_new(symbol: str | None = None, seed: int | None = None) -> dict:
    """A historical window that ends at least EDU_LAG_DAYS ago. Only the visible bars leave the server; the symbol
    and the future bars are kept in a replay session until the user decides."""
    rnd = random.Random(seed)
    for _ in range(6):
        sym = clean_symbol(symbol) if symbol else rnd.choice(ALL_SYMBOLS)
        try:
            df = market.lagged(market.bars(sym, 5), EDU_LAG_DAYS)
        except Exception:
            if symbol:
                raise PracticeError("Price history for that symbol could not be loaded.") from None
            continue
        if len(df) < REPLAY_MIN_HISTORY_BARS:
            continue
        start = rnd.randint(0, len(df) - REPLAY_WINDOW_BARS)
        candles = _candles(df.iloc[start : start + REPLAY_WINDOW_BARS])
        session_id = secrets.token_urlsafe(12)
        with db.connect() as con:
            con.execute(
                "INSERT INTO replay_sessions (id, symbol, start_date, end_date, visible) VALUES (?,?,?,?,?)",
                (session_id, sym, candles[0]["time"], candles[-1]["time"], REPLAY_VISIBLE_BARS),
            )
        return {
            "id": session_id,
            "visible": REPLAY_VISIBLE_BARS,
            "candles": candles[:REPLAY_VISIBLE_BARS],
            "note": f"A real past chart, chosen at random, ending at least {EDU_LAG_DAYS} days ago. The name is hidden "
            "until you decide, so you judge the chart and not the company.",
        }
    raise PracticeError("Could not load a practice chart right now (the price source may be offline).")


def replay_score(session_id: str, decision: str, stop: float | None, target: float | None) -> dict:
    """Score the user's plan for a replay session, then reveal the hidden bars, the company and the dates."""
    with db.connect() as con:
        row = con.execute("SELECT * FROM replay_sessions WHERE id = ?", (session_id,)).fetchone()
    if not row:
        raise PracticeError("That practice chart has expired. Start a new chart.")
    if row["scored_on"]:
        raise PracticeError("This chart was already played. Start a new chart.")
    try:
        candles = _replay_window(row["symbol"], row["start_date"], row["end_date"])
    except DataError as e:
        raise PracticeError(str(e)) from e
    if len(candles) <= row["visible"]:
        raise PracticeError("The rest of this chart could not be loaded. Start a new chart.")
    res = score_plan(candles, row["visible"], decision, stop, target)
    with db.connect() as con:
        con.execute("UPDATE replay_sessions SET scored_on = datetime('now') WHERE id = ?", (session_id,))
    replay_save(row["symbol"], row["start_date"], decision, res.get("r"), res["outcome"])
    return {
        **res,
        "symbol": row["symbol"],
        "start_date": row["start_date"],
        "end_date": row["end_date"],
        "hidden": candles[row["visible"] :],
        "stats": replay_stats(),
    }


def score_plan(candles: list[dict], visible: int, decision: str, stop: float | None, target: float | None) -> dict:
    """Play the hidden bars forward against the user's plan."""
    if decision not in ("long", "skip"):
        raise PracticeError("Decision must be long or skip.")
    future = candles[visible:]
    entry = candles[visible - 1]["close"]
    if decision == "skip":
        move = (future[-1]["close"] / entry - 1) * 100 if future else 0
        return {
            "outcome": "skipped",
            "r": None,
            "move_pct": round(move, 1),
            "text": f"You skipped. Over the next {len(future)} sessions price moved {move:+.1f}%. "
            "Skipping a chart you do not understand is a valid decision.",
        }
    if not stop or stop >= entry:
        raise PracticeError(f"Set a stop below the last close (₹{entry:.2f}).")
    for i, c in enumerate(future):
        if c["low"] <= stop:
            px = min(c["open"], stop)
            return {
                "outcome": "stop",
                "r": engine.r_multiple(entry, stop, px),
                "bars": i + 1,
                "text": f"The stop at ₹{stop:.2f} was hit after {i + 1} sessions. A planned, small loss is the system working.",
            }
        if target and c["high"] >= target:
            px = max(c["open"], target)
            return {
                "outcome": "target",
                "r": engine.r_multiple(entry, stop, px),
                "bars": i + 1,
                "text": f"The target at ₹{target:.2f} was reached after {i + 1} sessions.",
            }
    last = future[-1]["close"]
    return {
        "outcome": "open",
        "r": engine.r_multiple(entry, stop, last),
        "bars": len(future),
        "text": f"Neither stop nor target was hit in {len(future)} sessions; the trade would still be open at ₹{last:.2f}.",
    }


def replay_save(symbol: str, start_date: str, decision: str, r: float | None, outcome: str) -> None:
    with db.connect() as con:
        con.execute(
            "INSERT INTO replays (symbol, start_date, decision, r_multiple, outcome) VALUES (?,?,?,?,?)",
            (symbol, start_date, decision, r, outcome),
        )
    db.touch_activity("practice")


def replay_stats() -> dict:
    with db.connect() as con:
        rs = db.rows(con.execute("SELECT * FROM replays ORDER BY id DESC LIMIT 200"))
    taken = [r for r in rs if r["decision"] == "long" and r["r_multiple"] is not None]
    return {
        "count": len(rs),
        "taken": len(taken),
        "avg_r": round(sum(r["r_multiple"] for r in taken) / len(taken), 2) if taken else None,
        "recent": rs[:10],
    }
