"""Main executor for fishy-config CLI."""

import pydantic
import rich
from pathlib import Path
import yaml
import json

from .context import ContextManager, schema_as_defaults
from .models import BuildConfig, ContextSource, ContextSourceType
from .exceptions import InvalidContextError, InvalidContextSchemaError, InvalidBuildFileError
from .config import load_config

from ..models.config import EngineConfig
from ..models.files import QueuedFile, FailedFile, FileResult
from ..models.artifact import ArtifactResult
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
        dry_run: bool = False,
        export: bool = False,
    ):
        self.build_file = build_file
        self.context_manager = ContextManager()
        self.presets = presets or []
        self.flow = flow
        self.interactive = interactive
        self.dry_run = dry_run
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

        self._config = load_config(self.build_file)
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
        self._validate_context()

        engine_config = self._generate_engine_config()
        renderer = TemplateRenderer(engine_config)

        queued_files = self._scan_source_directory(engine_config, renderer)
        renderer.loader.update_queued_files(queued_files)

        success_files = [f for f in queued_files if isinstance(f, QueuedFile)]
        failed_files = [f for f in queued_files if isinstance(f, FailedFile)]

        self._queued_file_summary(success_files, failed_files)
        if self.dry_run:
            self.console.print("[yellow]Dry run mode enabled. No files will be generated.[/yellow]")
            return

        if self.interactive and not self.console.input(
            "[bold yellow]Proceed with file generation? (y/n): [/bold yellow]"
        ).strip().lower().startswith("y"):
            self.console.print("[red]Aborting file generation.[/red]")
            return

        results = self._generate_output_files(engine_config, renderer, success_files)
        artifact_results = self._generate_artifacts(engine_config, renderer)

        self._print_build_summary(engine_config, results, artifact_results, failed_files)

    def _validate_context(self) -> None:
        """Validate the context against the schema."""
        logger.debug(
            f"Validating {self.context_manager.context} against schema {self.context_manager.schema}"
        )
        try:
            self.context_manager.validate_context()
        except InvalidContextSchemaError as e:
            raise InvalidContextError(f"Context validation failed: {e}") from e

        self.console.print("[green]Successfully validated context.[/green]")

    def _scan_source_directory(self, engine_config, renderer) -> list:
        """Scan the source directory for files to render."""
        scanner = SourceTreeScanner(engine_config, renderer)
        queued_files = []
        with self.console.status("[bold green]Scanning source directory...[/bold green]") as status:
            for queued_file in scanner.scan():
                queued_files.append(queued_file)
                logger.debug(f"Queued file: {queued_file.source} -> {queued_file.relative_path}")
                status.update(
                    f"[blue]({len(queued_files)})[/blue] [green]Found {queued_file.source}[/green]"
                )
        return queued_files

    def _generate_output_files(self, engine_config, renderer, queued_files) -> list:
        """Generate output files from queued files."""
        output = OutputBuilder(engine_config, renderer)
        results = []
        with self.console.status("[bold green]Generating output files...[/bold green]") as status:
            for result in output.generate(queued_files, sort=True, clean=True):
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
        return results

    def _generate_artifacts(self, engine_config, renderer) -> list:
        """Generate artifacts based on configuration."""
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
        return artifact_results

    def _print_build_summary(self, engine_config: EngineConfig, results: list[FileResult], artifact_results: list[ArtifactResult], failed_files: list[FailedFile]) -> None:
        """Print the final build summary."""
        results_failed = [r for r in results if r.error]
        artifact_results_failed = [a for a in artifact_results if a.error]
        has_errors = bool(results_failed or artifact_results_failed)

        if has_errors:
            self.console.print(
                "\n[bold red]Build process completed with errors.\nOverview:[/bold red]"
            )
        else:
            self.console.print(
                "\n[bold green]Build process completed successfully.\nOverview:[/bold green]"
            )

        self.console.print(f"[bold blue]{len(results)} files [/bold blue]")
        self.console.print(
            f"[bold green]{len(results) - len(results_failed)} successful[/bold green]"
        )
        self.console.print(f"[bold red]{len(results_failed)} failed[/bold red]")
        self.console.print(f"[bold blue]Output directory: {engine_config.output_dir}[/bold blue]")

        for artifact_result in artifact_results:
            if artifact_result.error:
                self.console.print(
                    f"[red]Artifact: {artifact_result.artifact.path} failed with error: {artifact_result.error}[/red]"
                )
            else:
                self.console.print(f"[green]Artifact: {artifact_result.generated_path}[/green]")

        if has_errors:
            self.console.print("\n[bold red]Failed Files:[/bold red]")
            for r in results_failed:
                self.console.print(f" - [red]{r.queued_file.source}: {r.error}[/red]")

            if artifact_results_failed:
                self.console.print("\n[bold red]Failed Artifacts:[/bold red]")
                for a in artifact_results_failed:
                    self.console.print(f" - [red]{a.artifact.path}: {a.error}[/red]")
        if failed_files:
            self.console.print("\n[bold red]Files that failed to queue:[/bold red]")
            for f in failed_files:
                self.console.print(f" - [red]{f.source}: {f.error}[/red]")

    def _apply_build_config_to_context(self) -> None:
        """Apply the build configuration to the context manager."""
        context = self.config.context
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
        logger.debug(
            f"Final context after applying build configuration: {self.context_manager.context}"
        )

    def _read_context_file(self) -> dict | None:
        """Read the context schema and defaults from the specified context file."""
        if not self.config.context_file:
            return None
        if not self.config.context_file.exists():
            raise InvalidBuildFileError(f"Context file {self.config.context_file} does not exist.")
        try:
            text = self.config.context_file.read_text()
            if self.config.context_file.suffix in [".yaml", ".yml"]:
                return yaml.safe_load(text)
            elif self.config.context_file.suffix == ".json":

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
            output_config=self.config.options,
        )
        logger.debug(f"Generated engine configuration: {engine_config}")
        return engine_config

    def _queued_file_summary(self, success_files: list[QueuedFile], failed_files: list[FailedFile]) -> None:
        """Print a summary of the queued files."""

        self.console.print(
            f"[bold green]Queued {len(success_files)} files for processing:[/bold green]"
        )
        for queued_file in success_files:
            self.console.print(
                f" - [blue]{queued_file.source}[/blue] -> [green]{queued_file.relative_path}[/green] ({queued_file.metadata.summary()})"
            )

        if failed_files:
            self.console.print(
                f"\n[bold red]Failed to queue {len(failed_files)} files due to errors:[/bold red]"
            )
            for failed_file in failed_files:
                self.console.print(
                    f" - [red]{failed_file.source}[/red]: {failed_file.error}"
                )
                
    @property
    def config(self) -> BuildConfig:
        """Return the build configuration."""
        if self._config is None:
            raise ValueError("Build configuration has not been read yet.")
        return self._config
