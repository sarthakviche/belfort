"""Belfort: one local app with four verticals (Research, Learn, Practice, News) and a bring-your-own-key assistant.

Run:  python -m uvicorn belfort.main:app --port 8765
The server binds to your own machine. Set ACCESS_CODES only if you knowingly share it on a private network;
Belfort is not designed to be run as a public service (see docs/COMPLIANCE.md).
"""

import os
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.staticfiles import StaticFiles

from .assistant import chat
from .assistant.router import router as assistant_router
from .core.compliance import AI_NOTICE, DISCLAIMER
from .core.glossary import GLOSSARY
from .data.universe import UNIVERSE
from .learn.router import router as learn_router
from .news.router import router as news_router
from .practice.router import router as practice_router
from .research.router import router as research_router
from .settings import EDU_LAG_DAYS, PAPER_START_POINTS, PREDICTION_HORIZONS, STYLES, VERSION


def _codes() -> set[str]:
    return {c.strip() for c in os.environ.get("ACCESS_CODES", "").split(",") if c.strip()}


def require_access(x_access_code: str | None = Header(default=None)):
    codes = _codes()
    if codes and x_access_code not in codes:
        raise HTTPException(status_code=401, detail="A valid access code is required.")


app = FastAPI(title="Belfort", version=VERSION, docs_url="/api/docs", redoc_url=None)


@app.get("/api/config")
def config():
    return {
        "version": VERSION,
        "requires_code": bool(_codes()),
        "disclaimer": DISCLAIMER,
        "ai_notice": AI_NOTICE,
        "styles": [{"key": s.key, "name": s.name, "holds": s.holds} for s in STYLES.values()],
        "universe": UNIVERSE,
        "glossary": GLOSSARY,
        "chat_env_ready": chat.configured(),
        "practice": {"start_points": PAPER_START_POINTS, "horizons": list(PREDICTION_HORIZONS)},
        "edu_lag_days": EDU_LAG_DAYS,
    }


for r in (research_router, learn_router, practice_router, news_router, assistant_router):
    app.include_router(r, dependencies=[Depends(require_access)])

app.mount("/", StaticFiles(directory=Path(__file__).parent / "static", html=True), name="static")
