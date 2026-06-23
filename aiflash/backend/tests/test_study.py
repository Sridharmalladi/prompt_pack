"""Integration tests for study_service — mocks OpenAI and Supabase."""
from unittest.mock import patch

import pytest

from app.services import study_service
from tests.conftest import TEST_DOCUMENT_ID, TEST_SESSION_ID, TEST_USER_ID


# ── generate_summary ────────────────────────────────────────────

def test_generate_summary_returns_correct_shape():
    summary_payload = {"summary": "A great summary.", "key_points": ["point 1", "point 2"]}

    with (
        patch("app.services.rag_service.build_context", return_value="[1] some content"),
        patch("app.services.llm_service.chat_json", return_value=summary_payload),
        patch("app.db.crud.create_study_session", return_value={"id": TEST_SESSION_ID}),
        patch("app.db.crud.complete_study_session"),
    ):
        result = study_service.generate_summary(TEST_DOCUMENT_ID, TEST_USER_ID)

    assert result["summary"] == "A great summary."
    assert result["key_points"] == ["point 1", "point 2"]
    assert "session_id" in result


def test_generate_summary_raises_when_no_context():
    with patch("app.services.rag_service.build_context", return_value=""):
        with pytest.raises(ValueError, match="No content found"):
            study_service.generate_summary(TEST_DOCUMENT_ID, TEST_USER_ID)


# ── generate_quiz ───────────────────────────────────────────────

def test_generate_quiz_returns_questions():
    quiz_payload = {
        "questions": [
            {
                "question": "What is X?",
                "options": ["A. 1", "B. 2", "C. 3", "D. 4"],
                "correct_answer": "A",
                "explanation": "Because 1.",
            }
        ]
    }

    with (
        patch("app.services.rag_service.build_context", return_value="[1] content"),
        patch("app.services.llm_service.chat_json", return_value=quiz_payload),
        patch("app.db.crud.create_study_session", return_value={"id": TEST_SESSION_ID}),
        patch("app.db.crud.store_quiz_results"),
        patch("app.db.crud.complete_study_session"),
    ):
        result = study_service.generate_quiz(TEST_DOCUMENT_ID, TEST_USER_ID)

    assert len(result["questions"]) == 1
    assert result["questions"][0]["question"] == "What is X?"


# ── generate_flashcards ─────────────────────────────────────────

def test_generate_flashcards_returns_cards():
    fc_payload = {"flashcards": [{"front": "Q?", "back": "A."}]}

    with (
        patch("app.services.rag_service.build_context", return_value="[1] content"),
        patch("app.services.llm_service.chat_json", return_value=fc_payload),
        patch("app.db.crud.create_study_session", return_value={"id": TEST_SESSION_ID}),
        patch("app.db.crud.complete_study_session"),
    ):
        result = study_service.generate_flashcards(TEST_DOCUMENT_ID, TEST_USER_ID)

    assert result["flashcards"][0]["front"] == "Q?"
    assert result["flashcards"][0]["back"] == "A."
