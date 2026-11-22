"""Learn vertical API: syllabus, lessons, quizzes, progress and lagged example charts."""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..data import market
from ..data.providers import DataError, clean_symbol
from ..settings import EDU_LAG_DAYS
from . import curriculum
from .curriculum import LearnError

router = APIRouter(prefix="/api/learn", tags=["learn"])


class QuizIn(BaseModel):
    answers: list[int] = Field(max_length=50)


@router.get("/syllabus")
def syllabus():
    return curriculum.progress()


@router.get("/lessons/{lesson_id}")
def lesson(lesson_id: str):
    try:
        return curriculum.lesson(lesson_id)
    except LearnError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.post("/lessons/{lesson_id}/quiz")
def quiz(lesson_id: str, body: QuizIn):
    try:
        return curriculum.grade(lesson_id, body.answers)
    except LearnError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/example")
def example(symbol: str = Query(..., max_length=30), bars: int = Query(120, ge=20, le=400)):
    """Daily candles for a lesson. They always end at least EDU_LAG_DAYS ago."""
    try:
        sym = clean_symbol(symbol)
        df = market.lagged(market.bars(sym, 3), EDU_LAG_DAYS).iloc[-bars:]
    except DataError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception:
        raise HTTPException(status_code=502, detail="Example prices could not be loaded.") from None
    if df.empty:
        raise HTTPException(status_code=404, detail="No example prices old enough for a lesson.")
    return {
        "symbol": sym,
        "lag_days": EDU_LAG_DAYS,
        "ends": df.index[-1].strftime("%Y-%m-%d"),
        "candles": [
            {
                "time": ts.strftime("%Y-%m-%d"),
                "open": round(float(r["open"]), 2),
                "high": round(float(r["high"]), 2),
                "low": round(float(r["low"]), 2),
                "close": round(float(r["close"]), 2),
            }
            for ts, r in df.iterrows()
        ],
        "note": f"Past prices for learning only, ending at least {EDU_LAG_DAYS} days ago. Not a view on this stock today.",
    }
