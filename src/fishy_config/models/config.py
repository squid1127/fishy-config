"""Main config model with engine configuration"""

from pydantic import BaseModel, Field, field_validator
from pathlib import Path
from typing import Any

from .fishy_types import ContextValue
from .enums import ArtifactType
from .artifact import BuildArtifact

class EngineConfig(BaseModel):
    """Configuration for the templating engine."""

    source_dir: Path = Field(..., description="The directory containing the source config files.")
    output_dir: Path = Field(
        ..., description="The directory where the rendered config files will be saved."
    )

    context: dict[str, ContextValue] = Field(
        default_factory=dict, description="The context data for rendering templates."
    )
    
    artifacts: list[BuildArtifact] = Field(
        default_factory=list, description="List of build artifacts to produce after rendering."
    )

    clean_output: bool = Field(
        default=False, description="Whether to clean the output directory before rendering."
    )
    overwrite: bool = Field(
        default=False, description="Whether to overwrite existing files in the output directory."
    )
    metadata_suffix: str = Field(
        default=".meta.yaml", description="Suffix for metadata files in the source directory."
    )
    template_suffix: str = Field(
        default=".j2", description="Suffix for Jinja2 template files in the source directory."
    )
    internal_template_namespace: str = Field(
        default="_build", description="Namespace in the Jinja2 context for internal metadata and variables."
    )

    @field_validator("source_dir", "output_dir")
    def validate_directories(cls, value: Path) -> Path:
        if not value.is_dir():
            raise ValueError(f"{value} is not a valid directory.")
        return value
