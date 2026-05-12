"""Typer-based command line interface for fishy-config."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable
import logging

import typer

from . import __version__, configure_logging, render
from .loader import load_yaml_file, merge_contexts
from .plugins.discovery import resolve_plugins

RenderCallable = Callable[..., Any]
PluginResolver = Callable[..., list[Any]]


def create_app(
    render_fn: RenderCallable = render,
    plugin_resolver: PluginResolver = resolve_plugins,
    *,
    help_text: str = "Render templated config directories.",
) -> typer.Typer:
    """Build a CLI app around a render function.

    External projects can reuse this factory and provide their own render
    callable and/or plugin resolver while keeping the same command interface.
    """

    app = typer.Typer(add_completion=False, help=help_text)

    @app.callback()
    def main(
        ctx: typer.Context,
        verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable debug logging."),
        version: bool = typer.Option(False, "--version", help="Show version and exit."),
    ) -> None:
        if version:
            typer.echo(__version__)
            raise typer.Exit()

        configure_logging(level=logging.DEBUG if verbose else logging.INFO)
        ctx.ensure_object(dict)

    @app.command(name="render")
    def render_command(
        config_dir: Path = typer.Argument(
            ..., exists=True, file_okay=False, dir_okay=True, readable=True
        ),
        dest_dir: Path = typer.Argument(..., file_okay=False, dir_okay=True),
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
        plugin: list[str] = typer.Option(
            [],
            "--plugin",
            help="Plugin import path (module:Class or module.function). Can be repeated.",
        ),
        discover_plugins: bool = typer.Option(
            False,
            "--discover-plugins/--no-discover-plugins",
            help="Load plugins from the fishy_config.plugins entry point group.",
        ),
        strict_undefined: bool = typer.Option(False, help="Fail on undefined template variables."),
        dry_run: bool = typer.Option(False, help="Simulate without writing files."),
        overwrite: bool = typer.Option(False, help="Overwrite existing output files."),
        skip_patterns: list[str] = typer.Option([], "--skip", help="Skip patterns to apply."),
    ) -> None:
        """Render a config directory into a destination directory."""

        inline_context = _parse_key_values(context_kv)
        file_context = _load_context_file(context_file) if context_file else {}
        context = merge_contexts(file_context, inline_context)
        resolved_plugins = plugin_resolver(plugin, discover=discover_plugins)

        result = render_fn(
            config_dir=config_dir,
            dest_dir=dest_dir,
            context=context,
            plugins=resolved_plugins,
            skip_patterns=skip_patterns,
            strict_undefined=strict_undefined,
            dry_run=dry_run,
            overwrite=overwrite,
        )

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


app = create_app()


if __name__ == "__main__":
    app()
