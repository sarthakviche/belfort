"""Learn vertical API: syllabus, lessons, quizzes, progress and lagged example charts."""

from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from ..core.users import current_user_id
from ..data import market
from ..data.providers import DataError, clean_symbol
from ..settings import EDU_LAG_DAYS
from . import curriculum, game
from .curriculum import LearnError

router = APIRouter(prefix="/api/learn", tags=["learn"])


class QuizIn(BaseModel):
    answers: list[Any] = Field(max_length=50)


class CheckIn(BaseModel):
    index: int = Field(ge=0, le=200)
    answer: Any = None


class GoalIn(BaseModel):
    goal: int


def _fail(e: LearnError) -> HTTPException:
    """Locked or out of hearts: 403. Not ready yet: 409. Anything else about a missing thing: 404."""
    if isinstance(e, game.LockedError | game.NoHeartsError):
        return HTTPException(status_code=403, detail=str(e))
    if isinstance(e, game.NotReadyError):
        return HTTPException(status_code=409, detail=str(e))
    return HTTPException(status_code=404, detail=str(e))


@router.get("/syllabus")
def syllabus():
    return curriculum.progress()


@router.get("/path")
def path(request: Request):
    """The stages, nodes and the learner's XP, hearts and streak."""
    return game.path(current_user_id(request))


@router.get("/lessons/{lesson_id}")
def lesson(lesson_id: str, request: Request):
    user = current_user_id(request)
    try:
        curriculum.lesson_info(lesson_id)
        game.ensure_open(user, lesson_id)
        data = curriculum.lesson(lesson_id)
        game.ensure_can_start(user, lesson_id)
        return data
    except LearnError as e:
        raise _fail(e) from e


@router.post("/lessons/{lesson_id}/check")
def check(lesson_id: str, body: CheckIn, request: Request):
    """Grade one exercise now (a wrong answer costs a heart)."""
    try:
        return game.check_question(current_user_id(request), lesson_id, body.index, body.answer)
    except LearnError as e:
        raise _fail(e) from e


@router.post("/lessons/{lesson_id}/quiz")
def quiz(lesson_id: str, body: QuizIn, request: Request):
    try:
        return game.complete_lesson(current_user_id(request), lesson_id, body.answers)
    except LearnError as e:
        raise _fail(e) from e


@router.get("/tests/{kind}/{key}")
def start_test(kind: str, key: str, request: Request):
    """Start a checkpoint (module id), a stage test (stage) or the placement test (beginner)."""
    try:
        return game.start_test(current_user_id(request), kind, key)
    except LearnError as e:
        raise _fail(e) from e


@router.post("/sessions/{session_id}/grade")
def grade_session(session_id: str, body: QuizIn, request: Request):
    try:
        return game.grade_session(current_user_id(request), session_id, body.answers)
    except LearnError as e:
        raise _fail(e) from e


@router.get("/weak-spots")
def weak_spots(request: Request):
    return game.weak_spots(current_user_id(request))


@router.put("/goal")
def set_goal(body: GoalIn, request: Request):
    try:
        return game.set_goal(current_user_id(request), body.goal)
    except LearnError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/placement/dismiss")
def dismiss_placement(request: Request):
    game.dismiss_placement(current_user_id(request))
    return {"ok": True}


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
