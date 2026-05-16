"""Models for the fishy-config CLI."""

from dataclasses import dataclass, field
from enum import Enum
from pydantic import BaseModel, Field, field_validator
from pathlib import Path

from ..models.artifact import BuildArtifact


class ContextSourceType(Enum):
    """Enumeration of context source types."""

    FILE = "file"
    ENV = "env"
    ARG = "arg"
    PRESET = "preset"
    DEFAULTS = "defaults"


@dataclass
class ContextSource:
    """Represents a source of context for the CLI."""

    data: dict = field(default_factory=dict)
    source_type: ContextSourceType = ContextSourceType.FILE
    priority: int = 0


class BuildFlowConfig(BaseModel):
    """Model representing the build flow configuration for a project."""

    artifacts: list[BuildArtifact] = Field(
        default_factory=list,
        description="A list of build artifacts to generate when using this build flow.",
    )
    dry_run: bool = Field(
        default=False,
        description="If True, the build flow will simulate the generation of artifacts without actually creating any files. Enabling this option will dump the render diffs to the console for review.",
    )
    presets: list[str] = Field(
        default_factory=list,
        description="A list of context presets to apply when using this build flow.",
    )


class BuildConfig(BaseModel):
    """Model representing the build configuration for a project"""

    source: Path = Field(
        ...,
        description="The source (templates) directory.",
        examples=[Path("src"), Path("templates")],
    )
    output: Path = Field(
        ...,
        description="The destination (output) directory.",
        examples=[Path("dist"), Path("output")],
    )
    flows: dict[str, BuildFlowConfig] = Field(
        default_factory=dict,
        description="A dictionary of named build flows, where each flow is a BuildFlowConfig object.",
    )
    context: dict = Field(
        default_factory=dict,
        description="A json schema-like dictionary representing the context's structure and default values.",
    )
    presets: dict[str, dict] = Field(
        default_factory=dict,
        description="A dictionary of named context presets, where each preset is a dictionary of context values.",
    )
    artifacts: list[BuildArtifact] = Field(
        default_factory=list,
        description="A list of build artifacts to generate after rendering the templates.",
    )
    clean_output: bool = Field(
        default=False,
        description="If True, the output directory will be cleaned before generating new artifacts.",
    )
    overwrite: bool = Field(
        default=False,
        description="If True, existing files in the output directory will be overwritten.",
    )
    skip_patterns: list[str] = Field(
        default_factory=list,
        description="Glob patterns for source files or directories to skip during scanning.",
    )

    @field_validator("source", "output")
    def validate_paths(cls, v: Path) -> Path:
        """Validate that the provided paths are valid directories."""
        if not v.is_dir():
            if v.exists():
                raise ValueError(f"Path {v} is not a valid directory.")
            else:
                v.mkdir(parents=True, exist_ok=True)
        if v.is_absolute():
            raise ValueError(f"Path {v} must be relative to the build context.")
        return v
