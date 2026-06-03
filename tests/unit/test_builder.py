"""Tests for builder module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from fishy_config.builder import build
from fishy_config.models.config import EngineConfig
from fishy_config.models.artifact import ArtifactResult


@pytest.fixture
def mock_config():
    """Create a mock EngineConfig."""
    config = Mock(spec=EngineConfig)
    config.source_dir = Path("src")
    config.output_dir = Path("dist")
    config.artifacts = []
    config.context = {}
    return config


@patch("fishy_config.builder.TemplateRenderer")
@patch("fishy_config.builder.SourceTreeScanner")
@patch("fishy_config.builder.ArtifactGenerator")
@patch("fishy_config.builder.OutputBuilder")
def test_build_returns_list(mock_output, mock_artifact, mock_scanner, mock_renderer, mock_config):
    """Test build function returns a list."""
    mock_scanner_instance = MagicMock()
    mock_scanner_instance.scan.return_value = []
    mock_scanner.return_value = mock_scanner_instance

    mock_artifact_instance = MagicMock()
    mock_artifact_instance.generate_artifacts.return_value = []
    mock_artifact.return_value = mock_artifact_instance

    result = build(mock_config)
    assert isinstance(result, list)


@patch("fishy_config.builder.TemplateRenderer")
@patch("fishy_config.builder.SourceTreeScanner")
@patch("fishy_config.builder.ArtifactGenerator")
@patch("fishy_config.builder.OutputBuilder")
def test_build_creates_components(
    mock_output, mock_artifact, mock_scanner, mock_renderer, mock_config
):
    """Test build function instantiates all required components."""
    mock_scanner_instance = MagicMock()
    mock_scanner_instance.scan.return_value = []
    mock_scanner.return_value = mock_scanner_instance

    mock_artifact_instance = MagicMock()
    mock_artifact_instance.generate_artifacts.return_value = []
    mock_artifact.return_value = mock_artifact_instance

    build(mock_config)

    mock_renderer.assert_called_once_with(mock_config, [])
    mock_scanner.assert_called_once()
    mock_artifact.assert_called_once()
    mock_output.assert_called_once()
