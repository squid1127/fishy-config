"""Plugin protocol and base classes for fishy-config.

Defines standard hook context objects used during the render lifecycle so
plugins receive a consistent, well-typed set of information.
"""

from __future__ import annotations

from typing import Protocol, Optional
from pathlib import Path
from dataclasses import dataclass

from ..models import RenderOptions, RenderResult


@dataclass(frozen=True, slots=True)
class HookContext:
    src_path: Path
    rel_path: Path
    dest_path: Path
    context: dict
    options: RenderOptions


@dataclass(frozen=True, slots=True)
class PostRunContext:
    options: RenderOptions
    result: RenderResult


class Plugin(Protocol):
    """Protocol that plugins should follow.

    Methods are optional; plugin manager will call them if present.
    """

    name: str

    def on_run_start(self, options: RenderOptions) -> None:  # pragma: no cover - interface
        ...

    def should_skip(self, ctx: HookContext) -> bool:  # pragma: no cover - interface
        return False

    def pre_render(self, ctx: HookContext) -> dict:
        return ctx.context

    def post_render(self, ctx: HookContext, rendered: str) -> Optional[str]:
        return rendered

    def on_run_end(self, ctx: PostRunContext) -> None:  # pragma: no cover - interface
        ...


class BasePlugin:
    """Simple base with defaults so implementing plugins can override what they need."""

    name = "base"

    def on_run_start(self, options: RenderOptions) -> None:
        return None

    def should_skip(self, ctx: HookContext) -> bool:
        return False

    def pre_render(self, ctx: HookContext) -> dict:
        return ctx.context

    def post_render(self, ctx: HookContext, rendered: str) -> Optional[str]:
        return rendered

    def on_run_end(self, ctx: PostRunContext) -> None:
        return None
