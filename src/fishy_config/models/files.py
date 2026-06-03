"""Models representing files and directories"""

from pydantic import BaseModel, Field
from pathlib import Path
from dataclasses import dataclass, field as dataclass_field

from .enums import FileType


class FileMetadata(BaseModel):
    """Metadata for an queued file."""

    skip: bool = Field(default=False, description="Whether to skip processing this file.")
    path: Path | None = Field(
        default=None,
        description="Optional new path for the file when rendered. Use a '/' prefix for absolute paths or no prefix for relative paths.",
    )
    path_absolute: bool = Field(
        default=False,
        description="Whether the provided path should be treated as absolute. If true, the path will be treated as absolute relative to the output directory. If false, the path will be treated as relative itself.",
    )
    name: str | None = Field(
        default=None,
        description="Optional new name for the file when rendered.",
        alias="output_name",
    )
    priority: int = Field(
        default=0,
        description="The priority of the file. Higher priority files are processed first.",
    )

    def summary(self) -> str:
        """Return a summary of the metadata for logging purposes."""
        summary = ""
        if self.skip:
            summary += "skip "
        if self.priority != 0:
            summary += f"priority={self.priority} "
        return summary


class DirectoryMetadata(FileMetadata):
    """Metadata for an queued directory."""

    variant: str | None = Field(
        default=None,
        description="Match and promote the subdirectory with this name during scanning.",
    )
    variant_skip_if_missing: bool = Field(
        default=False,
        description="Whether to skip the directory if the specified variant is not found. If false, an error will be raised if the variant is not found.",
    )
    flatten: bool = Field(
        default=False, description="Whether to flatten the directory structure when rendering."
    )

    def summary(self) -> str:
        """Return a summary of the directory metadata for logging purposes."""
        summary = super().summary()
        if self.variant:
            summary += "variant"
            if self.variant_skip_if_missing:
                summary += "(skip if missing)"
            summary += f"={self.variant} "
        if self.flatten:
            summary += "flatten "
        return summary


@dataclass(frozen=True, slots=True)
class ScanItem:
    """Model representing a path that is scanned, including its source path and relative path from the source directory."""

    source: Path
    relative_path: Path


@dataclass(frozen=True, slots=True)
class QueuedFile(ScanItem):
    """Dataclass representing a file that is queued for copying/rendering."""

    file_type: FileType
    metadata: FileMetadata = dataclass_field(default_factory=FileMetadata)


@dataclass(frozen=True, slots=True)
class FailedFile(ScanItem):
    """Model representing a file that encountered an error during scanning, including the error message."""

    error: Exception


@dataclass(frozen=True, slots=True)
class FileResult:
    """Dataclass representing the result of processing an queued file, including the rendered content and any errors."""

    queued_file: QueuedFile
    rendered_content: str | None = None
    error: Exception | None = None
