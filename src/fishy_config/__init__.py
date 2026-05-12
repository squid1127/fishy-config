"""A "simple" python-based library for templating config."""

__version__ = "0.1.0"

from pathlib import Path
from typing import Any

from .exceptions import (
    ConfigValidationError,
    ContextLoadError,
    ContextMergeError,
    FileIOError,
    FishyConfigError,
    PluginError,
    TemplateRenderError,
)
from .loader import load_context
from .models import ContextConfig, RenderOptions, RenderResult, RenderError
from .pipeline import RenderPipeline
from .log import configure_logging
from .plugins.base import BasePlugin, Plugin as PluginProtocol, HookContext, PostRunContext
from .plugins.manager import PluginManager

__all__ = [
    "render",
    "load_context",
    "RenderPipeline",
    "ContextConfig",
    "RenderOptions",
    "RenderResult",
    "RenderError",
    "FishyConfigError",
    "ContextLoadError",
    "ContextMergeError",
    "TemplateRenderError",
    "FileIOError",
    "ConfigValidationError",
    "PluginError",
    "configure_logging",
    "PluginProtocol",
    "BasePlugin",
    "PluginManager",
    "HookContext",
    "PostRunContext",
]


def render(
    config_dir: str | Path,
    dest_dir: str | Path,
    context: dict[str, Any] | None = None,
    plugins: list[Any] | None = None,
    *,
    preserve_structure: bool = True,
    skip_patterns: list[str] | None = None,
    strict_undefined: bool = False,
    dry_run: bool = False,
    overwrite: bool = False,
) -> RenderResult:
    """High-level API for rendering config templates.

    Renders all templates (.j2 files) and copies other files from config_dir
    to dest_dir, using provided context for template variable substitution.

    Args:
        config_dir: Source directory containing templates and config files
        dest_dir: Destination directory for rendered output
        context: Context dict for template rendering; overrides context.yaml
        preserve_structure: If True, preserve directory structure from config_dir
        skip_patterns: List of gitignore-style patterns for files to skip
        strict_undefined: If True, fail on undefined template variables
        dry_run: If True, don't write files, only simulate
        overwrite: If True, overwrite existing files in destination

    Returns:
        RenderResult with files processed and any errors

    Raises:
        ContextLoadError: If context cannot be loaded
        FishyConfigError: For other errors during rendering
    """
    config_dir = Path(config_dir)
    dest_dir = Path(dest_dir)

    # Load context (from YAML + runtime override)
    ctx = load_context(config_dir, context)

    # Create render options
    options = RenderOptions(
        config_dir=config_dir,
        dest_dir=dest_dir,
        context=ctx,
        preserve_structure=preserve_structure,
        skip_patterns=skip_patterns or [],
        plugins=plugins or [],
        strict_undefined=strict_undefined,
        dry_run=dry_run,
        overwrite=overwrite,
    )

    # Execute pipeline
    pipeline = RenderPipeline(options)
    return pipeline.run()
