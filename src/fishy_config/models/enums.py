"""Enums used across the project."""

from enum import Enum, auto

class FileType(Enum):
    """Enum representing different types of files."""
    TEMPLATE = auto()
    METADATA = auto()
    RAW = auto()
    OTHER = auto()
    
class ArtifactType(Enum):
    """Enum representing different types of build artifacts."""
    ZIP_ARCHIVE = "zip"
    DIRECTORY = "directory"
    CUSTOM_BUILDER = "custom_builder"