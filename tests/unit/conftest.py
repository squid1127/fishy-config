"""Conftest for unit tests."""

import pytest
from pathlib import Path
from unittest.mock import Mock


@pytest.fixture
def tmp_src_dir(tmp_path):
    """Create a temporary source directory."""
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    return src_dir


@pytest.fixture
def tmp_dist_dir(tmp_path):
    """Create a temporary output directory."""
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()
    return dist_dir


@pytest.fixture
def temp_template_file(tmp_src_dir):
    """Create a temporary template file."""
    template = tmp_src_dir / "config.yaml.j2"
    template.write_text("key: {{ value }}")
    return template
