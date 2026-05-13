"""Project configuration for fishy-config consumers."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Type

from pydantic import BaseModel

from .models import DEFAULT_SKIP_PATTERNS


@dataclass
class ProjectConfig:
    """Describes a fishy-config consumer project.

    This allows consumers to define their defaults and custom behavior
    without reimplementing CLI or render logic.
    """

    name: str
    """Project name (e.g., 'the-server-rp')."""

    context_model: Type[BaseModel] | None = None
    """Optional Pydantic model for context validation."""

    default_config_dir: Path | None = None
    """Default config directory. If None, becomes a required CLI argument."""

    default_dest_dir: Path | None = None
    """Default destination directory. If None, becomes a required CLI argument."""

    plugin_factory: Callable[..., list] | None = None
    """Optional factory function that creates plugins given the context.

    Signature: (context: dict | BaseModel) -> list[BasePlugin]
    """

    skip_patterns: list[str] = field(default_factory=lambda: DEFAULT_SKIP_PATTERNS.copy())
    """Default skip patterns for rendering."""

    template_extension: str = ".j2"
    """Template file extension."""

    help_text: str = "Render templated config."
    """CLI help text."""

    default_overwrite: bool = True
    """Overwrite destination files by default (set to False to preserve existing)."""

    default_clean_dest: bool = False
    """Delete destination directory before rendering by default."""
