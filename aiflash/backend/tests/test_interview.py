"""Integration tests for interview_service — mocks OpenAI and Supabase."""
from unittest.mock import patch

import pytest

from app.services import interview_service
from tests.conftest import (
    TEST_DOCUMENT_ID,
    TEST_QUESTION_ID,
    TEST_SESSION_ID,
    TEST_USER_ID,
)


def _mock_question_row():
    return {
        "id": TEST_QUESTION_ID,
        "session_id": TEST_SESSION_ID,
        "question": "Explain the main concept.",
        "scenario": "You are in a technical interview.",
    }


# ── generate_question ───────────────────────────────────────────

def test_generate_question_returns_correct_shape():
    gpt_payload = {
        "question": "Explain the main concept.",
        "scenario": "You are in a technical interview.",
    }

    with (
        patch("app.services.rag_service.build_context", return_value="[1] content"),
        patch("app.services.llm_service.chat_json", return_value=gpt_payload),
        patch("app.db.crud.create_interview_session", return_value={"id": TEST_SESSION_ID}),
        patch(
            "app.db.crud.store_interview_question",
            return_value={"id": TEST_QUESTION_ID, "session_id": TEST_SESSION_ID, "question": gpt_payload["question"]},
        ),
    ):
        result = interview_service.generate_question(TEST_DOCUMENT_ID, TEST_USER_ID)

    assert result["question"] == "Explain the main concept."
    assert "session_id" in result
    assert "question_id" in result


def test_generate_question_raises_when_no_context():
    with patch("app.services.rag_service.build_context", return_value=""):
        with pytest.raises(ValueError, match="No content found"):
            interview_service.generate_question(TEST_DOCUMENT_ID, TEST_USER_ID)


# ── evaluate_answer ─────────────────────────────────────────────

def test_evaluate_answer_returns_score_and_feedback():
    eval_payload = {
        "score": 8,
        "strengths": ["clear explanation", "good structure"],
        "weaknesses": ["missing edge cases"],
        "feedback": "Good overall, work on edge cases.",
    }

    with (
        patch("app.db.crud.get_interview_question", return_value=_mock_question_row()),
        patch("app.services.llm_service.chat_json", return_value=eval_payload),
        patch("app.db.crud.update_interview_result"),
    ):
        result = interview_service.evaluate_answer(
            TEST_QUESTION_ID, TEST_SESSION_ID, "My detailed answer."
        )

    assert result["score"] == 8
    assert "clear explanation" in result["strengths"]
    assert result["feedback"] == "Good overall, work on edge cases."


def test_evaluate_answer_raises_for_missing_question():
    with patch("app.db.crud.get_interview_question", return_value=None):
        with pytest.raises(ValueError, match="Question not found"):
            interview_service.evaluate_answer(
                TEST_QUESTION_ID, TEST_SESSION_ID, "some answer"
            )
