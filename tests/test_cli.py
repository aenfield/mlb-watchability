"""Tests for the CLI module."""

from typer.testing import CliRunner

from mlb_watchability.cli import app


def test_cli_with_default_date():
    """Test that the CLI runs successfully with default date."""
    runner = CliRunner()
    result = runner.invoke(app, [])
    
    assert result.exit_code == 0
