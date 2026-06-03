"""Models for the fishy-config CLI."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field, field_validator, model_validator
from pathlib import Path

from ..models.artifact import BuildArtifact
from ..models.config import OutputConfig
from .migrations import VERSION_CURRENT


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


class BuildConfig(BaseModel):
    """Model representing the build configuration for a project"""

    version: int = Field(
        default=VERSION_CURRENT,
        description="The version of the build configuration schema",
    )

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
    context: dict = Field(
        default_factory=dict,
        description="A json schema-like dictionary representing the context's structure and default values.",
    )
    context_file: Path | None = Field(
        None,
        description="An optional path to a YAML or JSON file containing context schema and default values. If provided, this file will override the 'context' field in the configuration.",
    )
    presets: dict[str, dict[str, Any]] = Field(
        default_factory=dict,
        description="A dictionary of named context presets, where each preset is a dictionary of context values.",
    )
    artifacts: list[BuildArtifact] = Field(
        default_factory=list,
        description="A list of build artifacts to generate after rendering the templates.",
    )
    options: OutputConfig = Field(
        default_factory=OutputConfig,
        description="Options for controlling the output generation and rendering process.",
    )

    @field_validator("source", "output")
    @classmethod
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
    

    @model_validator(mode="before")
    @classmethod
    def transform_artifacts(cls, values: dict[str, Any]) -> dict[str, Any]:
        """Transform artifacts from a dictionary to a list if necessary."""
        artifacts = values.get("artifacts", [])
        if isinstance(artifacts, dict):
            artifacts_list = []
            for artifact_id, artifact_data in artifacts.items():
                if not isinstance(artifact_data, dict):
                    raise ValueError(f"Artifact data for '{artifact_id}' must be a dictionary.")
                artifact_data["id"] = artifact_id
                artifacts_list.append(BuildArtifact(**artifact_data))
            values["artifacts"] = artifacts_list
        return values