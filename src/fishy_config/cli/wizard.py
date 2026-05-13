"""Interactive wizard command for fishy-config."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any, Callable

import typer
from pydantic import BaseModel, ValidationError
import yaml

from ..loader import load_yaml_file, merge_contexts
from ..models import RenderRequest
from ..project import ProjectConfig


def register_wizard_command(
    app: typer.Typer,
    render_fn: Callable[[RenderRequest], Any],
    config: ProjectConfig,
) -> None:
    """Register the interactive wizard command when enabled."""

    @app.command(name="wizard")
    def wizard_command(
        config_dir: Path | None = typer.Argument(
            None,
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
        ),
        dest_dir: Path | None = typer.Argument(
            None,
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
        """Interactively gather context and render config files."""

        from .tui import BuildSession, WizardSetup, build_field_specs, run_wizard_tui

        resolved_config_dir = config_dir or config.default_config_dir
        resolved_dest_dir = dest_dir or config.default_dest_dir
        initial_context = parse_key_values(context_kv)

        if context_file:
            file_context = load_context_file(context_file)
        elif resolved_config_dir is not None and Path(resolved_config_dir).exists():
            default_context_file = Path(resolved_config_dir) / "context.yaml"
            file_context = (
                load_context_file(default_context_file) if default_context_file.exists() else {}
            )
        else:
            file_context = {}

        context = merge_contexts(file_context, initial_context)

        field_specs = []
        if config.context_model:
            field_specs = build_field_specs(config.context_model, context)

        setup = WizardSetup(
            config_dir=resolved_config_dir,
            dest_dir=resolved_dest_dir,
            strict_undefined=strict_undefined,
            dry_run=dry_run,
            overwrite=overwrite if overwrite is not None else config.default_overwrite,
            clean_dest=clean_dest if clean_dest is not None else config.default_clean_dest,
            skip_patterns=(
                [*config.skip_patterns, *skip_patterns]
                if (config.skip_patterns or skip_patterns)
                else []
            ),
        )

        session = BuildSession(setup=setup, field_specs=field_specs, context=context)
        tui_result = run_wizard_tui(session)
        if tui_result is None:
            raise typer.Exit(code=1)

        request = build_render_request(
            config=replace(config, skip_patterns=[]),
            config_dir=tui_result.config_dir,
            dest_dir=tui_result.dest_dir,
            context=tui_result.context,
            strict_undefined=tui_result.strict_undefined,
            dry_run=tui_result.dry_run,
            overwrite=tui_result.overwrite,
            clean_dest=tui_result.clean_dest,
            skip_patterns=tui_result.skip_patterns,
        )

        result = render_fn(request)

        if result.success:
            typer.echo("\nSuccess!")
            typer.echo(f"Rendered {result.total_files} files")
            if getattr(result, "artifacts", None):
                for artifact in result.artifacts:
                    typer.echo(f"Artifact: {artifact}")
            raise typer.Exit(code=0)

        typer.echo("\nErrors occurred during rendering:", err=True)
        for error in result.errors:
            typer.echo(f"{error.file}: {error.message}", err=True)
        raise typer.Exit(code=1)


def parse_key_values(values: list[str]) -> dict[str, Any]:
    parsed: dict[str, Any] = {}
    for raw in values:
        if "=" not in raw:
            raise typer.BadParameter(f"Expected key=value, got: {raw}")
        key, value = raw.split("=", 1)
        parsed[key] = value
    return parsed


def load_context_file(path: Path) -> dict[str, Any]:
    loaded = load_yaml_file(path)
    return loaded

def build_render_request(
    *,
    config: ProjectConfig,
    config_dir: Path,
    dest_dir: Path,
    context: dict[str, Any],
    strict_undefined: bool,
    dry_run: bool,
    overwrite: bool | None,
    clean_dest: bool | None,
    skip_patterns: list[str],
) -> RenderRequest:
    final_skip_patterns: list[str] | None = None
    if config.skip_patterns or skip_patterns:
        final_skip_patterns = [*config.skip_patterns, *skip_patterns]

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

    plugins = []
    if config.plugin_factory:
        try:
            plugins = config.plugin_factory(typed_context or context)
        except Exception as exc:
            typer.echo(f"Plugin factory failed: {exc}", err=True)
            raise typer.Exit(code=1)

    final_overwrite = overwrite if overwrite is not None else config.default_overwrite
    final_clean_dest = clean_dest if clean_dest is not None else config.default_clean_dest

    return RenderRequest(
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


def get_field_default(field_info: Any) -> Any:
    if getattr(field_info, "is_required", lambda: True)():
        return MISSING
    try:
        return field_info.get_default(call_default_factory=True)
    except Exception:
        return MISSING


def field_examples(field_info: Any) -> list[Any]:
    examples = getattr(field_info, "examples", None)
    if examples:
        return list(examples)
    extra = getattr(field_info, "json_schema_extra", None) or {}
    extra_examples = extra.get("examples")
    return list(extra_examples) if extra_examples else []


def normalize_prompt_seed(value: Any) -> Any:
    if isinstance(value, str):
        return parse_prompt_value(value)
    return value


def stringify_default(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (dict, list, tuple, set)):
        return yaml.safe_dump(value, sort_keys=True, indent=4).strip()
    return str(value)


def parse_prompt_value(raw_value: str) -> Any:
    parsed = yaml.safe_load(raw_value)
    return raw_value if parsed is None and raw_value.strip().lower() != "null" else parsed


MISSING = object()
 