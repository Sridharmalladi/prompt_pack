"""Integration tests for session_service — mocks Supabase."""
from unittest.mock import patch

import pytest

from app.services import session_service
from tests.conftest import TEST_DOCUMENT_ID, TEST_SESSION_ID, TEST_USER_ID


def _study_session(session_type="summary"):
    return {
        "id": TEST_SESSION_ID,
        "user_id": TEST_USER_ID,
        "document_id": TEST_DOCUMENT_ID,
        "session_type": session_type,
        "created_at": "2026-01-01T00:00:00+00:00",
        "completed_at": "2026-01-01T00:01:00+00:00",
    }


def _interview_session():
    return {
        "id": TEST_SESSION_ID,
        "user_id": TEST_USER_ID,
        "document_id": TEST_DOCUMENT_ID,
        "created_at": "2026-01-01T00:00:00+00:00",
    }


# ── get_user_sessions ───────────────────────────────────────────

def test_get_user_sessions_combines_study_and_interview():
    with (
        patch("app.db.crud.get_user_study_sessions", return_value=[_study_session()]),
        patch("app.db.crud.get_user_interview_sessions", return_value=[_interview_session()]),
    ):
        sessions = session_service.get_user_sessions(TEST_USER_ID)

    assert len(sessions) == 2
    types = {s["type"] for s in sessions}
    assert "study" in types
    assert "interview" in types


def test_get_user_sessions_empty():
    with (
        patch("app.db.crud.get_user_study_sessions", return_value=[]),
        patch("app.db.crud.get_user_interview_sessions", return_value=[]),
    ):
        sessions = session_service.get_user_sessions(TEST_USER_ID)
    assert sessions == []


# ── get_session_detail ──────────────────────────────────────────

def test_get_session_detail_study_summary():
    with (
        patch("app.db.crud.get_study_session", return_value=_study_session("summary")),
    ):
        detail = session_service.get_session_detail(TEST_SESSION_ID)

    assert detail["type"] == "study"
    assert detail["session_type"] == "summary"
    assert detail["results"] == []


def test_get_session_detail_quiz_includes_results():
    quiz_results = [{"question": "Q?", "correct_answer": "A"}]
    with (
        patch("app.db.crud.get_study_session", return_value=_study_session("quiz")),
        patch("app.db.crud.get_quiz_results", return_value=quiz_results),
    ):
        detail = session_service.get_session_detail(TEST_SESSION_ID)

    assert detail["session_type"] == "quiz"
    assert len(detail["results"]) == 1


def test_get_session_detail_interview():
    interview_results = [{"question": "Tell me about X.", "score": 7}]
    with (
        patch("app.db.crud.get_study_session", return_value=None),
        patch("app.db.crud.get_interview_session", return_value=_interview_session()),
        patch("app.db.crud.get_interview_results", return_value=interview_results),
    ):
        detail = session_service.get_session_detail(TEST_SESSION_ID)

    assert detail["type"] == "interview"
    assert detail["results"][0]["score"] == 7


def test_get_session_detail_not_found():
    with (
        patch("app.db.crud.get_study_session", return_value=None),
        patch("app.db.crud.get_interview_session", return_value=None),
    ):
        with pytest.raises(ValueError, match="Session not found"):
            session_service.get_session_detail("nonexistent-id")
