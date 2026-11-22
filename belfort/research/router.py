"""Research vertical API: search, screens, the per-stock report, pattern reliability."""

import logging

from fastapi import APIRouter, HTTPException, Query

from ..data.providers import DataError
from . import screens
from .analysis import pipeline
from .analysis.pipeline import analyze, pattern_stats

log = logging.getLogger("belfort.research")
router = APIRouter(prefix="/api", tags=["research"])


@router.get("/search")
def api_search(q: str = Query("", max_length=60)):
    try:
        return {"results": pipeline.nse.search(q)}
    except Exception:
        return {"results": []}


@router.get("/screens")
def api_screens():
    return screens.get()


@router.get("/analyze")
def api_analyze(
    symbol: str = Query(..., max_length=60),
    style: str = "swing",
    capital: float = Query(100000, gt=0, le=1e12),
    risk_pct: float = Query(1.0, gt=0, le=100),
    stop: float | None = Query(None, gt=0),
    entry: float | None = Query(None, gt=0),
):
    try:
        return analyze(symbol, style, capital, risk_pct, stop, entry)
    except DataError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception:
        log.exception("analysis failed for %s", symbol)
        raise HTTPException(
            status_code=502,
            detail="The analysis could not be completed. The data source may be unavailable; try again in a minute.",
        ) from None


@router.get("/pattern-stats")
def api_stats():
    return pattern_stats()
