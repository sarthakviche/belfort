"""Tip Check API. Text is checked offline by rules; a screenshot is read, and the web searched (Gemini only), with the
user's own AI key (X-AI-* headers)."""

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from .. import settings
from ..assistant import chat, vision
from . import service, webcheck
from .strings import t

router = APIRouter(prefix="/api/tipcheck", tags=["tipcheck"])


class TipIn(BaseModel):
    text: str = Field(min_length=1, max_length=settings.TIP_MAX_CHARS * 2)
    symbol: str | None = Field(default=None, max_length=20)


class ImageIn(BaseModel):
    image: str = Field(min_length=20, max_length=settings.TIP_IMAGE_MAX_BYTES * 2)


@router.post("")
def check(body: TipIn):
    try:
        return service.check(body.text, body.symbol)
    except service.TipError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/image")
def read_image(
    body: ImageIn,
    x_ai_provider: str | None = Header(default=None),
    x_ai_key: str | None = Header(default=None),
    x_ai_model: str | None = Header(default=None),
    x_ai_base: str | None = Header(default=None),
):
    """The text in a screenshot, for the user to see and check before the rules run on it."""
    try:
        mime, raw = vision.decode(body.image)
    except vision.ImageError as e:
        raise HTTPException(status_code=400, detail=t("error.image_size" if str(e) == "size" else "error.image_type")) from e
    try:
        p = chat.Provider.resolve(x_ai_provider, x_ai_key, x_ai_model, x_ai_base)
        text = vision.read_text(mime, raw, p)
    except chat.ChatError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    if not text:
        raise HTTPException(status_code=422, detail=t("error.image_empty"))
    return {"text": text}


@router.post("/web")
def web_check(
    body: TipIn,
    x_ai_provider: str | None = Header(default=None),
    x_ai_key: str | None = Header(default=None),
    x_ai_model: str | None = Header(default=None),
    x_ai_base: str | None = Header(default=None),
):
    """What the web says about the tip: Gemini searches Google with the user's own key. The rules still set the flags."""
    symbol = (body.symbol or "").strip().upper() or None
    name = dict(service.companies()).get(symbol) if symbol else None
    try:
        p = chat.Provider.resolve(x_ai_provider, x_ai_key, x_ai_model, x_ai_base)
        return webcheck.check(body.text, symbol, name, p)
    except webcheck.WebCheckError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except chat.ChatError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
