"""Chat service — streaming SSE, 10-message limit per session."""

import asyncio
import json
import queue
import threading
from typing import AsyncGenerator, Optional

import anthropic
import redis as redis_lib
from loguru import logger

from app.core.config import settings

_CLIENT = anthropic.Anthropic(api_key=settings.anthropic_api_key)

_MAX_MESSAGES = 10
_MAX_TOKENS = 600

_SYSTEM_PROMPT = """You are dsbuddy — a sharp, friendly data science assistant. The user has just run an automated analysis on their dataset and can see the results on screen. Your job is to answer their follow-up questions.

Rules you must follow without exception:
- Write in plain conversational prose. Never use markdown headers (##, ###), never use asterisks for bold or bullets, never use hashtags.
- If you need to list things, write them out naturally: "There are three issues: first... second... third..."
- Only say things you can support from the context provided. If the answer is not in the context, say "I don't see that in the analysis" rather than guessing.
- Be direct and human. One or two clear sentences is almost always better than a long explanation.
- Do not repeat the user's question back to them.
- Do not start with filler phrases like "Great question!" or "Certainly!"."""


# ---------------------------------------------------------------------------
# Redis helpers
# ---------------------------------------------------------------------------

def _get_redis() -> Optional[redis_lib.Redis]:
    try:
        r = redis_lib.from_url(settings.redis_url, socket_connect_timeout=1)
        r.ping()
        return r
    except (redis_lib.RedisError, OSError):
        return None


_IN_MEMORY_STORE: dict[str, int] = {}


def _get_message_count(session_id: str) -> int:
    r = _get_redis()
    if r is not None:
        try:
            val = r.get(f"chat:count:{session_id}")
            return int(val) if val else 0
        except redis_lib.RedisError:
            pass
    return _IN_MEMORY_STORE.get(session_id, 0)


def _increment_message_count(session_id: str) -> int:
    r = _get_redis()
    if r is not None:
        try:
            key = f"chat:count:{session_id}"
            new_count = r.incr(key)
            r.expire(key, 3600)
            return int(new_count)
        except redis_lib.RedisError:
            pass
    count = _IN_MEMORY_STORE.get(session_id, 0) + 1
    _IN_MEMORY_STORE[session_id] = count
    return count


# ---------------------------------------------------------------------------
# Streaming entry point
# ---------------------------------------------------------------------------

async def chat_stream(
    session_id: str,
    question: str,
    context_summary: str,
    context_insights: Optional[str],
) -> AsyncGenerator[str, None]:
    """Async generator yielding SSE-formatted strings."""
    used = await asyncio.to_thread(_get_message_count, session_id)
    if used >= _MAX_MESSAGES:
        yield f'data: {{"type":"error","message":"You have used all {_MAX_MESSAGES} messages for this session."}}\n\n'
        return

    user_content = _build_user_content(question, context_summary, context_insights)

    # Run the blocking Anthropic stream in a thread, feed chunks to a queue
    q: queue.Queue[str | None] = queue.Queue()

    def _run_stream() -> None:
        try:
            with _CLIENT.messages.stream(
                model=settings.llm_class,
                max_tokens=_MAX_TOKENS,
                temperature=0,
                system=[
                    {
                        "type": "text",
                        "text": _SYSTEM_PROMPT,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                messages=[{"role": "user", "content": user_content}],
            ) as stream:
                for text in stream.text_stream:
                    q.put(f'data: {{"type":"delta","text":{json.dumps(text)}}}\n\n')

            new_count = _increment_message_count(session_id)
            remaining = max(0, _MAX_MESSAGES - new_count)
            q.put(f'data: {{"type":"done","remaining":{remaining}}}\n\n')
        except Exception as exc:
            logger.error("Chat stream error", error=str(exc))
            q.put(f'data: {{"type":"error","message":{json.dumps(str(exc))}}}\n\n')
        finally:
            q.put(None)  # sentinel

    thread = threading.Thread(target=_run_stream, daemon=True)
    thread.start()

    loop = asyncio.get_event_loop()
    while True:
        chunk = await loop.run_in_executor(None, q.get)
        if chunk is None:
            break
        yield chunk

    await asyncio.to_thread(thread.join)
    logger.info("Chat stream complete", session_id=session_id)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_user_content(
    question: str,
    context_summary: str,
    context_insights: Optional[str],
) -> list[dict]:
    context_parts: list[str] = []
    if context_summary:
        context_parts.append(f"Dataset analysis context:\n{context_summary}")
    if context_insights:
        context_parts.append(f"Detailed insights (JSON):\n{context_insights}")

    if context_parts:
        return [
            {
                "type": "text",
                "text": "\n\n".join(context_parts),
                "cache_control": {"type": "ephemeral"},
            },
            {
                "type": "text",
                "text": question,
            },
        ]
    return [{"type": "text", "text": question}]
