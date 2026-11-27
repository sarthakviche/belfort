"""News vertical API."""

from fastapi import APIRouter

from . import feeds

router = APIRouter(prefix="/api/news", tags=["news"])


@router.get("")
def news(refresh: bool = False):
    data = feeds.get(refresh)
    syms = [sym for story in data["stories"] for sym in story.get("symbols", [])]
    return {**data, "companies": feeds.companies(syms)}
