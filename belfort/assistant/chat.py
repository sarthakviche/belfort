"""Ask Belfort: an explainer chat. Bring your own key.

Two provider shapes cover most services:
  gemini  - Google AI Studio (generativelanguage.googleapis.com)
  openai  - any OpenAI-compatible chat endpoint: OpenAI, OpenRouter, Groq, Together, or a local Ollama / LM Studio

The key travels from the user's browser to this local server with each request (or comes from .env) and is
forwarded only to the provider the user chose. Belfort never stores it on disk and has no server of its own.
"""

import os
from dataclasses import dataclass

import httpx

from .. import settings
from ..core.compliance import find_banned

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
DEFAULTS = {"gemini": ("gemini-flash-latest", ""), "openai": ("gpt-4o-mini", "https://api.openai.com/v1")}

SYSTEM = """You are the helper inside Belfort, a free learning and research app for Indian (NSE) retail traders, many of
them beginners. Explain terms, charts, company figures, news stories, lessons and the app's own report in short, plain
sentences. Define any jargon you use.
Rules you must follow:
- Never tell the user to buy, sell or hold any stock, and never give price targets or predictions of your own.
- Never promise or imply returns. Markets are uncertain; say so when relevant.
- If asked "should I buy", explain what the report's label and checks mean and what the user would need to decide for
  themselves (position size, stop-loss, how much they can afford to lose). The decision is theirs.
- For facts about a stock, story or lesson, use only the context provided. If a figure is not there, say you do not
  have it. Do not invent numbers.
- When explaining news, say what happened, why it may matter for a beginner, and which terms mean what. Do not say how
  the stock "will" react.
- You are not a SEBI-registered adviser. Keep answers under about 150 words unless asked for more detail."""

MODES = {
    "report": "Report currently on the user's screen",
    "news": "News story the user is reading (headline and the publisher's short description only)",
    "lesson": "Lesson the user is studying",
    "general": "Context",
}


class ChatError(Exception):
    pass


@dataclass
class Provider:
    kind: str
    key: str
    model: str
    base: str

    @classmethod
    def resolve(cls, kind: str | None = None, key: str | None = None, model: str | None = None, base: str | None = None):
        kind = (kind or os.environ.get("AI_PROVIDER") or ("gemini" if os.environ.get("GEMINI_API_KEY") else "openai")).lower()
        if kind not in DEFAULTS:
            raise ChatError("Unknown AI provider. Choose gemini or openai (any OpenAI-compatible service).")
        env_key = os.environ.get("GEMINI_API_KEY") if kind == "gemini" else os.environ.get("OPENAI_API_KEY")
        dm, dbase = DEFAULTS[kind]
        p = cls(
            kind,
            (key or env_key or "").strip(),
            (model or os.environ.get("AI_MODEL") or dm).strip(),
            (base or os.environ.get("OPENAI_BASE_URL") or dbase).strip().rstrip("/"),
        )
        local = p.kind == "openai" and ("localhost" in p.base or "127.0.0.1" in p.base)
        if not p.key and not local:
            raise ChatError(
                "Ask Belfort needs your own AI key. Open Settings, choose a provider and paste a key. "
                "Gemini keys are free from Google AI Studio; a local Ollama needs no key."
            )
        return p


def configured() -> bool:
    return bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("OPENAI_API_KEY"))


def _turns(history: list[dict] | None) -> list[tuple[str, str]]:
    out = []
    for turn in (history or [])[-6:]:
        text = str(turn.get("text", ""))[:2000]
        if text:
            out.append(("assistant" if turn.get("role") in ("model", "assistant") else "user", text))
    return out


def _redact(text: str, key: str) -> str:
    """Remove the user's key from a provider's error text."""
    if key:
        text = text.replace(key, "[your key]")
    return text


def _http_error(p: Provider, status: int, provider_msg: str) -> ChatError:
    """Turn a provider's HTTP error into a sentence that tells the user what to do next."""
    name = "Gemini" if p.kind == "gemini" else "The AI service"
    lowered = provider_msg.lower()
    if status in (401, 403) or (status == 400 and ("api key" in lowered or "api_key" in lowered)):
        hint = " Gemini keys are free from Google AI Studio." if p.kind == "gemini" else ""
        return ChatError(f"{name} did not accept your key. Open Settings, check the provider and paste the key again.{hint}")
    if status == 404:
        return ChatError(f'The model "{p.model}" was not found at this provider. Open Settings and check the model name.')
    if status == 429:
        return ChatError(
            f"{name} says you have reached its rate or quota limit. Wait a minute and try again, or check your plan with the provider."
        )
    if status >= 500:
        return ChatError(f"{name} is having trouble right now (error {status}). Try again in a few minutes.")
    detail = _redact(provider_msg, p.key)[: settings.AI_ERROR_DETAIL_CHARS]
    return ChatError(f"{name} returned an error ({status}). {detail}".strip())


def _call(p: Provider, turns: list[tuple[str, str]]) -> str:
    timeout = settings.AI_TIMEOUT_SECONDS[p.kind]
    local = p.kind == "openai" and ("localhost" in p.base or "127.0.0.1" in p.base)
    try:
        if p.kind == "gemini":
            body = {
                "system_instruction": {"parts": [{"text": SYSTEM}]},
                "contents": [{"role": "model" if r == "assistant" else "user", "parts": [{"text": t}]} for r, t in turns],
                "generationConfig": {"temperature": 0.3, "maxOutputTokens": settings.AI_MAX_OUTPUT_TOKENS},
            }
            r = httpx.post(GEMINI_URL.format(model=p.model), headers={"x-goog-api-key": p.key}, json=body, timeout=timeout)
        else:
            body = {
                "model": p.model,
                "temperature": 0.3,
                "max_tokens": settings.AI_MAX_OUTPUT_TOKENS,
                "messages": [{"role": "system", "content": SYSTEM}] + [{"role": r, "content": t} for r, t in turns],
            }
            headers = {"Authorization": f"Bearer {p.key}"} if p.key else {}
            r = httpx.post(p.base + "/chat/completions", headers=headers, json=body, timeout=timeout)
    except httpx.TimeoutException:
        raise ChatError("The AI service took too long to answer. Try again, or choose a faster model in Settings.") from None
    except httpx.HTTPError:
        if local:
            raise ChatError(
                f"Could not reach your local model at {p.base}. Start Ollama (or LM Studio) and check the address in Settings."
            ) from None
        raise ChatError("Could not reach the AI service. Check your internet connection and try again.") from None
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
            answer = "".join(x.get("text", "") for x in data["candidates"][0]["content"]["parts"]).strip()
        else:
            answer = (data["choices"][0]["message"]["content"] or "").strip()
    except (KeyError, IndexError, TypeError, ValueError):
        answer = ""
    if not answer:
        raise ChatError("The AI service gave no answer to that question. Try rephrasing it.")
    return answer


def ask(
    question: str, history: list[dict] | None = None, context: str = "", mode: str = "report", provider: Provider | None = None
) -> str:
    p = provider or Provider.resolve()
    prompt = question.strip()[:2000]
    if context:
        prompt = f"{MODES.get(mode, MODES['general'])}:\n{context[:6000]}\n\nUser question: {prompt}"
    answer = _call(p, _turns(history) + [("user", prompt)])
    if find_banned(answer):
        return (
            "I can't answer that the way it came out, because the reply used promise-style wording Belfort does not "
            "allow. I can explain what the label, the checks or any term on the screen mean."
        )
    return answer
