"""Unit tests for file parsing utils and document upload route."""
import pytest

from app.utils.chunker import chunk_text
from app.utils.text_cleaner import clean_text


# ── chunk_text ─────────────────────────────────────────────────

def test_chunk_text_basic_split():
    words = ["word"] * 350
    text = " ".join(words)
    chunks = chunk_text(text, chunk_size=300, overlap=50)
    assert len(chunks) == 2
    assert len(chunks[0].split()) == 300
    assert len(chunks[1].split()) == 100  # 350 - 250 (300 - 50 overlap)


def test_chunk_text_short_document():
    """Text shorter than chunk_size produces exactly one chunk."""
    text = "short text here"
    chunks = chunk_text(text)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_chunk_text_overlap():
    """The last `overlap` words of chunk N are the first words of chunk N+1."""
    words = [str(i) for i in range(400)]
    text = " ".join(words)
    chunks = chunk_text(text, chunk_size=300, overlap=50)
    # Last 50 words of chunk 0 == first 50 words of chunk 1
    tail_0 = chunks[0].split()[-50:]
    head_1 = chunks[1].split()[:50]
    assert tail_0 == head_1


def test_chunk_text_empty():
    assert chunk_text("") == []
    assert chunk_text("   ") == []


# ── clean_text ─────────────────────────────────────────────────

def test_clean_text_normalizes_whitespace():
    raw = "hello   world\t\there"
    result = clean_text(raw)
    assert "  " not in result
    assert "\t" not in result


def test_clean_text_strips_control_chars():
    raw = "hello\x00world\x1f"
    result = clean_text(raw)
    assert "\x00" not in result
    assert "\x1f" not in result


def test_clean_text_collapses_blank_lines():
    raw = "line1\n\n\n\n\nline2"
    result = clean_text(raw)
    assert "\n\n\n" not in result


def test_clean_text_preserves_content():
    raw = "  The quick brown fox.  "
    result = clean_text(raw)
    assert "quick brown fox" in result


# ── Upload endpoint ─────────────────────────────────────────────

def test_upload_unsupported_format(client):
    """Uploading an unsupported file type returns 422."""
    response = client.post(
        "/api/documents/upload",
        files={"file": ("test.exe", b"binary content", "application/octet-stream")},
    )
    assert response.status_code == 422
