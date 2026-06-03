"""Simplified build function for fishy_config."""

from .models.config import EngineConfig, BuildArtifact
from .models.artifact import ArtifactResult
from .scanner import SourceTreeScanner
from .artifact_generator import ArtifactGenerator
from .renderer import TemplateRenderer
from .output import OutputBuilder


def build(config: EngineConfig) -> list[ArtifactResult]:
    """Build the project based on the provided EngineConfig.

    Args:
        config (EngineConfig): The configuration for the build process.
    """
    renderer = TemplateRenderer(config)
    scanner = SourceTreeScanner(config, renderer)
    artifact_generator = ArtifactGenerator(config, renderer)
    output_generator = OutputBuilder(config, renderer)

    # Scan source directory and generate artifacts
    queued_files = scanner.scan_and_raise()

    # Generate output files
    output_generator.generate(list(queued_files), sort=True)
    artifacts = artifact_generator.generate_artifacts(config.artifacts)
    return list(artifacts)
