from typing import List, Optional

import json

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from app.db import crud
from app.middleware.auth_middleware import get_current_user
from app.config import settings
from app.schemas.schemas import (
    AuthResponse,
    DevLoginRequest,
    DocumentStatusResponse,
    DocumentUploadResponse,
    FlashcardsRequest,
    FlashcardsResponse,
    GoogleLoginRequest,
    InterviewEvaluateResponse,
    InterviewGenerateRequest,
    InterviewGenerateResponse,
    QuizRequest,
    QuizResponse,
    SessionDetailResponse,
    SessionListItem,
    SummaryRequest,
    SummaryResponse,
)
from app.services import auth_service, document_service, interview_service, session_service, study_service, whisper_service

router = APIRouter(prefix="/api")


# ── Auth ───────────────────────────────────────────────────────

@router.post("/auth/google", response_model=AuthResponse)
def google_login(body: GoogleLoginRequest):
    try:
        return auth_service.google_login(body.token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc))


@router.post("/auth/dev-login", response_model=AuthResponse)
def dev_login(body: DevLoginRequest):
    if not settings.debug:
        raise HTTPException(status_code=403, detail="Not available in production.")
    return auth_service.dev_login(body.email)


# ── Documents ─────────────────────────────────────────────────

@router.post("/documents/upload", response_model=DocumentUploadResponse, status_code=202)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user),
):
    try:
        doc = await document_service.upload_document(file, user_id, background_tasks)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return DocumentUploadResponse(document_id=doc["id"], status=doc["status"])


@router.get("/documents/", response_model=list)
def list_documents(user_id: str = Depends(get_current_user)):
    return crud.get_user_documents(user_id)


@router.get("/documents/{document_id}/status", response_model=DocumentStatusResponse)
def get_document_status(document_id: str):
    doc = crud.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentStatusResponse(
        document_id=doc["id"],
        status=doc["status"],
        filename=doc["filename"],
    )


# ── Study ──────────────────────────────────────────────────────

def _assert_document_ready(document_id: str) -> None:
    """Raise 404 if document not found, 409 if not yet ready."""
    doc = crud.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc["status"] != "ready":
        raise HTTPException(
            status_code=409,
            detail=f"Document is not ready yet (status: {doc['status']}). "
                   "Wait for processing to complete before generating study content.",
        )


@router.post("/study/summary", response_model=SummaryResponse)
def get_summary(body: SummaryRequest, user_id: str = Depends(get_current_user)):
    _assert_document_ready(str(body.document_id))
    try:
        return study_service.generate_summary(str(body.document_id), user_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/study/quiz", response_model=QuizResponse)
def get_quiz(body: QuizRequest, user_id: str = Depends(get_current_user)):
    _assert_document_ready(str(body.document_id))
    try:
        return study_service.generate_quiz(
            str(body.document_id), user_id, body.difficulty, body.num_questions
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/study/summary/stream")
def stream_summary(body: SummaryRequest, user_id: str = Depends(get_current_user)):
    _assert_document_ready(str(body.document_id))
    def event_generator():
        for event in study_service.stream_summary(str(body.document_id), user_id):
            yield f"data: {json.dumps(event)}\n\n"
    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/study/flashcards", response_model=FlashcardsResponse)
def get_flashcards(body: FlashcardsRequest, user_id: str = Depends(get_current_user)):
    _assert_document_ready(str(body.document_id))
    try:
        return study_service.generate_flashcards(
            str(body.document_id), user_id, body.num_cards
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ── Interview ──────────────────────────────────────────────────

@router.post("/interview/generate", response_model=InterviewGenerateResponse)
def generate_interview_question(
    body: InterviewGenerateRequest,
    user_id: str = Depends(get_current_user),
):
    _assert_document_ready(str(body.document_id))
    try:
        return interview_service.generate_question(
            str(body.document_id), user_id, body.difficulty
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/interview/evaluate/stream")
async def stream_evaluate(
    question_id: str = Form(...),
    session_id: str = Form(...),
    user_answer: Optional[str] = Form(None),
    audio_file: Optional[UploadFile] = File(None),
):
    if audio_file is not None:
        try:
            audio_bytes = await audio_file.read()
            user_answer = whisper_service.transcribe(audio_bytes, audio_file.filename or "audio.webm")
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))
    if not user_answer:
        raise HTTPException(status_code=422, detail="Provide either user_answer (text) or audio_file.")
    def event_generator():
        for event in interview_service.stream_evaluate(question_id, session_id, user_answer):
            yield f"data: {json.dumps(event)}\n\n"
    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/interview/evaluate", response_model=InterviewEvaluateResponse)
async def evaluate_interview_answer(
    question_id: str = Form(...),
    session_id: str = Form(...),
    user_answer: Optional[str] = Form(None),
    audio_file: Optional[UploadFile] = File(None),
):
    """
    Accepts either a typed user_answer OR an audio_file — not both.
    If audio_file is provided, Whisper transcribes it before evaluation.
    """
    transcription: Optional[str] = None

    if audio_file is not None:
        try:
            audio_bytes = await audio_file.read()
            transcription = whisper_service.transcribe(audio_bytes, audio_file.filename or "audio.webm")
            user_answer = transcription
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))

    if not user_answer:
        raise HTTPException(
            status_code=422,
            detail="Provide either user_answer (text) or audio_file.",
        )

    try:
        result = interview_service.evaluate_answer(question_id, session_id, user_answer)
        result["transcription"] = transcription
        return result
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ── Sessions ───────────────────────────────────────────────────

@router.get("/sessions/", response_model=List[SessionListItem])
def list_sessions(user_id: str = Depends(get_current_user)):
    return session_service.get_user_sessions(user_id)


@router.get("/sessions/{session_id}", response_model=SessionDetailResponse)
def get_session(session_id: str, user_id: str = Depends(get_current_user)):
    try:
        return session_service.get_session_detail(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
