"""Assistant API. The user's key arrives in X-AI-* headers from their own browser and is never stored."""
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from . import chat

router = APIRouter(prefix="/api", tags=["assistant"])


class ChatIn(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    history: list[dict] = Field(default_factory=list, max_length=12)
    context: str = Field(default="", max_length=8000)
    mode: str = Field(default="report", max_length=20)


@router.post("/chat")
def api_chat(body: ChatIn, x_ai_provider: str | None = Header(default=None), x_ai_key: str | None = Header(default=None),
             x_ai_model: str | None = Header(default=None), x_ai_base: str | None = Header(default=None)):
    try:
        p = chat.Provider.resolve(x_ai_provider, x_ai_key, x_ai_model, x_ai_base)
        return {"answer": chat.ask(body.question, body.history, body.context, body.mode, p)}
    except chat.ChatError as e:
        raise HTTPException(status_code=503, detail=str(e))
