from fastapi import APIRouter

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat import answer_chat
from app.config import get_settings

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    history = [item.model_dump() for item in payload.history]
    reply, source = answer_chat(payload.message, history)
    return ChatResponse(
        reply=reply,
        source=source,
        provider=get_settings().ai_provider if source == "ai" else "template",
    )
