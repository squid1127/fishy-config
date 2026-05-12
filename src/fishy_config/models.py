"""Data models for fishy-config core."""

from enum import Enum
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MergeStrategy(str, Enum):
    """Strategy for merging context sources."""

    DEEP = "deep"  # Recursively merge dicts
    SHALLOW = "shallow"  # Only merge top level
    REPLACE = "replace"  # Runtime data replaces YAML entirely


class ContextSource(BaseModel):
    """Single context source (e.g., YAML file)."""

    path: Path
    merge_strategy: MergeStrategy = MergeStrategy.DEEP
    required: bool = False


class ContextConfig(BaseModel):
    """Merged context for template rendering."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    data: dict[str, Any] = Field(default_factory=dict)
    sources: list[ContextSource] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)


class RenderOptions(BaseModel):
    """Configuration for rendering operation."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    config_dir: Path
    dest_dir: Path
    context: ContextConfig
    preserve_structure: bool = True
    skip_patterns: list[str] = Field(default_factory=lambda: ["*.md", ".git", ".gitkeep"])
    strict_undefined: bool = False
    dry_run: bool = False
    template_extension: str = ".j2"
    overwrite: bool = False


class RenderError(BaseModel):
    """Single rendering error."""

    file: str
    error_type: Literal["template", "io", "validation", "plugin"]
    message: str
    line_number: int | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class RenderResult(BaseModel):
    """Result of a render operation."""

    files_rendered: list[str] = Field(default_factory=list)
    files_copied: list[str] = Field(default_factory=list)
    errors: list[RenderError] = Field(default_factory=list)
    duration_ms: float = 0.0
    success: bool = True

    @property
    def total_files(self) -> int:
        """Total files processed (rendered + copied)."""
        return len(self.files_rendered) + len(self.files_copied)

    def add_error(
        self,
        file: str,
        error_type: Literal["template", "io", "validation", "plugin"],
        message: str,
        line_number: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Add an error to the result."""
        self.errors.append(
            RenderError(
                file=file,
                error_type=error_type,
                message=message,
                line_number=line_number,
                details=details or {},
            )
        )
        self.success = False
