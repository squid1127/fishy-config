"""Tests for exceptions module."""

import pytest
from fishy_config.models.exceptions import (
    FishyConfigError,
    TemplateRenderError,
    ContextLoadError,
    InvalidMetadataError,
)


def test_fishy_config_error():
    """Test FishyConfigError is raised correctly."""
    with pytest.raises(FishyConfigError):
        raise FishyConfigError("Test error")


def test_template_render_error():
    """Test TemplateRenderError is raised correctly."""
    with pytest.raises(TemplateRenderError):
        raise TemplateRenderError("Template error")


def test_context_load_error():
    """Test ContextLoadError is raised correctly."""
    with pytest.raises(ContextLoadError):
        raise ContextLoadError("Context load error")


def test_invalid_metadata_error():
    """Test InvalidMetadataError is raised correctly."""
    with pytest.raises(InvalidMetadataError):
        raise InvalidMetadataError("Invalid metadata")


def test_exception_inheritance():
    """Test exception inheritance."""
    assert issubclass(TemplateRenderError, FishyConfigError)
    assert issubclass(ContextLoadError, FishyConfigError)
    assert issubclass(InvalidMetadataError, FishyConfigError)
