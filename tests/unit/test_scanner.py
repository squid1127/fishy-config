"""Tests for scanner module."""

import pytest
from unittest.mock import Mock
from fishy_config.scanner import SourceTreeScanner
from fishy_config.models.config import EngineConfig


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
    renderer.render = Mock(side_effect=lambda text, context: text)
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


def test_scan_skips_files_matching_patterns(tmp_path):
    """Files matching skip patterns are not queued."""
    source = tmp_path / "src"
    output = tmp_path / "dist"
    source.mkdir()
    output.mkdir()

    (source / "keep.txt").write_text("keep")
    (source / "skip.txt").write_text("skip")
    (source / "notes.log").write_text("skip")

    config = EngineConfig(
        source_dir=source,
        output_dir=output,
        skip_patterns=["skip.txt", "*.log"],
    )
    renderer = Mock()
    renderer.render = Mock(side_effect=lambda text, context: text)

    scanner = SourceTreeScanner(config, renderer)
    queued = list(scanner.scan())

    queued_names = sorted(q.source.name for q in queued)
    assert queued_names == ["keep.txt"]


def test_scan_skips_directories_matching_patterns(tmp_path):
    """Directories matching skip patterns are skipped recursively."""
    source = tmp_path / "src"
    output = tmp_path / "dist"
    source.mkdir()
    output.mkdir()

    public_dir = source / "public"
    internal_dir = source / "internal"
    public_dir.mkdir()
    internal_dir.mkdir()

    (public_dir / "kept.txt").write_text("keep")
    (internal_dir / "ignored.txt").write_text("skip")

    config = EngineConfig(
        source_dir=source,
        output_dir=output,
        skip_patterns=["internal/**"],
    )
    renderer = Mock()
    renderer.render = Mock(side_effect=lambda text, context: text)

    scanner = SourceTreeScanner(config, renderer)
    queued = list(scanner.scan())

    queued_relative_paths = sorted(q.relative_path.as_posix() for q in queued)
    assert queued_relative_paths == ["public/kept.txt"]
