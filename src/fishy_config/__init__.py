"""fishy-config public package API.

This package exposes the main build entrypoint, CLI app, logging helpers,
core exception types, data models, and utilities for custom implementations.
"""

__version__ = "0.1.0"

# CLI and build
from .cli import app
from .builder import build

# Logging
from .log import disable_logging, enable_logging, get_logger

# Core classes for custom implementations
from .renderer import TemplateRenderer
from .scanner import SourceTreeScanner
from .output import OutputBuilder
from .artifact_generator import ArtifactGenerator

# Data models and configuration
from .models.config import EngineConfig, OutputConfig
from .models.artifact import BuildArtifact, ArtifactResult
from .models.files import (
    QueuedFile,
    FileMetadata,
    DirectoryMetadata,
    FileResult,
    FailedFile,
)
from .models.constants import ContextValue
from .models.enums import FileType, ArtifactType

# Exceptions
from .models.exceptions import (
    ContextLoadError,
    FileIOError,
    FishyConfigError,
    InvalidFileSyntaxError,
    InvalidMetadataError,
    ScanError,
    TemplateRenderError,
    TemplateUndefinedError,
    ArtifactGenerationError,
)

__all__ = [
    # CLI and build
    "app",
    "build",
    # Logging
    "disable_logging",
    "enable_logging",
    "get_logger",
    # Core classes
    "ArtifactGenerator",
    "OutputBuilder",
    "SourceTreeScanner",
    "TemplateRenderer",
    # Configuration models
    "EngineConfig",
    "OutputConfig",
    # Data models
    "ArtifactResult",
    "BuildArtifact",
    "ContextValue",
    "DirectoryMetadata",
    "FailedFile",
    "FileMetadata",
    "FileResult",
    "QueuedFile",
    # Enums
    "ArtifactType",
    "FileType",
    # Exceptions
    "ArtifactGenerationError",
    "ContextLoadError",
    "FileIOError",
    "FishyConfigError",
    "InvalidFileSyntaxError",
    "InvalidMetadataError",
    "ScanError",
    "TemplateRenderError",
    "TemplateUndefinedError",
]
