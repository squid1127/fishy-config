"""Typer application for fishy-config."""

import logging
from importlib.metadata import version as get_distribution_version
from pathlib import Path
import typer
from typer import Typer
import rich
import yaml

from ..log import enable_logging, get_logger
from .main import FishyConfigCLI
from .models import ContextSourceType
from .schema_gen import generate_schemas, generate_vs_code_settings

logger = get_logger(__name__)

app = Typer(
    name="fishy-config",
    help="A fishy python tool to make managing config files easier using a simple templating system.",
    no_args_is_help=True,
    add_completion=False,
)


@app.callback()
def main(
    ctx: typer.Context,
    debug: bool = typer.Option(False, "--debug", help="Enable debug logging."),
) -> None:
    """Configure CLI logging before command execution."""
    del ctx
    enable_logging(logging.DEBUG if debug else logging.INFO)
    logger.debug("Debug logging enabled.")


@app.command()
def version() -> None:
    """Show the version of fishy-config."""
    rich.print(f"fishy-config {get_distribution_version('fishy_config')}")


@app.command()
def wizard() -> None:
    """Run the fishy-config wizard to create a new configuration."""
    rich.print("[red]fishy-config wizard is not yet implemented. Please check back later.[/red]")


@app.command()
def build(
    build_file: Path | None = typer.Argument(None, help="Path to the build configuration file."),
    context: list[str] = typer.Option(
        None, "--context", "-c", help="Additional context values in key=value format."
    ),
    presets: list[str] = typer.Option(
        None, "--preset", "-p", help="Presets to apply from the build configuration."
    ),
    flow: str = typer.Option(
        None, "--flow", "-f", help="Specify a flow to execute from the build configuration."
    ),
    interactive: bool = typer.Option(
        False, "--interactive", "-i", help="Run in interactive mode to confirm actions."
    ),
):
    """Build artifacts based on the provided build configuration file."""

    app_instance = FishyConfigCLI(
        build_file=build_file, presets=presets, flow=flow, interactive=interactive
    )
    app_instance.read_build_file()
    app_instance.add_context_source(
        source=parse_context_options(context) if context else {},
        source_type=ContextSourceType.ARG,
        priority=30,
    )
    rich.print("[green]Configuration loaded successfully. Starting build process...[/green]")
    app_instance.run()
    
@app.command()
def generate_schema(
    output: Path = typer.Argument(
        Path(".fishy-config/schemas"), help="The output directory where the generated JSON schema files will be saved."
    ),
    vs_code_settings: Path | None = typer.Option(
        None,
        "--vs-code-settings",
        help="If provided, also update or generate a VS Code settings.json file with JSON schema associations for the generated schema files.",
    ),
):
    """Generate JSON schema files for the Pydantic models used in fishy-config."""
    if output.exists() and not output.is_dir():
        raise typer.BadParameter(f"Output path '{output}' exists and is not a directory.")
    elif not output.exists():
        output.mkdir(parents=True)
    generate_schemas(output)
    typer.echo(f"JSON schema files generated successfully in '{output}'.")
    
@app.command()
def generate_schema_vs(
    vs_code_settings: Path = typer.Argument(
        Path(".vscode/settings.json"), help="The path to the VS Code settings.json file to update or create with JSON schema associations for fishy-config."
    )
):
    """Generate or update a VS Code settings.json file with JSON schema associations for the Pydantic models used in fishy-config."""
    if vs_code_settings.exists() and not vs_code_settings.is_file():
        raise typer.BadParameter(f"VS Code settings path '{vs_code_settings}' exists and is not a file.")
    elif not vs_code_settings.exists():
        vs_code_settings.parent.mkdir(parents=True, exist_ok=True)
    generate_vs_code_settings(vs_code_settings)
    typer.echo(f"VS Code settings file '{vs_code_settings}' updated successfully with JSON schema associations for fishy-config.")


def parse_context_options(context_options: list[str]) -> dict[str, str]:
    """Parse context options provided as key=value pairs into a dictionary."""
    context_dict = {}
    for option in context_options:
        if "=" not in option:
            raise typer.BadParameter(f"Context option '{option}' is not in key=value format.")
        key, _, value = option.partition("=")
        try:
            value = yaml.safe_load(value)
        except yaml.YAMLError as e:
            raise typer.BadParameter(f"Value for context key '{key}' is not valid YAML: {e}") from e
        context_dict[key] = value
    return context_dict
