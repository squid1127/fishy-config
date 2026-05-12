"""Test fixtures and utilities."""

import pytest
from pathlib import Path
import tempfile
import shutil


@pytest.fixture
def tmp_config_dir():
    """Create a temporary config directory for tests."""
    tmpdir = Path(tempfile.mkdtemp(prefix="fishy_config_test_"))
    yield tmpdir
    shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture
def tmp_dest_dir():
    """Create a temporary destination directory for tests."""
    tmpdir = Path(tempfile.mkdtemp(prefix="fishy_config_dest_"))
    yield tmpdir
    shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture
def simple_config(tmp_config_dir):
    """Create a simple config structure with a template and context.yaml."""
    # Create context.yaml
    context_file = tmp_config_dir / "context.yaml"
    context_file.write_text("name: TestProject\nversion: '1.0.0'\n")

    # Create a simple template
    template_file = tmp_config_dir / "config.yaml.j2"
    template_file.write_text("project:\n" "  name: {{ name }}\n" "  version: {{ version }}\n")

    # Create a static file
    static_file = tmp_config_dir / "README.md"
    static_file.write_text("# {{ name }} Configuration\n")

    return tmp_config_dir


@pytest.fixture
def nested_config(tmp_config_dir):
    """Create a nested config structure."""
    # Create context.yaml
    context_file = tmp_config_dir / "context.yaml"
    context_file.write_text(
        "database:\n" "  host: localhost\n" "  port: 5432\n" "app:\n" "  name: myapp\n"
    )

    # Create nested directories
    db_dir = tmp_config_dir / "db"
    db_dir.mkdir()
    db_file = db_dir / "postgres.conf.j2"
    db_file.write_text("host = {{ database.host }}\nport = {{ database.port }}\n")

    app_dir = tmp_config_dir / "app"
    app_dir.mkdir()
    app_file = app_dir / "config.json.j2"
    app_file.write_text('{"name": "{{ app.name }}"}\n')

    return tmp_config_dir
