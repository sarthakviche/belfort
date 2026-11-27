"""Read the text of a screenshot with the user's own AI key (Tip Check, T44).

Same providers and key handling as chat.py: the key comes from the user's browser with the request (or from .env),
goes only to the provider they chose, and is never stored. The model only transcribes; Tip Check's rules do the
checking. Its output is the tip's own words, so it is not run through the banned-wording filter: those words are
shown back to the user as quoted evidence, never as Belfort's wording.
"""

import base64
import binascii
import re

import httpx

from .. import settings
from .chat import GEMINI_URL, ChatError, Provider, _http_error

PROMPT = (
    "This is a screenshot of a message from WhatsApp, Telegram, Instagram or a similar app. Copy out all of its text "
    "exactly as written, in its original language and script: the sender's name or number, the group name, every "
    "message, numbers, prices, registration numbers and links. Keep line breaks. Do not translate, summarise, explain "
    "or add anything. If there is no text, reply with nothing."
)
IMAGE_TYPES = {"image/png", "image/jpeg", "image/webp"}
DATA_URL_RE = re.compile(r"^data:(image/[a-z]+);base64,(.+)$", re.DOTALL)


class ImageError(ValueError):
    pass


def decode(data_url: str) -> tuple[str, bytes]:
    """(mime type, bytes) from a browser data URL, checking the type and size."""
    m = DATA_URL_RE.match((data_url or "").strip())
    if not m or m.group(1) not in IMAGE_TYPES:
        raise ImageError("type")
    try:
        raw = base64.b64decode(m.group(2), validate=True)
    except (binascii.Error, ValueError):
        raise ImageError("type") from None
    if len(raw) > settings.TIP_IMAGE_MAX_BYTES:
        raise ImageError("size")
    return m.group(1), raw


def read_text(mime: str, image: bytes, p: Provider) -> str:
    """The text in the image, as the provider read it. Raises ChatError with a sentence for the user."""
    b64 = base64.b64encode(image).decode()
    timeout = settings.AI_TIMEOUT_SECONDS[p.kind]
    try:
        if p.kind == "gemini":
            body = {
                "contents": [{"role": "user", "parts": [{"inline_data": {"mime_type": mime, "data": b64}}, {"text": PROMPT}]}],
                "generationConfig": {"temperature": 0, "maxOutputTokens": settings.AI_MAX_OUTPUT_TOKENS * 2},
            }
            r = httpx.post(GEMINI_URL.format(model=p.model), headers={"x-goog-api-key": p.key}, json=body, timeout=timeout)
        else:
            body = {
                "model": p.model,
                "temperature": 0,
                "max_tokens": settings.AI_MAX_OUTPUT_TOKENS * 2,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": PROMPT},
                            {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
                        ],
                    }
                ],
            }
            headers = {"Authorization": f"Bearer {p.key}"} if p.key else {}
            r = httpx.post(p.base + "/chat/completions", headers=headers, json=body, timeout=timeout)
    except httpx.TimeoutException:
        raise ChatError("The AI service took too long to read the image. Try again, or paste the text instead.") from None
    except httpx.HTTPError:
        raise ChatError("Could not reach the AI service. Check your connection, or paste the text instead.") from None
    if r.status_code != 200:
        try:
            err = r.json().get("error", {})
            msg = err.get("message", "") if isinstance(err, dict) else str(err)
        except Exception:
            msg = ""
        raise _http_error(p, r.status_code, msg)
    try:
        data = r.json()
        if p.kind == "gemini":
            text = "".join(x.get("text", "") for x in data["candidates"][0]["content"]["parts"])
        else:
            text = data["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, TypeError, ValueError):
        text = ""
    return text.strip()[: settings.TIP_MAX_CHARS]
