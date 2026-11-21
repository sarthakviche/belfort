"""Practice vertical: a paper account, a prediction journal and a chart-replay trainer. Virtual points only."""
import random
from datetime import date

from ..core import db
from ..data import market
from ..data.providers import DataError, clean_symbol
from ..data.universe import ALL_SYMBOLS
from ..settings import EDU_LAG_DAYS, PAPER_COST_PCT, PAPER_START_POINTS, PREDICTION_HORIZONS
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


def settle_all() -> None:
    """Replay new end-of-day bars against every pending and open trade."""
    acc = account()
    live = [t for t in _trades(acc["id"]) if t["status"] in ("pending", "open")]
    frames = {}
    for t in live:
        if t["symbol"] not in frames:
            try:
                frames[t["symbol"]] = market.bars(t["symbol"], 1)
            except Exception:
                frames[t["symbol"]] = None
        df = frames[t["symbol"]]
        if df is None:
            continue
        f = engine.settle_trade(t, df)
        if f.status != t["status"] or f.entry_price != t["entry_price"]:
            with db.connect() as con:
                con.execute("UPDATE trades SET status=?, entry_price=?, entry_date=?, exit_price=?, exit_date=?, exit_reason=? "
                            "WHERE id=?", (f.status, f.entry_price, f.entry_date, f.exit_price, f.exit_date, f.exit_reason, t["id"]))


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
            open_rows.append({**t, "last": last, "as_of": as_of, "pnl": round((last - t["entry_price"]) * t["qty"], 2),
                              "open_r": engine.r_multiple(t["entry_price"], t["stop"], last)})
        elif t["status"] == "pending":
            est = (t["limit_price"] or marks.get(t["symbol"], (0, None))[0]) * t["qty"]
            reserved += est + _cost(est)
            pending_rows.append(t)
    wins = [t for t in closed_rows if t["pnl"] > 0]
    rs = [t["r"] for t in closed_rows if t["r"] is not None]
    equity = cash + market_value
    return {
        "account": acc, "cash": round(cash, 2), "available": round(cash - reserved, 2), "reserved": round(reserved, 2),
        "invested": round(invested, 2), "market_value": round(market_value, 2), "equity": round(equity, 2),
        "return_pct": round((equity / acc["start_points"] - 1) * 100, 2),
        "open": open_rows, "pending": pending_rows, "closed": closed_rows[:50],
        "stats": {"closed": len(closed_rows), "win_rate": round(len(wins) / len(closed_rows), 3) if closed_rows else None,
                  "avg_r": round(sum(rs) / len(rs), 2) if rs else None,
                  "expectancy_note": "Average R is the average result per trade in units of the risk you took. Above 0 "
                                     "means the process made more than it lost, on these trades, after rough costs."},
        "note": "Virtual points only (1 point stands for ₹1). They have no money value and cannot be redeemed. "
                "Fills use end-of-day prices: orders fill at the next session's open.",
    }


