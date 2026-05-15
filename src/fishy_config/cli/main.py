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
from ..models.files import EnqueuedFile
from ..log import get_logger
from ..scanner import SourceScanner
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
        try:
            self.context_manager.validate_context(schema=self.config.context)
        except InvalidContextSchemaError as e:
            raise InvalidContextError(f"Context validation failed: {e}") from e

        self.console.print("[green]Successfully validated context against schema.[/green]")
        engine_config = self._generate_engine_config()
        renderer = TemplateRenderer(engine_config)
        scanner = SourceScanner(engine_config, renderer)

        with self.console.status("[bold green]Scanning source directory...[/bold green]") as status:
            enqueued_files = []
            for enqueued_file in scanner.scan():
                enqueued_files.append(enqueued_file)
                logger.debug(
                    f"Enqueued file: {enqueued_file.source} -> {enqueued_file.relative_path}"
                )
                status.update(
                    f"[blue]({len(enqueued_files)})[/blue] [green]Found {enqueued_file.source}[/green]"
                )

        self._enqueued_file_summary(enqueued_files)
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
            for result in output.generate(enqueued_files):
                results.append(result)
                if result.error:
                    logger.error(
                        f"Error generating file {result.enqueued_file.source}: {result.error}"
                    )
                    self.console.print(
                        f"[red]Error generating file {result.enqueued_file.source}: {result.error}[/red]"
                    )
                else:
                    logger.debug(
                        f"Successfully generated file {result.enqueued_file.source} -> {result.enqueued_file.relative_path}"
                    )
                    status.update(
                        f"[blue]({len(results)}/{len(enqueued_files)})[/blue] [green]Generated {result.enqueued_file.relative_path}[/green]"
                    )

        self.console.print(
            f"[bold green]Successfully generated {len([r for r in results if not r.error])} files.[/bold green]"
        )

    def _apply_build_config_to_context(self) -> None:
        """Apply the build configuration to the context manager."""
        self.context_manager.set_schema(self.config.context)
        self.context_manager.add_source(
            ContextSource(
                data=schema_as_defaults(self.config.context),
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

    def _generate_engine_config(self) -> EngineConfig:
        """Generate an EngineConfig from the current context."""
        engine_config = EngineConfig(
            source_dir=Path(self.config.source),
            output_dir=Path(self.config.output),
            context=self.context_manager._context,
            artifacts=self.config.artifacts,
            clean_output=self.config.clean_output,
            overwrite=self.config.overwrite,
        )
        logger.debug(f"Generated engine configuration: {engine_config}")
        return engine_config

    def _enqueued_file_summary(self, enqueued_files: list[EnqueuedFile]) -> None:
        """Print a summary of the enqueued files."""
        self.console.print(
            f"[bold green]Enqueued {len(enqueued_files)} files for processing:[/bold green]"
        )
        for enqueued_file in enqueued_files:
            self.console.print(
                f" - [blue]{enqueued_file.source}[/blue] -> [green]{enqueued_file.relative_path}[/green] ({enqueued_file.metadata.summary()})"
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
