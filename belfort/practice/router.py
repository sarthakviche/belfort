"""Practice vertical API: paper account, prediction journal, chart replay. Virtual points only."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from . import service
from .service import PracticeError

router = APIRouter(prefix="/api/practice", tags=["practice"])


def _guard(fn, *a, **k):
    try:
        return fn(*a, **k)
    except PracticeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


class TradeIn(BaseModel):
    symbol: str = Field(min_length=1, max_length=30)
    qty: int = Field(gt=0, le=10_000_000)
    stop: float = Field(gt=0)
    target: float | None = Field(default=None, gt=0)
    thesis: str = Field(default="", max_length=2000)
    confidence: float | None = Field(default=None, ge=0.5, le=0.99)
    entry_type: str = "market"
    limit_price: float | None = Field(default=None, gt=0)


class ReviewIn(BaseModel):
    review: str = Field(max_length=2000)


class PredictionIn(BaseModel):
    symbol: str = Field(min_length=1, max_length=30)
    direction: str
    horizon: str
    confidence: float = Field(ge=0.5, le=0.99)
    reason: str = Field(default="", max_length=1000)


class ReplayIn(BaseModel):
    symbol: str = Field(max_length=30)
    candles: list[dict] = Field(max_length=400)
    visible: int = Field(gt=1)
    decision: str
    stop: float | None = None
    target: float | None = None


@router.get("/portfolio")
def portfolio():
    return service.portfolio()


@router.post("/trades")
def place(body: TradeIn):
    from ..data.providers import DataError
    try:
        return service.place_trade(body.symbol, body.qty, body.stop, body.target, body.thesis, body.confidence,
                                   body.entry_type, body.limit_price)
    except (PracticeError, DataError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/trades/{trade_id}/close")
def close(trade_id: int):
    return _guard(service.close_trade, trade_id)


@router.post("/trades/{trade_id}/review")
def review(trade_id: int, body: ReviewIn):
    return _guard(service.review_trade, trade_id, body.review)


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
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/replay/new")
def replay_new(symbol: str | None = None):
    from ..data.providers import DataError
    try:
        return service.replay_new(symbol)
    except (PracticeError, DataError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/replay/score")
def replay_score(body: ReplayIn):
    res = _guard(service.replay_score, body.candles, body.visible, body.decision, body.stop, body.target)
    service.replay_save(body.symbol, body.candles[0]["time"], body.decision, res.get("r"), res["outcome"])
    return {**res, "stats": service.replay_stats()}


@router.get("/replay/stats")
def replay_stats():
    return service.replay_stats()
