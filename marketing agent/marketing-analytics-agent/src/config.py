"""
Central configuration — loads from the environment (.env file or shell exports).
All tuneable values live here so nothing is hard-coded across the codebase.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Required — the agent will refuse to start without this.
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Swap to claude-opus-4-8 for harder multi-step reasoning; sonnet handles most queries well.
MODEL = os.getenv("AGENT_MODEL", "claude-sonnet-4-6")

# Resolved from this file's location so the path is correct regardless of cwd.
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "marketing.db"

# Enforces read-only SQL validation before any query reaches the database.
READ_ONLY = True

# Guards against flooding the model context with a broad SELECT result set.
MAX_ROWS = 200

# Safety cap on the agent loop — well-formed questions resolve in 3–4 turns.
MAX_TURNS = 8
