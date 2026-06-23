import json
import logging
from typing import Any, Generator

from openai import OpenAI

from app.config import settings

logger = logging.getLogger(__name__)

_client = OpenAI(api_key=settings.openai_api_key)


def chat(system_prompt: str, user_prompt: str, temperature: float = 0.7) -> str:
    """
    Single entry point for all plain-text GPT responses.
    Used for summaries, feedback, and any free-form text generation.
    """
    response = _client.chat.completions.create(
        model=settings.model_name,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.choices[0].message.content.strip()


def chat_stream(system_prompt: str, user_prompt: str, temperature: float = 0.7) -> Generator[str, None, None]:
    """
    Streams plain-text GPT responses token by token.
    Used for summary and interview feedback streaming endpoints.
    """
    stream = _client.chat.completions.create(
        model=settings.model_name,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        stream=True,
    )
    for chunk in stream:
        token = chunk.choices[0].delta.content
        if token:
            yield token


def chat_json(system_prompt: str, user_prompt: str, temperature: float = 0.3) -> Any:
    """
    Single entry point for all structured JSON GPT responses.
    Used for quizzes, flashcards, interview questions, and evaluation scores.
    Lower temperature (0.3) keeps JSON output deterministic.
    Raises ValueError if GPT returns invalid JSON.
    """
    response = _client.chat.completions.create(
        model=settings.model_name,
        temperature=temperature,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    raw = response.choices[0].message.content.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.error("GPT returned invalid JSON: %s", raw)
        raise ValueError(f"GPT returned invalid JSON: {exc}") from exc
