"""Unit tests for loader module."""

from pathlib import Path

import pytest

from fishy_config.exceptions import ContextLoadError
from fishy_config.loader import (
    deep_merge,
    load_context,
    load_yaml_file,
    merge_contexts,
    shallow_merge,
)
from fishy_config.models import MergeStrategy


class TestLoadYamlFile:
    """Tests for load_yaml_file function."""

    def test_load_valid_yaml(self, tmp_config_dir):
        """Test loading a valid YAML file."""
        yaml_file = tmp_config_dir / "test.yaml"
        yaml_file.write_text("key: value\nnumber: 42\n")

        result = load_yaml_file(yaml_file)
        assert result == {"key": "value", "number": 42}

    def test_load_yaml_not_found(self, tmp_config_dir):
        """Test error when YAML file doesn't exist."""
        with pytest.raises(ContextLoadError, match="not found"):
            load_yaml_file(tmp_config_dir / "nonexistent.yaml")

    def test_load_yaml_invalid_syntax(self, tmp_config_dir):
        """Test error on invalid YAML syntax."""
        yaml_file = tmp_config_dir / "bad.yaml"
        yaml_file.write_text("invalid: yaml: content:\n")

        with pytest.raises(ContextLoadError):
            load_yaml_file(yaml_file)

    def test_load_yaml_not_dict(self, tmp_config_dir):
        """Test error when YAML is not a dict."""
        yaml_file = tmp_config_dir / "list.yaml"
        yaml_file.write_text("- item1\n- item2\n")

        with pytest.raises(ContextLoadError, match="must contain a dict"):
            load_yaml_file(yaml_file)


class TestMergeStrategies:
    """Tests for merge strategy functions."""

    def test_deep_merge_simple(self):
        """Test deep merge with simple dicts."""
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        result = deep_merge(base, override)
        assert result == {"a": 1, "b": 3, "c": 4}

    def test_deep_merge_nested(self):
        """Test deep merge with nested dicts."""
        base = {"a": {"x": 1, "y": 2}, "b": 3}
        override = {"a": {"y": 20, "z": 30}, "c": 40}
        result = deep_merge(base, override)
        assert result == {"a": {"x": 1, "y": 20, "z": 30}, "b": 3, "c": 40}

    def test_shallow_merge(self):
        """Test shallow merge only affects top level."""
        base = {"a": {"x": 1}, "b": 2}
        override = {"a": {"y": 2}, "c": 3}
        result = shallow_merge(base, override)
        # 'a' is completely replaced
        assert result == {"a": {"y": 2}, "b": 2, "c": 3}

    def test_merge_contexts_deep(self):
        """Test merge_contexts with deep strategy."""
        base = {"db": {"host": "localhost", "port": 5432}}
        override = {"db": {"port": 3306}}
        result = merge_contexts(base, override, MergeStrategy.DEEP)
        assert result["db"]["host"] == "localhost"
        assert result["db"]["port"] == 3306

    def test_merge_contexts_shallow(self):
        """Test merge_contexts with shallow strategy."""
        base = {"db": {"host": "localhost", "port": 5432}}
        override = {"db": {"port": 3306}}
        result = merge_contexts(base, override, MergeStrategy.SHALLOW)
        assert result["db"] == {"port": 3306}  # db is replaced entirely

    def test_merge_contexts_replace(self):
        """Test merge_contexts with replace strategy."""
        base = {"db": {"host": "localhost"}}
        override = {"app": "myapp"}
        result = merge_contexts(base, override, MergeStrategy.REPLACE)
        assert result == {"app": "myapp"}


class TestLoadContext:
    """Tests for load_context function."""

    def test_load_context_with_yaml(self, simple_config):
        """Test loading context from context.yaml."""
        ctx = load_context(simple_config)
        assert ctx.data["name"] == "TestProject"
        assert ctx.data["version"] == "1.0.0"

    def test_load_context_with_runtime_override(self, tmp_config_dir):
        """Test runtime data overrides YAML."""
        yaml_file = tmp_config_dir / "context.yaml"
        yaml_file.write_text("name: original\nvalue: 42\n")

        runtime = {"name": "overridden"}
        ctx = load_context(tmp_config_dir, runtime)
        assert ctx.data["name"] == "overridden"
        assert ctx.data["value"] == 42

    def test_load_context_no_yaml_file(self, tmp_config_dir):
        """Test loading context when no context.yaml exists."""
        runtime = {"key": "value"}
        ctx = load_context(tmp_config_dir, runtime)
        assert ctx.data == {"key": "value"}

    def test_load_context_empty(self, tmp_config_dir):
        """Test loading context with no YAML and no runtime data."""
        ctx = load_context(tmp_config_dir)
        assert ctx.data == {}
