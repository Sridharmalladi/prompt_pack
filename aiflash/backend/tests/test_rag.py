"""Unit tests for rag_service — chunk retrieval and context building."""
from unittest.mock import patch

from app.services import rag_service


def _make_chunks(n: int, content_length: int = 100) -> list:
    return [
        {"content": f"chunk_{i} " + ("x " * content_length), "similarity": 0.9 - i * 0.05}
        for i in range(n)
    ]


def test_build_context_returns_numbered_chunks():
    chunks = _make_chunks(3, content_length=10)
    with patch("app.services.rag_service.retrieve_chunks", return_value=chunks):
        context = rag_service.build_context("query", "doc-id", top_k=3)
    assert "[1]" in context
    assert "[2]" in context
    assert "[3]" in context


def test_build_context_empty_when_no_chunks():
    with patch("app.services.rag_service.retrieve_chunks", return_value=[]):
        context = rag_service.build_context("query", "doc-id")
    assert context == ""


def test_build_context_respects_char_limit():
    """Context must not exceed _MAX_CONTEXT_CHARS."""
    # Each chunk is ~600 chars — 20 chunks would be 12k, well over 6k limit
    chunks = _make_chunks(20, content_length=300)
    with patch("app.services.rag_service.retrieve_chunks", return_value=chunks):
        context = rag_service.build_context("query", "doc-id", top_k=20)
    assert len(context) <= rag_service._MAX_CONTEXT_CHARS


def test_build_context_single_chunk():
    chunks = [{"content": "only one chunk here", "similarity": 0.95}]
    with patch("app.services.rag_service.retrieve_chunks", return_value=chunks):
        context = rag_service.build_context("query", "doc-id")
    assert "only one chunk here" in context
    assert "[1]" in context
