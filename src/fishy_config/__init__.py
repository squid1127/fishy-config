"""A fishy python tool to make managing config files easier using a simple templating system."""

__version__ = "0.1.0"

from .models.exceptions import (
    FishyConfigError,
    ContextLoadError,
    TemplateRenderError,
    InvalidMetadataError,
    FileIOError,
)
from .models.fishy_types import ContextValue

__all__ = [
    "FishyConfigError",
    "ContextLoadError",
    "TemplateRenderError",
    "InvalidMetadataError",
    "FileIOError",
    "ContextValue",
]
