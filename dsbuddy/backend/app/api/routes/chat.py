"""POST /chat/stream — streaming SSE chat about an analysed dataset."""

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from loguru import logger

from app.models.requests import ChatRequest
from app.services import chat_client

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/stream")
async def chat_stream(request: ChatRequest) -> StreamingResponse:
    """Stream an AI response about the dataset, one token at a time.

    SSE event types:
      {"type": "delta", "text": "..."}   — text chunk
      {"type": "done", "remaining": N}   — stream finished, N messages left
      {"type": "error", "message": "..."} — error
    """
    logger.info("Chat stream request", session_id=request.session_id)

    return StreamingResponse(
        chat_client.chat_stream(
            session_id=request.session_id,
            question=request.question,
            context_summary=request.context_summary,
            context_insights=request.context_insights,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
