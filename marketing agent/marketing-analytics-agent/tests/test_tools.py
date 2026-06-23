"""
Unit tests for the non-LLM layers: SQL validation, database, glossary, and tool dispatch.

These tests run without an Anthropic API key. The conftest.py fixture seeds the
database automatically before the session starts, so no manual setup is required.
"""

import pytest

from src import database, glossary, tools


# ---------------------------------------------------------------------------
# SQL safety validator
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("sql", [
    "SELECT 1",
    "select * from channels",
    "WITH t AS (SELECT 1) SELECT * FROM t",
])
def test_safe_selects_pass(sql):
    ok, _ = database.is_safe_select(sql)
    assert ok


@pytest.mark.parametrize("sql", [
    "DROP TABLE channels",
    "DELETE FROM campaigns",
    "SELECT 1; DROP TABLE channels",   # stacked statement
    "UPDATE channels SET name='x'",
    "INSERT INTO channels VALUES (99,'x')",
])
def test_unsafe_statements_blocked(sql):
    ok, reason = database.is_safe_select(sql)
    assert not ok
    assert reason  # should always return an explanation


# ---------------------------------------------------------------------------
# Database layer
# ---------------------------------------------------------------------------

def test_schema_lists_core_tables():
    schema = database.describe_schema()
    for table in ("channels", "campaigns", "daily_performance"):
        assert table in schema


def test_query_returns_rows():
    result = database.run_select("SELECT COUNT(*) AS n FROM channels")
    assert "error" not in result
    assert result["rows"][0]["n"] == 5  # seed.py creates exactly 5 channels


def test_blocked_query_returns_error_dict():
    result = database.run_select("DELETE FROM channels")
    assert "error" in result


# ---------------------------------------------------------------------------
# Glossary
# ---------------------------------------------------------------------------

def test_glossary_exact_acronym_match():
    hits = glossary.lookup("what is ROAS?")
    assert any(h.startswith("ROAS") for h in hits)


def test_glossary_returns_empty_for_unknown_term():
    assert glossary.lookup("xyzzy not a metric") == []


# ---------------------------------------------------------------------------
# Tool dispatch
# ---------------------------------------------------------------------------

def test_run_tool_unknown_name_returns_error():
    out = tools.run_tool("does_not_exist", {})
    assert "error" in out


def test_run_tool_define_metric_returns_definitions():
    out = tools.run_tool("define_metric", {"term": "CAC"})
    assert out["definitions"]


def test_run_tool_get_schema_returns_schema():
    out = tools.run_tool("get_schema", {})
    assert "schema" in out
    assert "daily_performance" in out["schema"]


def test_run_tool_get_trend_returns_rows():
    out = tools.run_tool("get_trend", {"metric": "spend", "granularity": "month"})
    assert "error" not in out
    assert out["rows"]


def test_run_tool_get_trend_invalid_metric():
    out = tools.run_tool("get_trend", {"metric": "not_a_metric"})
    assert "error" in out
