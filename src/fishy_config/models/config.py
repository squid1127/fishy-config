"""Main config model with engine configuration"""

from pydantic import BaseModel, Field, field_validator
from pathlib import Path
from typing import Any

from .constants import ContextValue
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
    skip_patterns: list[str] = Field(
        default_factory=list, description="List of glob patterns to match files that should be skipped during rendering."
    )

    @field_validator("source_dir", "output_dir")
    def validate_directories(cls, value: Path) -> Path:
        if not value.is_dir():
            raise ValueError(f"{value} is not a valid directory.")
        return value
    
    def context_get(self, key: str, separator: str = ".") -> Any:
        """Get a value from the context using a dot-separated key."""
        keys = key.split(separator)
        value = self.context
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            elif isinstance(value, list):
                try:
                    index = int(k)
                    value = value[index]
                except (ValueError, IndexError):
                    raise KeyError(f"Key '{key}' not found in context.")
            else:
                raise KeyError(f"Key '{key}' not found in context")
        return value