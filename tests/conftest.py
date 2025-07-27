"""
Pytest configuration and fixtures.
"""

from pathlib import Path

import pytest
from dotenv import load_dotenv


@pytest.fixture(scope="session", autouse=True)
def load_env_vars() -> None:
    """Load environment variables from .env file if it exists."""
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        load_dotenv(env_file)
