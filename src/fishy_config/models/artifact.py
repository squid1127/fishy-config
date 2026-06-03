"""Build artifact model for representing build artifacts in the configuration."""

from pydantic import BaseModel, Field, model_validator
from pathlib import Path
from dataclasses import dataclass, field

from .enums import ArtifactType


class BuildArtifact(BaseModel):
    """Model representing a build artifact, to generate a manifest of rendered files and their metadata."""

    id: str = Field(..., description="A unique identifier for the artifact.")
    artifact_type: ArtifactType = Field(
        ..., description="The type of the artifact (zip archive, directory, custom builder)."
    )
    path: Path = Field(
        ..., description="The path to the generated artifact. If custom builder, this is the CWD"
    )
    command: str | None = Field(
        None,
        description="The command to run to build the artifact, if artifact_type is CUSTOM_BUILDER, using a jinja2 template",
    )
    overwrite: bool = Field(
        True,
        description="Whether to overwrite the artifact if it already exists. Defaults to True. Must be True for CUSTOM_BUILDER artifacts.",
    )
    primary: bool = Field(
        False,
        description="Whether this artifact is the primary artifact for the build. This is used to determine which artifact to return as the main result of the build process when multiple artifacts are defined.",
    )
    
    @model_validator(mode="after") # type: ignore
    def validate_artifact(self) -> BuildArtifact:
        """Validate that the artifact configuration is complete and consistent based on the artifact type."""
        if self.artifact_type == ArtifactType.CUSTOM_BUILDER:
            if not self.command:
                raise ValueError(
                    f"Custom builder artifact at {self.path} is missing a command."
                )
            if not self.overwrite:
                raise ValueError(
                    f"Custom builder artifact at {self.path} must have overwrite=True to run the builder command."
                )
        elif self.command is not None:
            raise ValueError(
                f"Only custom builder artifacts can have a command. Artifact at {self.path} has type {self.artifact_type} but defines a command."
            )
        return self


@dataclass(frozen=True, slots=True)
class ArtifactResult:
    """Model representing the result of generating a build artifact, including the path to the generated artifact and any errors."""

    artifact: BuildArtifact
    generated_path: Path | None = None
    error: Exception | None = None
    output: str | None = None