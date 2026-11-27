"""Dictionary API: ranked search, an AI explanation for a missing term, and the web-search fallback.

The user's key arrives in X-AI-* headers from their own browser and is never stored. Nothing about a query leaves this
computer unless the user presses "Ask Belfort" (sent to their own AI provider) or "Search the web" (their browser).
"""

import webbrowser

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, Field

from ..core.glossary_search import MAX_QUERY, search, web_search_url
from . import chat

router = APIRouter(prefix="/api/glossary", tags=["glossary"])

PROMPT = (
    'Explain the term "{term}" in 2 to 4 plain sentences for a beginner trader in India. Say what it means in the '
    "stock market. Do not give advice about buying, selling or holding anything, and do not predict prices. If it is "
    "not a market or finance term, or you are not sure what it means, say so briefly."
)
CONTEXT = "A beginner looking up a term that is missing from Belfort's dictionary. No stock or report is open."
AI_LABEL = "AI explanation — may be wrong"


class TermIn(BaseModel):
    term: str = Field(min_length=1, max_length=MAX_QUERY)


@router.get("/search")
def api_search(q: str = "", limit: int = 20):
    results = search(q, limit=max(1, min(limit, 500)))
    return {"query": q, "count": len(results), "results": results, "web_url": web_search_url(q) if q.strip() else None}


@router.post("/ask")
def api_ask(
    body: TermIn,
    x_ai_provider: str | None = Header(default=None),
    x_ai_key: str | None = Header(default=None),
    x_ai_model: str | None = Header(default=None),
    x_ai_base: str | None = Header(default=None),
):
    term = " ".join(body.term.split())
    if not term:
        raise HTTPException(status_code=422, detail="Type a term first.")
    try:
        p = chat.Provider.resolve(x_ai_provider, x_ai_key, x_ai_model, x_ai_base)
        answer = chat.ask(PROMPT.format(term=term.replace('"', "'")), None, CONTEXT, "general", p)
    except chat.ChatError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    return {"term": term, "answer": answer, "label": AI_LABEL}


@router.post("/web-search")
def api_web_search(body: TermIn, request: Request):
    """Open the system browser on a web search. The desktop window does not open new browser windows by itself."""
    url = web_search_url(body.term)
    local = (request.client.host if request.client else "") in ("127.0.0.1", "::1", "testclient")
    opened = False
    if local:
        try:
            opened = bool(webbrowser.open(url))
        except Exception:
            opened = False
    return {"url": url, "opened": opened}
