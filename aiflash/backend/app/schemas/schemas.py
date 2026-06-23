from datetime import datetime
from typing import List
from uuid import UUID

from pydantic import BaseModel


# ── Auth schemas ──────────────────────────────────────────────

class GoogleLoginRequest(BaseModel):
    token: str


class DevLoginRequest(BaseModel):
    email: str


class UserOut(BaseModel):
    id: UUID
    email: str
    name: str


class AuthResponse(BaseModel):
    access_token: str
    user: UserOut


# ── Document schemas ──────────────────────────────────────────

class DocumentUploadResponse(BaseModel):
    document_id: UUID
    status: str


class DocumentStatusResponse(BaseModel):
    document_id: UUID
    status: str
    filename: str


class DocumentListItem(BaseModel):
    document_id: UUID
    filename: str
    file_type: str
    status: str
    created_at: datetime


# ── Study schemas ──────────────────────────────────────────────

class SummaryRequest(BaseModel):
    document_id: UUID


class SummaryResponse(BaseModel):
    session_id: UUID
    summary: str
    key_points: List[str]


class QuizRequest(BaseModel):
    document_id: UUID
    difficulty: str = "medium"
    num_questions: int = 5


class QuizQuestion(BaseModel):
    question: str
    options: List[str]
    correct_answer: str
    explanation: str


class QuizResponse(BaseModel):
    session_id: UUID
    questions: List[QuizQuestion]


class FlashcardsRequest(BaseModel):
    document_id: UUID
    num_cards: int = 10


class Flashcard(BaseModel):
    front: str
    back: str


class FlashcardsResponse(BaseModel):
    session_id: UUID
    flashcards: List[Flashcard]


# ── Interview schemas ──────────────────────────────────────────

class InterviewGenerateRequest(BaseModel):
    document_id: UUID
    difficulty: str = "medium"


class InterviewGenerateResponse(BaseModel):
    session_id: UUID
    question_id: UUID
    question: str
    scenario: str


class InterviewEvaluateRequest(BaseModel):
    question_id: UUID
    session_id: UUID
    user_answer: str


class InterviewEvaluateResponse(BaseModel):
    score: int
    strengths: List[str]
    weaknesses: List[str]
    feedback: str
    transcription: str | None = None


# ── Session schemas ────────────────────────────────────────────

class SessionListItem(BaseModel):
    id: UUID
    type: str            # "study" or "interview"
    session_type: str    # "quiz", "summary", "flashcard", "interview"
    document_id: UUID
    created_at: datetime
    completed_at: datetime | None = None


class SessionDetailResponse(BaseModel):
    id: UUID
    type: str
    session_type: str
    document_id: UUID
    created_at: datetime
    completed_at: datetime | None = None
    results: list = []
