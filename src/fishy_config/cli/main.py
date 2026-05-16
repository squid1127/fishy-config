"""Main executor for fishy-config CLI."""

import pydantic
import rich
import typer
from pathlib import Path
import yaml

from .context import ContextManager, schema_as_defaults
from .models import BuildConfig, ContextSource, ContextSourceType, BuildFlowConfig
from .exceptions import InvalidContextError, InvalidContextSchemaError, InvalidBuildFileError

from ..models.config import EngineConfig
from ..models.files import QueuedFile
from ..log import get_logger
from ..scanner import SourceTreeScanner
from ..renderer import TemplateRenderer
from ..artifact_generator import ArtifactGenerator
from ..output import OutputBuilder

logger = get_logger(__name__)


class FishyConfigCLI:
    """Main executor for fishy-config CLI."""

    def __init__(
        self,
        build_file: Path | None,
        presets: list[str] | None = None,
        flow: str | None = None,
        interactive: bool = False,
    ):
        self.build_file = build_file
        self.context_manager = ContextManager()
        self.presets = presets or []
        self.flow = flow
        self.interactive = interactive
        self._config: BuildConfig | None = None
        self.console = rich.console.Console()

    def read_build_file(self) -> None:
        """Read the build configuration file and return its path."""
        if not self.build_file:
            logger.info(
                "Using default build configuration file 'build.yaml' in the current directory."
            )
            self.build_file = Path("build.yaml")

        if not self.build_file.exists():
            raise InvalidBuildFileError(
                f"Build configuration file {self.build_file} does not exist."
            )

        try:
            text = self.build_file.read_text()
            config_data = yaml.safe_load(text)
            if not isinstance(config_data, dict):
                raise InvalidBuildFileError(
                    f"Build configuration file {self.build_file} is not a valid YAML mapping."
                )
            self._config = BuildConfig(**config_data)
        except yaml.YAMLError as e:
            raise InvalidBuildFileError(
                f"Failed to parse build configuration file {self.build_file}: {e}"
            ) from e
        except pydantic.ValidationError as e:
            raise InvalidBuildFileError(
                f"Build configuration file {self.build_file} is invalid: {e}"
            ) from e
        self._apply_build_config_to_context()
        logger.info(f"Successfully read build configuration from {self.build_file}")

    def add_context_source(
        self, source: dict, source_type: ContextSourceType, priority: int = 0
    ) -> None:
        """Add a context source to the context manager."""
        self.context_manager.add_source(
            ContextSource(data=source, source_type=source_type, priority=priority)
        )
        logger.info(f"Added context source of type {source_type} with priority {priority}.")

    def run(self) -> None:
        """Run the fishy-config CLI with the provided build configuration."""
        logger.debug(f"Validating {self.context_manager.context} against schema {self.context_manager.schema}")
        try:
            self.context_manager.validate_context()
        except InvalidContextSchemaError as e:
            raise InvalidContextError(f"Context validation failed: {e}") from e

        self.console.print("[green]Successfully validated context against schema.[/green]")
        engine_config = self._generate_engine_config()
        renderer = TemplateRenderer(engine_config)
        scanner = SourceTreeScanner(engine_config, renderer)

        with self.console.status("[bold green]Scanning source directory...[/bold green]") as status:
            queued_files = []
            for queued_file in scanner.scan():
                queued_files.append(queued_file)
                logger.debug(f"Queued file: {queued_file.source} -> {queued_file.relative_path}")
                status.update(
                    f"[blue]({len(queued_files)})[/blue] [green]Found {queued_file.source}[/green]"
                )

        self._queued_file_summary(queued_files)
        if self.active_flow and self.active_flow.dry_run:
            self.console.print("[yellow]Dry run mode enabled. No files will be generated.[/yellow]")
            return

        if self.interactive and not self.console.input(
            "[bold yellow]Proceed with file generation? (y/n): [/bold yellow]"
        ).strip().lower().startswith("y"):
            self.console.print("[red]Aborting file generation.[/red]")
            return

        output = OutputBuilder(engine_config, renderer)
        results = []
        with self.console.status("[bold green]Generating output files...[/bold green]") as status:
            for result in output.generate(queued_files):
                results.append(result)
                if result.error:
                    logger.error(
                        f"Error generating file {result.queued_file.source}: {result.error}"
                    )
                    self.console.print(
                        f"[red]Error generating file {result.queued_file.source}: {result.error}[/red]"
                    )
                else:
                    logger.debug(
                        f"Successfully generated file {result.queued_file.source} -> {result.queued_file.relative_path}"
                    )
                    status.update(
                        f"[blue]({len(results)}/{len(queued_files)})[/blue] [green]Generated {result.queued_file.relative_path}[/green]"
                    )

        self.console.print(
            f"[bold green]Successfully generated {len([r for r in results if not r.error])} files.[/bold green]"
        )

        artifact_generator = ArtifactGenerator(engine_config, renderer)
        artifact_results = []
        with self.console.status("[bold green]Generating artifacts...[/bold green]") as status:
            for artifact_result in artifact_generator.generate_artifacts(engine_config.artifacts):
                artifact_results.append(artifact_result)
                if artifact_result.error:
                    logger.error(
                        f"Error generating artifact {artifact_result.artifact.path}: {artifact_result.error}"
                    )
                    self.console.print(
                        f"[red]Error generating artifact {artifact_result.artifact.path}: {artifact_result.error}[/red]"
                    )
                else:
                    logger.debug(
                        f"Successfully generated artifact {artifact_result.artifact.path} -> {artifact_result.generated_path}"
                    )
                    status.update(
                        f"[blue]({len(artifact_results)}/{len(engine_config.artifacts)})[/blue] [green]Generated artifact {artifact_result.generated_path}[/green]"
                    )

        self.console.print(
            f"[bold green]Successfully generated {len([a for a in artifact_results if not a.error])} artifacts.[/bold green]"
        )
        
        results_failed =  len([r for r in results if r.error])

        self.console.print("[bold green]Build process completed successfully.\nOverview:[/bold green]")
        self.console.print(f"[bold blue]{len(results)} files [/bold blue]")
        self.console.print(f"[bold green]{len(results) - results_failed} successful[/bold green]")
        self.console.print(f"[bold red]{results_failed} failed[/bold red]")
        self.console.print(f"[bold blue]Output directory: {engine_config.output_dir}[/bold blue]")
        for artifact_result in artifact_results:
            if artifact_result.error:
                self.console.print(
                    f"[red]Artifact: {artifact_result.artifact.path} failed with error: {artifact_result.error}[/red]"
                )
            else:
                self.console.print(f"[green]Artifact: {artifact_result.generated_path}[/green]")

    def _apply_build_config_to_context(self) -> None:
        """Apply the build configuration to the context manager."""
        context = self.config.context
        if self.config.context_file:
            file_context = self._read_context_file()
            if file_context and self.config.context:
                logger.warning(
                    "Both 'context' and 'context_file' are provided in the build configuration. Only 'context_file' will be used and 'context' will be ignored."
                )
            else:
                logger.info(f"Applied context from: {self.config.context_file}")
            context = file_context or context
        defaults = schema_as_defaults(context)
        logger.debug(f"Extracted context schema: {context}")
        logger.debug(f"Extracted default context values from schema: {defaults}")
        self.context_manager.set_schema(context)
        self.context_manager.add_source(
            ContextSource(
                data=defaults,
                source_type=ContextSourceType.DEFAULTS,
                priority=1,
            )
        )

        for preset, data in self.config.presets.items():
            if preset not in self.presets:
                logger.debug(
                    f"Skipping preset {preset} as it is not in the specified presets list."
                )
                continue
            self.context_manager.add_source(
                ContextSource(data=data, source_type=ContextSourceType.PRESET, priority=10)
            )
            logger.info(f"Applied preset {preset} to context.")
        logger.debug(f"Final context after applying build configuration: {self.context_manager.context}")
            
    def _read_context_file(self) -> dict | None:
        """Read the context schema and defaults from the specified context file."""
        if not self.config.context_file:
            return None
        if not self.config.context_file.exists():
            raise InvalidBuildFileError(
                f"Context file {self.config.context_file} does not exist."
            )
        try:
            text = self.config.context_file.read_text()
            if self.config.context_file.suffix in [".yaml", ".yml"]:
                return yaml.safe_load(text)
            elif self.config.context_file.suffix == ".json":
                import json

                return json.loads(text)
            else:
                raise InvalidBuildFileError(
                    f"Context file {self.config.context_file} has unsupported file extension. Supported extensions are .yaml, .yml, and .json."
                )
        except (yaml.YAMLError, json.JSONDecodeError) as e:
            raise InvalidBuildFileError(
                f"Failed to parse context file {self.config.context_file}: {e}"
            ) from e

    def _generate_engine_config(self) -> EngineConfig:
        """Generate an EngineConfig from the current context."""
        engine_config = EngineConfig(
            source_dir=Path(self.config.source),
            output_dir=Path(self.config.output),
            context=self.context_manager._context,
            artifacts=self.config.artifacts,
            clean_output=self.config.clean_output,
            overwrite=self.config.overwrite,
            skip_patterns=self.config.skip_patterns,
        )
        logger.debug(f"Generated engine configuration: {engine_config}")
        return engine_config

    def _queued_file_summary(self, queued_files: list[QueuedFile]) -> None:
        """Print a summary of the queued files."""
        self.console.print(
            f"[bold green]Queued {len(queued_files)} files for processing:[/bold green]"
        )
        for queued_file in queued_files:
            self.console.print(
                f" - [blue]{queued_file.source}[/blue] -> [green]{queued_file.relative_path}[/green] ({queued_file.metadata.summary()})"
            )

    @property
    def config(self) -> BuildConfig:
        """Return the build configuration."""
        if self._config is None:
            raise ValueError("Build configuration has not been read yet.")
        return self._config

    @property
    def active_flow(self) -> BuildFlowConfig | None:
        """Return the active flow configuration, if any."""
        if self.flow is None:
            return None
        flow_config = self.config.flows.get(self.flow)
        if flow_config is None:
            raise InvalidBuildFileError(
                f"Flow '{self.flow}' is not defined in the build configuration."
            )
        return flow_config
