"""
Shared fixtures for all tests.
- Supabase is always mocked — no real DB calls.
- OpenAI is always mocked — no real API calls.
- Auth is bypassed via dependency override.
"""
import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.middleware.auth_middleware import get_current_user

TEST_USER_ID = "00000000-0000-0000-0000-000000000001"
TEST_DOCUMENT_ID = "00000000-0000-0000-0000-000000000002"
TEST_SESSION_ID = "00000000-0000-0000-0000-000000000003"
TEST_QUESTION_ID = "00000000-0000-0000-0000-000000000004"


@pytest.fixture
def client():
    """TestClient with auth bypassed — returns TEST_USER_ID for all protected routes."""
    app.dependency_overrides[get_current_user] = lambda: TEST_USER_ID
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def mock_supabase():
    """Mock the Supabase client singleton used in all DB operations."""
    with patch("app.db.supabase_client.get_supabase") as mock:
        yield mock


def make_supabase_mock(return_data):
    """
    Helper: build a mock Supabase chain that returns `return_data`.
    Covers: .table().select/insert/update/upsert().eq().order()
            .maybe_single().execute() patterns.
    """
    mock_client = MagicMock()
    mock_execute = MagicMock()
    mock_execute.data = return_data

    # Every chained method returns the same mock so .execute() always works
    chain = MagicMock()
    chain.execute.return_value = mock_execute
    chain.eq.return_value = chain
    chain.order.return_value = chain
    chain.maybe_single.return_value = chain
    chain.select.return_value = chain
    chain.insert.return_value = chain
    chain.update.return_value = chain
    chain.upsert.return_value = chain

    mock_client.table.return_value = chain
    mock_client.rpc.return_value = chain
    return mock_client


@pytest.fixture
def mock_llm_chat():
    """Mock llm_service.chat — returns plain text."""
    with patch("app.services.llm_service._client") as mock:
        response = MagicMock()
        response.choices[0].message.content = "Mocked GPT response."
        mock.chat.completions.create.return_value = response
        yield mock


@pytest.fixture
def mock_llm_chat_json():
    """Mock llm_service.chat_json — returns a JSON string from GPT."""
    with patch("app.services.llm_service._client") as mock:
        def _json_response(payload: dict):
            response = MagicMock()
            response.choices[0].message.content = json.dumps(payload)
            mock.chat.completions.create.return_value = response
        yield mock, _json_response


@pytest.fixture
def mock_embeddings():
    """Mock embedding_service._client — returns a fixed 1536-dim vector."""
    with patch("app.services.embedding_service._client") as mock:
        fake_vector = [0.1] * 1536
        item = MagicMock()
        item.index = 0
        item.embedding = fake_vector
        response = MagicMock()
        response.data = [item]
        mock.embeddings.create.return_value = response
        yield mock
