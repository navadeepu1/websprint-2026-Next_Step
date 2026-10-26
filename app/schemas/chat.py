from typing import Literal

from pydantic import Field

from app.schemas.common import APIModel


class ChatMessageIn(APIModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1, max_length=1200)


class ChatRequest(APIModel):
    message: str = Field(..., min_length=1, max_length=1200)
    history: list[ChatMessageIn] = Field(default_factory=list, max_length=8)


class ChatResponse(APIModel):
    reply: str
    source: Literal["ai", "template"]
    provider: str
