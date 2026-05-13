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
from .models import ContextConfig, RenderOptions, RenderResult, RenderError, RenderRequest
from .pipeline import RenderPipeline
from .log import configure_logging
from .project import ProjectConfig
from .cli import create_app
from .plugins.base import BasePlugin, Plugin as PluginProtocol, HookContext, PostRunContext
from .plugins.builtins import (
    CopyArtifactPlugin,
    RewriteRelativePathPlugin,
    SkipIfContextMissingPlugin,
    ZipExporterPlugin,
)
from .plugins.manager import PluginManager

__all__ = [
    "render",
    "create_app",
    "load_context",
    "RenderPipeline",
    "ProjectConfig",
    "ContextConfig",
    "RenderRequest",
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
    "SkipIfContextMissingPlugin",
    "RewriteRelativePathPlugin",
    "ZipExporterPlugin",
    "CopyArtifactPlugin",
]


def render(
    request: RenderRequest,
) -> RenderResult:
    """High-level API for rendering config templates from a unified request model.

    Renders all templates (.j2 files) and copies other files from config_dir
    to dest_dir, using provided context for template variable substitution.

    Args:
        request: Canonical render request containing directories, context, plugins, and options.

    Returns:
        RenderResult with files processed and any errors

    Raises:
        ContextLoadError: If context cannot be loaded
        FishyConfigError: For other errors during rendering
    """
    config_dir = Path(request.config_dir)
    dest_dir = Path(request.dest_dir)

    # Load context (from YAML + runtime override)
    ctx = load_context(config_dir, request.context)

    # Create render options
    options_kwargs: dict[str, Any] = {
        "config_dir": config_dir,
        "dest_dir": dest_dir,
        "context": ctx,
        "context_type": request.context_model_type,
        "typed_context": request.typed_context,
        "preserve_structure": request.preserve_structure,
        "plugins": request.plugins,
        "template_extension": request.template_extension,
        "strict_undefined": request.strict_undefined,
        "dry_run": request.dry_run,
        "overwrite": request.overwrite,
        "clean_dest": request.clean_dest,
    }

    # Keep model defaults when caller does not provide an override.
    if request.skip_patterns is not None:
        options_kwargs["skip_patterns"] = request.skip_patterns

    options = RenderOptions(
        **options_kwargs,
    )

    # Execute pipeline
    pipeline = RenderPipeline(options)
    return pipeline.run()
