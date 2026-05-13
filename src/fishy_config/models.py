"""Data models for fishy-config core."""

from enum import Enum
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

DEFAULT_SKIP_PATTERNS = ["*.md", ".git", ".gitkeep"]


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


class RenderRequest(BaseModel):
    """Canonical request payload for high-level rendering."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    config_dir: Path
    dest_dir: Path
    context: dict[str, Any] = Field(default_factory=dict)
    typed_context: BaseModel | None = None
    context_model_type: type[BaseModel] | None = None
    plugins: list[Any] = Field(default_factory=list)
    preserve_structure: bool = True
    skip_patterns: list[str] | None = None
    template_extension: str = ".j2"
    strict_undefined: bool = False
    dry_run: bool = False
    overwrite: bool = False
    clean_dest: bool = False


class RenderOptions(BaseModel):
    """Configuration for rendering operation."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    config_dir: Path
    dest_dir: Path
    context: ContextConfig
    context_type: type[BaseModel] | None = None
    typed_context: BaseModel | None = None
    preserve_structure: bool = True
    skip_patterns: list[str] = Field(default_factory=lambda: DEFAULT_SKIP_PATTERNS.copy())
    plugins: list[Any] = Field(default_factory=list)
    strict_undefined: bool = False
    dry_run: bool = False
    template_extension: str = ".j2"
    overwrite: bool = False
    clean_dest: bool = False


class RenderError(BaseModel):
    """Single rendering error."""

    file: str
    error_type: Literal["template", "io", "validation", "plugin"]
    message: str
    line_number: int | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class RenderResult(BaseModel):
    """Result of a render operation."""

    config_dir: Path | None = None
    dest_dir: Path | None = None
    files_rendered: list[str] = Field(default_factory=list)
    files_copied: list[str] = Field(default_factory=list)
    errors: list[RenderError] = Field(default_factory=list)
    duration_ms: float = 0.0
    success: bool = True
    artifacts: list[str] = Field(default_factory=list)

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
