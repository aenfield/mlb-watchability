"""Tests for the CLI module."""

import pytest
from typer.testing import CliRunner

from mlb_watchability.cli import app


@pytest.mark.costly
def test_cli_with_default_date() -> None:
    """Test that the CLI runs successfully with default date."""
    runner = CliRunner()
    result = runner.invoke(app, [])

    assert result.exit_code == 0
