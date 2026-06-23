"""
Database layer — SQLite connection management, schema introspection, and SQL safety.

All queries pass through is_safe_select() before execution. The connection is opened
and closed per-call rather than held open, which keeps things simple for a single-file
SQLite setup.
"""

import re
import sqlite3
from typing import Any

from . import config


def _connect() -> sqlite3.Connection:
    if not config.DB_PATH.exists():
        raise FileNotFoundError(
            f"Database not found at {config.DB_PATH}. "
            "Run `python data/seed.py` first."
        )
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row  # lets us access columns by name
    return conn


def describe_schema() -> str:
    """Return the table/column layout as plain text for the model to read."""
    conn = _connect()
    try:
        tables = [
            r["name"]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
        ]
        lines = []
        for t in tables:
            cols = conn.execute(f"PRAGMA table_info({t})").fetchall()
            col_str = ", ".join(f"{c['name']} {c['type']}" for c in cols)
            lines.append(f"TABLE {t}({col_str})")
        return "\n".join(lines)
    finally:
        conn.close()


# Anything that isn't a plain read gets rejected before it touches the database.
# The semicolon check must come before the keyword regex — stacked statements like
# "SELECT 1; DROP TABLE channels" would otherwise pass a naive starts-with check.
_FORBIDDEN = re.compile(
    r"\b(insert|update|delete|drop|alter|create|replace|attach|detach|pragma|vacuum)\b",
    re.IGNORECASE,
)


def is_safe_select(sql: str) -> tuple[bool, str]:
    """Return (True, '') if sql is a safe read-only query, or (False, reason) if not."""
    stripped = sql.strip().rstrip(";").strip()
    if ";" in stripped:
        return False, "Only one statement at a time."
    if not stripped.lower().startswith(("select", "with")):
        return False, "Only SELECT or WITH queries are allowed."
    if _FORBIDDEN.search(stripped):
        return False, "Query contains a write or schema-changing keyword."
    return True, ""


def run_select(sql: str) -> dict[str, Any]:
    """Validate and execute a SELECT, returning rows plus metadata."""
    if config.READ_ONLY:
        ok, reason = is_safe_select(sql)
        if not ok:
            return {"error": reason, "rows": [], "sql": sql}

    conn = _connect()
    try:
        cur = conn.execute(sql)
        rows = [dict(r) for r in cur.fetchmany(config.MAX_ROWS)]
        # A second fetchmany(1) tells us whether the result set was cut short
        # without loading all remaining rows into memory.
        truncated = len(cur.fetchmany(1)) > 0
        return {
            "rows": rows,
            "row_count": len(rows),
            "truncated": truncated,
            "sql": sql,
        }
    except sqlite3.Error as e:
        return {"error": f"SQL error: {e}", "rows": [], "sql": sql}
    finally:
        conn.close()
