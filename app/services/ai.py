import hashlib
from datetime import datetime, timezone
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import AICache


def _cache_key(prompt: str, provider: str, model: str) -> str:
    return hashlib.sha256(f"{provider}:{model}:{prompt}".encode("utf-8")).hexdigest()


def _clean_output(output: Any) -> str:
    if not isinstance(output, str):
        raise ValueError("AI provider returned a non-text response.")
    cleaned = output.strip()
    if not cleaned or len(cleaned) > 20_000:
        raise ValueError("AI provider returned an empty or oversized response.")
    return cleaned


def _remote_explanation(prompt: str, provider: str, key: str) -> str:
    settings = get_settings()
    if provider == "gemini":
        response = httpx.post(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent",
            params={"key": key},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": settings.ai_temperature,
                    "maxOutputTokens": settings.ai_max_tokens,
                },
            },
            timeout=settings.ai_timeout_seconds,
        )
        response.raise_for_status()
        return _clean_output(response.json()["candidates"][0]["content"]["parts"][0]["text"])
    if provider == "groq":
        response = httpx.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.groq_model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Rewrite only the supplied text. Never invent eligibility rules, "
                            "documents, links, guarantees, diagnoses, or treatment advice."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": settings.ai_temperature,
                "max_tokens": settings.ai_max_tokens,
            },
            timeout=settings.ai_timeout_seconds,
        )
        response.raise_for_status()
        return _clean_output(response.json()["choices"][0]["message"]["content"])
    raise ValueError(f"Unsupported AI provider: {provider}")


def provider_status() -> dict[str, str | bool | int]:
    settings = get_settings()
    key = settings.gemini_api_key if settings.ai_provider == "gemini" else settings.groq_api_key
    configured = settings.ai_provider == "noop" or bool(key)
    model = (
        settings.groq_model
        if settings.ai_provider == "groq"
        else "gemini-1.5-flash"
        if settings.ai_provider == "gemini"
        else "template"
    )
    return {
        "provider": settings.ai_provider,
        "configured": configured,
        "model": model,
        "cache_ttl_seconds": settings.ai_cache_ttl_seconds,
    }


def explain(prompt: str, fallback: str, session: Session) -> tuple[str, str]:
    settings = get_settings()
    provider = settings.ai_provider
    key = settings.gemini_api_key if provider == "gemini" else settings.groq_api_key
    model = settings.groq_model if provider == "groq" else "gemini-1.5-flash"
    if provider == "noop" or not key:
        return fallback, "template"

    cache_key = _cache_key(prompt, provider, model)
    cached = session.get(AICache, cache_key)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if cached and (
        settings.ai_cache_ttl_seconds == 0
        or (now - cached.created_at).total_seconds() <= settings.ai_cache_ttl_seconds
    ):
        return cached.output_text, "ai"

    try:
        output = _remote_explanation(prompt, provider, key)
        session.add(
            AICache(
                input_hash=cache_key,
                output_text=output,
                provider=provider,
                created_at=now,
            )
        )
        session.commit()
        return output, "ai"
    except (httpx.HTTPError, KeyError, ValueError, TypeError):
        session.rollback()
        return fallback, "template"
