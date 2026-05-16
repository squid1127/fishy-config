"""Models representing files and directories"""

from pydantic import BaseModel, Field
from pathlib import Path
from dataclasses import dataclass, field

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
        description="Whether the provided path should be treated as absolute. If true, the path will be realtive to the output directory. If false, the path will be treated as relative itself.",
    )
    output_name: str | None = Field(
        default=None,
        description="Optional new name for the file when rendered.",
    )
    encoding: str | None = Field(
        default=None,
        description="Optional encoding to use when reading/writing this file. Defaults to UTF-8.",
    )
    priority: int = Field(
        default=0,
        description="The priority of the file. Higher priority files are processed first.",
    )

    def summary(self) -> str:
        """Return a summary of the metadata for logging purposes."""
        summary = ""
        if self.skip:
            summary += "skip, "
        if self.priority != 0:
            summary += f"priority={self.priority}, "
        return summary


class DirectoryVariantMode(BaseModel):
    """Model representing a directory's variant mode configuration."""

    key: str = Field(
        ...,
        description="The context key to evaluate for this variant. This will be mapped to a subdirectory name based on the provided mapping or the value itself.",
    )
    mapping: dict[str, str] | None = Field(
        default=None, description="Optional mapping of context values to subdirectory names."
    )
    skip_if_missing: bool = Field(
        default=False,
        description="Whether to skip the directory if the context key is missing or evaluates to None.",
    )


class DirectoryMetadata(FileMetadata):
    """Metadata for an queued directory."""

    variant: DirectoryVariantMode | None = Field(
        default=None, description="Optional configuration for directory variants based on context."
    )
    flatten: bool = Field(
        default=False, description="Whether to flatten the directory structure when rendering."
    )

    def summary(self) -> str:
        """Return a summary of the directory metadata for logging purposes."""
        summary = super().summary()
        if self.variant:
            summary += f"variant key={self.variant.key}, "
            if self.variant.mapping:
                summary += f"variant mapping={self.variant.mapping}, "
        if self.flatten:
            summary += "flatten, "
        return summary


class QueuedFile(BaseModel):
    """Model representing a file that is queued for copying/rendering."""

    source: Path = Field(..., description="The source path of the file.")
    relative_path: Path = Field(
        ..., description="The relative path of the file from the source directory."
    )
    file_type: FileType = Field(
        ..., description="The type of the file (template, metadata, raw, other)."
    )
    metadata: FileMetadata = Field(..., description="The metadata associated with this file.")


@dataclass(frozen=True, slots=True)
class FileResult:
    """Model representing the result of processing an queued file, including the rendered content and any errors."""

    queued_file: QueuedFile
    rendered_content: str | None = None
    error: Exception | None = None
