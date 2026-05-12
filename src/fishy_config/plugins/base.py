"""Plugin protocol and base classes for fishy-config."""

from __future__ import annotations

from typing import Protocol, Optional
from pathlib import Path

from ..models import RenderOptions, RenderResult


class Plugin(Protocol):
    """Protocol that plugins should follow.

    Methods are optional; plugin manager will call them if present.
    """

    name: str

    def on_run_start(self, options: RenderOptions) -> None:  # pragma: no cover - interface
        ...

    def should_skip(
        self, src_path: Path, rel_path: Path, context: dict
    ) -> bool:  # pragma: no cover - interface
        return False

    def pre_render(self, src_path: Path, rel_path: Path, dest_path: Path, context: dict) -> dict:
        return context

    def post_render(
        self, src_path: Path, rel_path: Path, dest_path: Path, rendered: str
    ) -> Optional[str]:
        return rendered

    def on_run_end(self, result: RenderResult) -> None:  # pragma: no cover - interface
        ...


class BasePlugin:
    """Simple base with defaults so implementing plugins can override what they need."""

    name = "base"

    def on_run_start(self, options: RenderOptions) -> None:
        return None

    def should_skip(self, src_path: Path, rel_path: Path, context: dict) -> bool:
        return False

    def pre_render(self, src_path: Path, rel_path: Path, dest_path: Path, context: dict) -> dict:
        return context

    def post_render(
        self, src_path: Path, rel_path: Path, dest_path: Path, rendered: str
    ) -> Optional[str]:
        return rendered

    def on_run_end(self, result: RenderResult) -> None:
        return None