def place_trade(symbol: str, qty: int, stop: float, target: float | None, thesis: str, confidence: float | None,
                entry_type: str = "market", limit_price: float | None = None) -> dict:
    symbol = clean_symbol(symbol)
    if qty < 1:
        raise PracticeError("Quantity must be at least 1 share.")
    if entry_type not in ("market", "limit"):
        raise PracticeError("Order type must be market or limit.")
    if entry_type == "limit" and not limit_price:
        raise PracticeError("A limit order needs a limit price.")
    if len((thesis or "").strip()) < 10:
        raise PracticeError("Write one line on why you are taking this trade (at least 10 characters). "
                            "Reviewing that reason later is most of the learning.")
    try:
        df = market.bars(symbol, 1)
    except DataError as e:
        raise PracticeError(str(e))
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
        cur = con.execute("INSERT INTO trades (account_id, symbol, qty, entry_type, limit_price, stop, target, thesis, confidence, placed_on) "
                          "VALUES (?,?,?,?,?,?,?,?,?,?)", (pf["account"]["id"], symbol, int(qty), entry_type, limit_price,
                                                           float(stop), target, thesis.strip(), confidence, _today()))
        tid = cur.lastrowid
    db.touch_activity("practice")
    return {"id": tid, "symbol": symbol, "status": "pending",
            "message": f"Order saved. It fills at the open of the next session after {df.index[-1].strftime('%Y-%m-%d')}."}


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
        raise PracticeError(str(e))
    ref_date, ref_close = df.index[-1].strftime("%Y-%m-%d"), float(df["close"].iloc[-1])
    with db.connect() as con:
        cur = con.execute("INSERT INTO predictions (symbol, direction, horizon_days, confidence, reason, made_on, ref_date, ref_close) "
                          "VALUES (?,?,?,?,?,?,?,?)", (symbol, direction, PREDICTION_HORIZONS[horizon], round(confidence, 3),
                                                       (reason or "").strip()[:1000], _today(), ref_date, ref_close))
        pid = cur.lastrowid
    db.touch_activity("practice")
    return {"id": pid, "message": f"Logged against the close of ₹{ref_close:.2f} on {ref_date}. "
                                  f"It resolves after {PREDICTION_HORIZONS[horizon]} sessions."}


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
                con.execute("UPDATE predictions SET status=?, outcome_date=?, outcome_close=?, correct=?, brier=?, score=? WHERE id=?",
                            (res["status"], res["outcome_date"], res["outcome_close"], res["correct"], res["brier"], res["score"], p["id"]))
    done = [p for p in ps if p["status"] == "resolved"]
    avg_brier = round(sum(p["brier"] for p in done) / len(done), 4) if done else None
    return {
        "open": [p for p in ps if p["status"] == "open"], "resolved": done,
        "score": sum(p["score"] for p in done), "avg_brier": avg_brier,
        "hit_rate": round(sum(p["correct"] for p in done) / len(done), 3) if done else None,
        "calibration": engine.calibration(done), "badges": badges(ps, done),
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

def replay_new(symbol: str | None = None, seed: int | None = None) -> dict:
    """A historical window that ends at least EDU_LAG_DAYS ago. The page hides the symbol and the future bars until
    the user decides; they travel with the response because this is a local practice tool, not a contest."""
    rnd = random.Random(seed)
    for _ in range(6):
        sym = clean_symbol(symbol) if symbol else rnd.choice(ALL_SYMBOLS)
        try:
            df = market.lagged(market.bars(sym, 5), EDU_LAG_DAYS)
        except Exception:
            if symbol:
                raise PracticeError("Price history for that symbol could not be loaded.")
            continue
        if len(df) < 260:
            continue
        start = rnd.randint(0, len(df) - 200)
        win = df.iloc[start:start + 200]
        candles = [{"time": ts.strftime("%Y-%m-%d"), "open": round(float(r["open"]), 2), "high": round(float(r["high"]), 2),
                    "low": round(float(r["low"]), 2), "close": round(float(r["close"]), 2)} for ts, r in win.iterrows()]
        return {"symbol": sym, "visible": 140, "candles": candles,
                "note": f"A real past chart, chosen at random, ending at least {EDU_LAG_DAYS} days ago. The name is hidden "
                        "until you decide, so you judge the chart and not the company."}
    raise PracticeError("Could not load a practice chart right now (the price source may be offline).")


def replay_score(candles: list[dict], visible: int, decision: str, stop: float | None, target: float | None) -> dict:
    """Play the hidden bars forward against the user's plan."""
    if decision not in ("long", "skip"):
        raise PracticeError("Decision must be long or skip.")
    future = candles[visible:]
    entry = candles[visible - 1]["close"]
    if decision == "skip":
        move = (future[-1]["close"] / entry - 1) * 100 if future else 0
        return {"outcome": "skipped", "r": None, "move_pct": round(move, 1),
                "text": f"You skipped. Over the next {len(future)} sessions price moved {move:+.1f}%. "
                        "Skipping a chart you do not understand is a valid decision."}
    if not stop or stop >= entry:
        raise PracticeError(f"Set a stop below the last close (₹{entry:.2f}).")
    for i, c in enumerate(future):
        if c["low"] <= stop:
            px = min(c["open"], stop)
            return {"outcome": "stop", "r": engine.r_multiple(entry, stop, px), "bars": i + 1,
                    "text": f"The stop at ₹{stop:.2f} was hit after {i + 1} sessions. A planned, small loss is the system working."}
        if target and c["high"] >= target:
            px = max(c["open"], target)
            return {"outcome": "target", "r": engine.r_multiple(entry, stop, px), "bars": i + 1,
                    "text": f"The target at ₹{target:.2f} was reached after {i + 1} sessions."}
    last = future[-1]["close"]
    return {"outcome": "open", "r": engine.r_multiple(entry, stop, last), "bars": len(future),
            "text": f"Neither stop nor target was hit in {len(future)} sessions; the trade would still be open at ₹{last:.2f}."}


def replay_save(symbol: str, start_date: str, decision: str, r: float | None, outcome: str) -> None:
    with db.connect() as con:
        con.execute("INSERT INTO replays (symbol, start_date, decision, r_multiple, outcome) VALUES (?,?,?,?,?)",
                    (symbol, start_date, decision, r, outcome))
    db.touch_activity("practice")


def replay_stats() -> dict:
    with db.connect() as con:
        rs = db.rows(con.execute("SELECT * FROM replays ORDER BY id DESC LIMIT 200"))
    taken = [r for r in rs if r["decision"] == "long" and r["r_multiple"] is not None]
    return {"count": len(rs), "taken": len(taken),
            "avg_r": round(sum(r["r_multiple"] for r in taken) / len(taken), 2) if taken else None,
            "recent": rs[:10]}

