"""Tests for scanner module."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from fishy_config.scanner import SourceTreeScanner
from fishy_config.models.config import EngineConfig
from fishy_config.models.enums import FileType


@pytest.fixture
def mock_config():
    """Create a mock EngineConfig."""
    config = Mock(spec=EngineConfig)
    config.source_dir = Path("src")
    config.context = {}
    return config


@pytest.fixture
def mock_renderer():
    """Create a mock TemplateRenderer."""
    renderer = Mock()
    renderer.render_template = Mock(return_value="rendered content")
    return renderer


@pytest.fixture
def scanner(mock_config, mock_renderer):
    """Create a SourceTreeScanner instance."""
    return SourceTreeScanner(mock_config, mock_renderer)


def test_scanner_init(scanner, mock_config, mock_renderer):
    """Test scanner initialization."""
    assert scanner.config == mock_config
    assert scanner.renderer == mock_renderer


def test_scanner_attributes(scanner):
    """Test scanner has expected attributes."""
    assert hasattr(scanner, "config")
    assert hasattr(scanner, "renderer")
    assert hasattr(scanner, "scan")
