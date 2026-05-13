"""Typer-based command line interface for fishy-config."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable
import logging

import typer
from pydantic import BaseModel, ValidationError

from . import __version__, configure_logging
from .loader import load_yaml_file, merge_contexts
from .models import RenderRequest
from .project import ProjectConfig

RenderCallable = Callable[[RenderRequest], Any]


def create_app(
    render_fn: RenderCallable | None = None,
    project_config: ProjectConfig | None = None,
    *,
    help_text: str | None = None,
) -> typer.Typer:
    """Build a CLI app around a render function.

    External projects can reuse this factory and provide their own render
    callable while keeping the same command interface.

    Args:
        render_fn: The render function to call (defaults to fishy_config.render)
        project_config: Optional ProjectConfig with defaults, plugins, and metadata
        help_text: Override help text (uses project_config.help_text if not provided)
    """

    # Late import to avoid circular import
    if render_fn is None:
        from . import render

        render_fn = render

    config = project_config or ProjectConfig(name="fishy-config")
    final_help_text = help_text or config.help_text

    app = typer.Typer(add_completion=False, help=final_help_text)

    @app.callback()
    def main(
        ctx: typer.Context,
        verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable debug logging."),
    ) -> None:

        configure_logging(level=logging.DEBUG if verbose else logging.INFO)
        ctx.ensure_object(dict)

    @app.command(name="version")
    def version_command() -> None:
        """Show version info."""
        typer.echo(f"fishy-config {__version__}")
        raise typer.Exit(code=0)

    @app.command(name="render")
    def render_command(
        config_dir: Path = typer.Argument(
            ... if config.default_config_dir is None else config.default_config_dir,
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
        ),
        dest_dir: Path = typer.Argument(
            ... if config.default_dest_dir is None else config.default_dest_dir,
            file_okay=False,
            dir_okay=True,
        ),
        context_file: Path | None = typer.Option(
            None,
            "--context-file",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Optional YAML file to merge into the render context.",
        ),
        context_kv: list[str] = typer.Option(
            [],
            "--context",
            help="Inline context values as key=value. Can be repeated.",
        ),
        strict_undefined: bool = typer.Option(False, help="Fail on undefined template variables."),
        dry_run: bool = typer.Option(False, help="Simulate without writing files."),
        overwrite: bool | None = typer.Option(
            None,
            "--overwrite/--no-overwrite",
            help="Overwrite existing output files. If not specified, uses project default.",
        ),
        clean_dest: bool | None = typer.Option(
            None,
            "--clean-dest/--no-clean-dest",
            help="Delete destination directory before rendering. If not specified, uses project default.",
        ),
        skip_patterns: list[str] = typer.Option([], "--skip", help="Skip patterns to apply."),
    ) -> None:
        """Render a config directory into a destination directory."""

        inline_context = _parse_key_values(context_kv)

        # Load context from file: explicit > config_dir/context.yaml
        file_context = {}
        if context_file:
            file_context = _load_context_file(context_file)
        else:
            # Try to auto-load context.yaml from config directory
            default_context_file = Path(config_dir) / "context.yaml"
            if default_context_file.exists():
                file_context = _load_context_file(default_context_file)

        context = merge_contexts(file_context, inline_context)

        # Deterministic skip precedence: project defaults first, CLI additions second.
        final_skip_patterns: list[str] | None = None
        if config.skip_patterns or skip_patterns:
            final_skip_patterns = [*config.skip_patterns, *skip_patterns]

        # Validate and optionally cast context
        typed_context = None
        if config.context_model:
            try:
                typed_context = config.context_model.model_validate(context)
            except ValidationError as exc:
                typer.echo(
                    f"Context validation failed for {config.context_model.__name__}: {exc}",
                    err=True,
                )
                raise typer.Exit(code=1)

        # Generate plugins from factory if available
        plugins = []
        if config.plugin_factory:
            try:
                plugins = config.plugin_factory(typed_context or context)
            except Exception as exc:
                typer.echo(f"Plugin factory failed: {exc}", err=True)
                raise typer.Exit(code=1)

        # Determine overwrite: CLI flag takes precedence, then project default
        final_overwrite = overwrite if overwrite is not None else config.default_overwrite

        # Determine clean_dest: CLI flag takes precedence, then project default
        final_clean_dest = clean_dest if clean_dest is not None else config.default_clean_dest

        request = RenderRequest(
            config_dir=config_dir,
            dest_dir=dest_dir,
            context=context,
            context_model_type=config.context_model,
            typed_context=typed_context,
            plugins=plugins,
            skip_patterns=final_skip_patterns,
            template_extension=config.template_extension,
            strict_undefined=strict_undefined,
            dry_run=dry_run,
            overwrite=final_overwrite,
            clean_dest=final_clean_dest,
        )

        result = render_fn(request)

        if result.success:
            typer.echo(f"Rendered {result.total_files} files")
            if getattr(result, "artifacts", None):
                for artifact in result.artifacts:
                    typer.echo(f"artifact: {artifact}")
            raise typer.Exit(code=0)

        for error in result.errors:
            typer.echo(f"{error.file}: {error.message}", err=True)
        raise typer.Exit(code=1)

    return app


def _parse_key_values(values: list[str]) -> dict[str, Any]:
    parsed: dict[str, Any] = {}
    for raw in values:
        if "=" not in raw:
            raise typer.BadParameter(f"Expected key=value, got: {raw}")
        key, value = raw.split("=", 1)
        parsed[key] = value
    return parsed


def _load_context_file(path: Path) -> dict[str, Any]:
    loaded = load_yaml_file(path)
    return loaded


# Lazy app initialization to avoid circular imports
class _LazyApp:
    """Wrapper that defers app creation until first call."""

    def __init__(self):
        self._app = None

    def __call__(self, *args, **kwargs):
        if self._app is None:
            self._app = create_app()
        return self._app(*args, **kwargs)


app = _LazyApp()


if __name__ == "__main__":
    app()
