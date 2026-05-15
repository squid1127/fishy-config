"""Tests for models."""

import pytest
from pathlib import Path
from fishy_config.models.config import EngineConfig
from fishy_config.models.enums import FileType, ArtifactType


def test_engine_config_creation(tmp_src_dir, tmp_dist_dir):
    """Test EngineConfig creation."""
    config = EngineConfig(source_dir=tmp_src_dir, output_dir=tmp_dist_dir)
    assert config.source_dir == tmp_src_dir
    assert config.output_dir == tmp_dist_dir


def test_engine_config_context(tmp_src_dir, tmp_dist_dir):
    """Test EngineConfig with context."""
    config = EngineConfig(source_dir=tmp_src_dir, output_dir=tmp_dist_dir, context={"key": "value"})
    assert config.context == {"key": "value"}


def test_file_type_enum():
    """Test FileType enum exists."""
    assert hasattr(FileType, "TEMPLATE")
    assert hasattr(FileType, "METADATA")


def test_artifact_type_enum():
    """Test ArtifactType enum values."""
    assert ArtifactType.ZIP_ARCHIVE.value == "zip"
    assert ArtifactType.DIRECTORY.value == "directory"
