"""Tests for renderer module."""

import pytest
from unittest.mock import Mock
from fishy_config.renderer import TemplateRenderer
from fishy_config.models.config import EngineConfig


@pytest.fixture
def mock_config():
    """Create a mock EngineConfig."""
    config = Mock(spec=EngineConfig)
    config.context = {"test_var": "test_value"}
    return config


@pytest.fixture
def renderer(mock_config):
    """Create a TemplateRenderer instance."""
    return TemplateRenderer(mock_config)


def test_renderer_init(renderer, mock_config):
    """Test renderer initialization."""
    assert renderer.config == mock_config


def test_renderer_has_required_methods(renderer):
    """Test renderer has required methods."""
    assert hasattr(renderer, "render")
    assert callable(renderer.render)


def test_render_simple_template(renderer):
    """Test rendering a simple template."""
    template = "Hello {{ name }}"
    context = {"name": "World"}
    result = renderer.render(template, context, None)
    assert result == "Hello World"


def test_render_with_variables(renderer):
    """Test rendering with context variables."""
    template = "Value: {{ value }}"
    context = {"value": 42}
    result = renderer.render(template, context, None)
    assert result == "Value: 42"
