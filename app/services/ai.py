import hashlib
from datetime import datetime, timezone

import httpx
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import AICache


def _cache_key(prompt: str, provider: str) -> str:
    return hashlib.sha256(f"{provider}:{prompt}".encode()).hexdigest()


def _remote_explanation(prompt: str, provider: str, key: str) -> str:
    if provider == "gemini":
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
        response = httpx.post(f"{url}?key={key}", json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=15)
        response.raise_for_status()
        return response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    if provider == "groq":
        response = httpx.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}"},
            json={"model": "llama-3.1-8b-instant", "messages": [{"role": "user", "content": prompt}], "temperature": 0},
            timeout=15,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    raise ValueError(f"Unsupported AI provider: {provider}")


def explain(prompt: str, fallback: str, session: Session) -> tuple[str, str]:
    settings = get_settings()
    provider = settings.ai_provider
    key = settings.gemini_api_key if provider == "gemini" else settings.groq_api_key
    if provider == "noop" or not key:
        return fallback, "template"
    cache_key = _cache_key(prompt, provider)
    cached = session.get(AICache, cache_key)
    if cached:
        return cached.output_text, "ai"
    try:
        output = _remote_explanation(prompt, provider, key)
        session.add(AICache(input_hash=cache_key, output_text=output, provider=provider, created_at=datetime.now(timezone.utc).replace(tzinfo=None)))
        session.commit()
        return output, "ai"
    except (httpx.HTTPError, KeyError, ValueError, TypeError):
        return fallback, "template"
