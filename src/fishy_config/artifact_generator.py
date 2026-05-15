"""Artifact generator for producing build artifacts based on the configuration."""

from pathlib import Path
import shutil
from typing import Iterator
from logging import getLogger
import subprocess
import zipfile

from .models.config import EngineConfig
from .models.artifact import BuildArtifact, ArtifactResult
from .models.exceptions import ArtifactGenerationError
from .models.enums import ArtifactType
from .renderer import TemplateRenderer

logger = getLogger(__name__)


class ArtifactGenerator:
    """Generates build artifacts based on the EngineConfig."""

    def __init__(self, config: EngineConfig, renderer: TemplateRenderer):
        self.config = config
        self.renderer = renderer

    def generate_artifacts(
        self, artifacts: Iterator[BuildArtifact]
    ) -> Iterator[ArtifactResult]:
        """Generate build artifacts based on the list or iterator of BuildArtifact configurations, yielding ArtifactResult objects with the results of each generation attempt."""
        for artifact in artifacts:
            try:
                if artifact.artifact_type == ArtifactType.CUSTOM_BUILDER:
                    yield self._run_custom_builder(artifact)
                else:
                    logger.warning(
                        f"Unsupported artifact type {artifact.artifact_type} for artifact at {artifact.path}"
                    )
                    yield ArtifactResult(
                        artifact=artifact,
                        generated_path=None,
                        error=ArtifactGenerationError(
                            f"Unsupported artifact type {artifact.artifact_type} for artifact at {artifact.path}"
                        ),
                    )

            except Exception as e:
                logger.exception(f"Failed to generate artifact at {artifact.path}")
                yield ArtifactResult(
                    artifact=artifact,
                    generated_path=None,
                    error=e,
                )

    def _render_custom_builder_command(self, artifact: BuildArtifact) -> str:
        """Render the command for a custom builder artifact using the Jinja2 context."""
        if not artifact.command:
            raise ArtifactGenerationError(
                f"Custom builder artifact at {artifact.path} is missing a command."
            )

        logger.debug(
            f"Rendering command for custom builder artifact at {artifact.path} with template: {artifact.command}"
        )
        try:
            context = self.config.context.copy()
            context[self.config.internal_template_namespace] = {
                "artifact": artifact,
                "config": self.config,
            }
            rendered_command = self.renderer.render(artifact.command, context)
            return rendered_command
        except Exception as e:
            logger.exception(
                f"Failed to render command for custom builder artifact at {artifact.path}"
            )
            raise ArtifactGenerationError(
                f"Failed to render command for custom builder artifact at {artifact.path}: {str(e)}"
            ) from e

    def _run_custom_builder(self, artifact: BuildArtifact) -> ArtifactResult:
        """Run a custom builder command to generate an artifact, using the rendered content as context."""
        if not artifact.command:
            raise ArtifactGenerationError(
                f"Custom builder artifact at {artifact.path} is missing a command."
            )
        if not artifact.overwrite:
            raise ArtifactGenerationError(
                f"Custom builder artifact at {artifact.path} must have overwrite=True to run the builder command."
            )
        command = self._render_custom_builder_command(artifact)

        logger.info(
            f"Running custom builder for artifact at {artifact.path} with command: {command}"
        )
        try:
            result = subprocess.run(command, shell=True, check=True, cwd=artifact.path)
            logger.info(f"Custom builder for artifact at {artifact.path} completed successfully.")
            
            return ArtifactResult(
                artifact=artifact,
                generated_path=artifact.path,
                output=str(result.stdout) + str(result.stderr),
            )
        except subprocess.CalledProcessError as e:
            logger.exception(f"Custom builder command failed for artifact at {artifact.path}")
            raise ArtifactGenerationError(
                f"Custom builder command failed for artifact at {artifact.path}: {str(e)}"
            ) from e

    def _generate_zip(self, artifact: BuildArtifact) -> ArtifactResult:
        """Generate a zip archive artifact from the rendered files."""

        if artifact.path.exists() and not artifact.overwrite:
            logger.warning(
                f"Artifact path {artifact.path} already exists and overwrite is False. Skipping zip generation."
            )
        else:
            try:
                with zipfile.ZipFile(artifact.path, "w", zipfile.ZIP_DEFLATED) as zipf:
                    for file in self.config.output_dir.rglob("*"):
                        if file.is_file():
                            zipf.write(file, file.relative_to(self.config.output_dir))

                logger.info(f"Zip archive artifact generated successfully at {artifact.path}")

            except Exception as e:
                logger.exception(f"Failed to generate zip archive artifact at {artifact.path}")
                raise ArtifactGenerationError(
                    f"Failed to generate zip archive artifact at {artifact.path}: {str(e)}"
                ) from e

        return ArtifactResult(
            artifact=artifact,
            generated_path=artifact.path,
        )

    def _copy_directory(self, artifact: BuildArtifact) -> ArtifactResult:
        """Copy the rendered output directory to the artifact path."""
        try:
            if artifact.path.exists():
                if not artifact.overwrite:
                    logger.warning(
                        f"Artifact path {artifact.path} already exists and overwrite is False. Skipping directory copy."
                    )
                    return ArtifactResult(
                        artifact=artifact,
                        generated_path=artifact.path,
                    )

                shutil.rmtree(artifact.path)
                logger.info(
                    f"Existing artifact path {artifact.path} removed before copying directory artifact."
                )

            shutil.copytree(self.config.output_dir, artifact.path)
            logger.info(f"Directory artifact generated successfully at {artifact.path}")
            return ArtifactResult(
                artifact=artifact,
                generated_path=artifact.path,
            )
        except Exception as e:
            logger.exception(f"Failed to generate directory artifact at {artifact.path}")
            raise ArtifactGenerationError(
                f"Failed to generate directory artifact at {artifact.path}: {str(e)}"
            ) from e
