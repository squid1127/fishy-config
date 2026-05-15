"""Tests for CLI app."""

import pytest
from unittest.mock import Mock, patch
from typer.testing import CliRunner
from fishy_config.cli.app import app


@pytest.fixture
def cli_runner():
    """Create a Typer CLI test runner."""
    return CliRunner()


def test_cli_app_exists():
    """Test CLI app is properly configured."""
    assert app is not None
    assert hasattr(app, "command")
