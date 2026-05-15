"""fishy-config public package API.

This package exposes the main build entrypoint, CLI app, logging helpers, and
the core exception and context types used by the project.
"""

__version__ = "0.1.0"

from .cli import app
from .log import disable_logging, enable_logging, get_logger
from .models.exceptions import (
    ContextLoadError,
    FileIOError,
    FishyConfigError,
    InvalidFileSyntaxError,
    InvalidMetadataError,
    ScanError,
    TemplateRenderError,
    TemplateUndefinedError,
)
from .models.constants import ContextValue
from .builder import build

__all__ = [
    "app",
    "build",
    "ContextLoadError",
    "ContextValue",
    "disable_logging",
    "enable_logging",
    "FileIOError",
    "FishyConfigError",
    "get_logger",
    "InvalidFileSyntaxError",
    "InvalidMetadataError",
    "ScanError",
    "TemplateRenderError",
    "TemplateUndefinedError",
]
