"""Pydantic v2 request models."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ProblemType(str, Enum):
    classification = "classification"
    regression = "regression"
    clustering = "clustering"
    unknown = "unknown"


class NotebookRequest(BaseModel):
    """Payload for POST /generate-notebook."""

    context_summary: str = Field(min_length=1, max_length=4000)
    context_insights: Optional[str] = Field(
        default=None,
        max_length=4000,
        description="JSON-serialised AgenticInsights from /analyze",
    )
    filename_hint: str = Field(
        default="analysis",
        max_length=64,
        description="Used as the suggested download filename",
    )


class ChatRequest(BaseModel):
    """Payload for POST /chat."""

    session_id: str = Field(min_length=1, max_length=128)
    question: str = Field(min_length=1, max_length=2000)
    context_summary: str = Field(
        default="",
        max_length=4000,
        description="Dataset summary text carried from /analyze response",
    )
    context_insights: Optional[str] = Field(
        default=None,
        max_length=4000,
        description="JSON-serialised AgenticInsights from /analyze, optional",
    )
