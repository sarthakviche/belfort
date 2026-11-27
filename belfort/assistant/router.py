"""Assistant API. The user's key arrives in X-AI-* headers from their own browser and is never stored."""

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from ..core import i18n
from . import chat

router = APIRouter(prefix="/api", tags=["assistant"])


class ChatIn(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    history: list[dict] = Field(default_factory=list, max_length=12)
    context: str = Field(default="", max_length=8000)
    mode: str = Field(default="report", max_length=20)


@router.post("/chat")
def api_chat(
    body: ChatIn,
    x_ai_provider: str | None = Header(default=None),
    x_ai_key: str | None = Header(default=None),
    x_ai_model: str | None = Header(default=None),
    x_ai_base: str | None = Header(default=None),
):
    try:
        p = chat.Provider.resolve(x_ai_provider, x_ai_key, x_ai_model, x_ai_base)
        question = body.question
        reply = i18n.reply_instruction(i18n.current())  # answers come in the language chosen in the app
        if reply:
            question = question[:1900] + "\n\n" + reply
        answer = chat.ask(question, body.history, body.context, body.mode, p)
        if i18n.find_banned(answer, i18n.current()):  # banned promise-style wording in the chosen language
            answer = i18n.tr(i18n.current(), "chat.blocked")
        return {"answer": answer}
    except chat.ChatError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
