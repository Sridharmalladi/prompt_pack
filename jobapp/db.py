import sqlite3
import json
from contextlib import contextmanager
from typing import List, Dict, Optional

DB_PATH = "data/sessions.db"


@contextmanager
def _conn():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with _conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                session_name    TEXT UNIQUE,
                job_description TEXT,
                resumes         TEXT,
                results         TEXT
            )
        """)


def save_session(session_name: str, job_description: str, resumes: List[str], results: List[Dict]):
    with _conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO sessions (session_name, job_description, resumes, results) VALUES (?, ?, ?, ?)",
            (session_name, job_description, json.dumps(resumes), json.dumps(results)),
        )


def load_all_sessions() -> List[str]:
    with _conn() as conn:
        rows = conn.execute("SELECT session_name FROM sessions ORDER BY id DESC").fetchall()
    return [row[0] for row in rows]


def load_session(session_name: str) -> Optional[Dict]:
    with _conn() as conn:
        row = conn.execute(
            "SELECT job_description, resumes, results FROM sessions WHERE session_name = ?",
            (session_name,),
        ).fetchone()
    if row:
        return {
            "job_description": row[0],
            "resumes": json.loads(row[1]),
            "results": json.loads(row[2]),
        }
    return None


def delete_session(session_name: str):
    with _conn() as conn:
        conn.execute("DELETE FROM sessions WHERE session_name = ?", (session_name,))
