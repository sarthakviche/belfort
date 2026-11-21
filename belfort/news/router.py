"""News vertical API."""
from fastapi import APIRouter

from . import feeds

router = APIRouter(prefix="/api/news", tags=["news"])


@router.get("")
def news(refresh: bool = False):
    return feeds.get(refresh)
