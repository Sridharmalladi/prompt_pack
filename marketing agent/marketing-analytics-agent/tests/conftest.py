import sys
from pathlib import Path

import pytest

# Make sure the data/ seed script can be found and run before any test touches the DB.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture(scope="session", autouse=True)
def seed_database():
    """Seed a fresh database once per test session so tests don't need manual setup."""
    from data.seed import build
    build()
