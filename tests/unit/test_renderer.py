"""Unit tests for renderer module."""

from pathlib import Path

import pytest

from fishy_config.exceptions import TemplateRenderError
from fishy_config.renderer import Jinja2Renderer


class TestJinja2Renderer:
    """Tests for Jinja2Renderer class."""

    def test_render_simple_template(self, tmp_config_dir):
        """Test rendering a simple template."""
        template_file = tmp_config_dir / "test.txt.j2"
        template_file.write_text("Hello {{ name }}!")

        renderer = Jinja2Renderer(tmp_config_dir)
        result = renderer.render_file(Path("test.txt.j2"), {"name": "World"})
        assert result == "Hello World!"

    def test_render_with_nested_context(self, tmp_config_dir):
        """Test rendering with nested context data."""
        template_file = tmp_config_dir / "config.yaml.j2"
        template_file.write_text("database:\n" "  host: {{ db.host }}\n" "  port: {{ db.port }}\n")

        renderer = Jinja2Renderer(tmp_config_dir)
        context = {"db": {"host": "localhost", "port": 5432}}
        result = renderer.render_file(Path("config.yaml.j2"), context)

        assert "localhost" in result
        assert "5432" in result

    def test_render_with_undefined_strict(self, tmp_config_dir):
        """Test that undefined variables raise error in strict mode."""
        template_file = tmp_config_dir / "test.txt.j2"
        template_file.write_text("Value: {{ undefined_var }}")

        renderer = Jinja2Renderer(tmp_config_dir, strict_undefined=True)
        with pytest.raises(TemplateRenderError, match="Undefined variable"):
            renderer.render_file(Path("test.txt.j2"), {})

    def test_render_with_undefined_lenient(self, tmp_config_dir):
        """Test that undefined variables render as empty in lenient mode."""
        template_file = tmp_config_dir / "test.txt.j2"
        template_file.write_text("Value: {{ undefined_var }}")

        renderer = Jinja2Renderer(tmp_config_dir, strict_undefined=False)
        result = renderer.render_file(Path("test.txt.j2"), {})
        assert "Value:" in result

    def test_render_template_with_filters(self, tmp_config_dir):
        """Test rendering with Jinja2 filters."""
        template_file = tmp_config_dir / "test.txt.j2"
        template_file.write_text("{{ name | upper }}")

        renderer = Jinja2Renderer(tmp_config_dir)
        result = renderer.render_file(Path("test.txt.j2"), {"name": "hello"})
        assert result == "HELLO"

    def test_render_template_with_loops(self, tmp_config_dir):
        """Test rendering with Jinja2 loops."""
        template_file = tmp_config_dir / "test.txt.j2"
        template_file.write_text("{% for item in items %}\n" "- {{ item }}\n" "{% endfor %}")

        renderer = Jinja2Renderer(tmp_config_dir)
        result = renderer.render_file(Path("test.txt.j2"), {"items": ["a", "b", "c"]})
        assert "- a" in result
        assert "- b" in result

    def test_render_template_syntax_error(self, tmp_config_dir):
        """Test error on template syntax error."""
        template_file = tmp_config_dir / "bad.txt.j2"
        template_file.write_text("{% for item in items %}\nno endfor")

        renderer = Jinja2Renderer(tmp_config_dir)
        with pytest.raises(TemplateRenderError, match="syntax error"):
            renderer.render_file(Path("bad.txt.j2"), {})

    def test_render_string(self, tmp_config_dir):
        """Test rendering a template string."""
        renderer = Jinja2Renderer(tmp_config_dir)
        result = renderer.render_string("Value: {{ x }}", {"x": 42})
        assert result == "Value: 42"

    def test_render_template_not_found(self, tmp_config_dir):
        """Test error when template file doesn't exist."""
        renderer = Jinja2Renderer(tmp_config_dir)
        with pytest.raises(TemplateRenderError, match="not found"):
            renderer.render_file(Path("nonexistent.j2"), {})
