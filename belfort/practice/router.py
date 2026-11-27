"""Practice vertical API: paper account, prediction journal, chart replay. Virtual points only."""

from fastapi import APIRouter, Body, HTTPException, Query, Response
from pydantic import BaseModel, Field

from .. import settings
from ..data.providers import DataError
from . import backup, service
from .service import PracticeError

router = APIRouter(prefix="/api/practice", tags=["practice"])


def _guard(fn, *a, **k):
    try:
        return fn(*a, **k)
    except (PracticeError, DataError) as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


class TradeIn(BaseModel):
    symbol: str = Field(min_length=1, max_length=30)
    qty: int = Field(gt=0, le=10_000_000)
    stop: float | None = Field(default=None, gt=0)  # optional: no stop means the whole position is at risk
    target: float | None = Field(default=None, gt=0)
    thesis: str = Field(default="", max_length=2000)
    confidence: float | None = Field(default=None, ge=0.5, le=0.99)
    entry_type: str = "market"
    limit_price: float | None = Field(default=None, gt=0)
    setup: str | None = Field(default=None, max_length=20)


class StopIn(BaseModel):
    stop: float = Field(gt=0)


class TrailIn(BaseModel):
    kind: str = Field(pattern="^(pct|atr|off)$")
    value: float | None = Field(default=None, gt=0)


class SellIn(BaseModel):
    qty: int = Field(gt=0, le=10_000_000)


class TagsIn(BaseModel):
    setup: str | None = Field(default=None, max_length=20)
    mistakes: list[str] = Field(default_factory=list, max_length=10)


class ReviewIn(BaseModel):
    review: str = Field(max_length=2000)


class PredictionIn(BaseModel):
    symbol: str = Field(min_length=1, max_length=30)
    direction: str
    horizon: str
    confidence: float = Field(ge=0.5, le=0.99)
    reason: str = Field(default="", max_length=1000)


class ReplayIn(BaseModel):
    id: str = Field(min_length=8, max_length=40)
    decision: str
    stop: float | None = None
    target: float | None = None


@router.get("/portfolio")
def portfolio():
    return service.portfolio()


@router.get("/quote")
def quote(symbol: str = Query(min_length=1, max_length=30)):
    return _guard(service.quote, symbol)


@router.get("/size")
def size(
    symbol: str = Query(min_length=1, max_length=30),
    stop: float = Query(gt=0),
    risk_pct: float = Query(default=settings.PAPER_DEFAULT_RISK_PCT, gt=0, le=100),
    entry: float | None = Query(default=None, gt=0),
):
    return _guard(service.size, symbol, risk_pct, stop, entry)


@router.post("/trades")
def place(body: TradeIn):
    from ..data.providers import DataError

    try:
        return service.place_trade(
            body.symbol,
            body.qty,
            body.stop,
            body.target,
            body.thesis,
            body.confidence,
            body.entry_type,
            body.limit_price,
            body.setup or None,
        )
    except (PracticeError, DataError) as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/trades/{trade_id}/close")
def close(trade_id: int):
    return _guard(service.close_trade, trade_id)


@router.post("/trades/{trade_id}/stop")
def raise_stop(trade_id: int, body: StopIn):
    return _guard(service.raise_stop, trade_id, body.stop)


@router.post("/trades/{trade_id}/trail")
def trail(trade_id: int, body: TrailIn):
    return _guard(service.set_trail, trade_id, body.kind, body.value)


@router.post("/trades/{trade_id}/sell")
def sell_part(trade_id: int, body: SellIn):
    return _guard(service.sell_part, trade_id, body.qty)


@router.post("/trades/{trade_id}/tags")
def tags(trade_id: int, body: TagsIn):
    return _guard(service.tag_trade, trade_id, body.setup or None, body.mistakes)


@router.get("/equity")
def equity():
    return service.equity_curve()


@router.get("/analytics")
def journal_analytics():
    return service.journal_analytics()


@router.post("/trades/{trade_id}/review")
def review(trade_id: int, body: ReviewIn):
    return _guard(service.review_trade, trade_id, body.review)


@router.get("/export/backup.json")
def export_backup():
    import json

    return Response(
        json.dumps(backup.export_backup(), indent=1),
        media_type="application/json",
        headers={"Content-Disposition": 'attachment; filename="belfort-practice-backup.json"'},
    )


@router.get("/export/{table}.csv")
def export_csv(table: str):
    try:
        text = backup.export_csv(table)
    except backup.BackupError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return Response(text, media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="belfort-{table}.csv"'})


@router.post("/import")
def import_backup(data: dict = Body(...)):
    try:
        return backup.import_backup(data)
    except backup.BackupError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/reset")
def reset():
    return service.reset_account()


@router.get("/predictions")
def predictions():
    return service.predictions()


@router.post("/predictions")
def predict(body: PredictionIn):
    from ..data.providers import DataError

    try:
        return service.add_prediction(body.symbol, body.direction, body.horizon, body.confidence, body.reason)
    except (PracticeError, DataError) as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/replay/new")
def replay_new(symbol: str | None = None):
    from ..data.providers import DataError

    try:
        return service.replay_new(symbol)
    except (PracticeError, DataError) as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/replay/score")
def replay_score(body: ReplayIn):
    return _guard(service.replay_score, body.id, body.decision, body.stop, body.target)


@router.get("/replay/stats")
def replay_stats():
    return service.replay_stats()
