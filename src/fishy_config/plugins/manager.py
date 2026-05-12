"""Plugin manager to coordinate plugin lifecycles."""

from __future__ import annotations

from typing import Iterable
from pathlib import Path

from .base import Plugin
from ..models import RenderOptions, RenderResult
from ..log import get_logger

logger = get_logger(__name__)


class PluginManager:
    def __init__(self, plugins: Iterable[Plugin] | None = None) -> None:
        self.plugins = list(plugins or [])

    def register(self, plugin: Plugin) -> None:
        self.plugins.append(plugin)

    def on_run_start(self, options: RenderOptions) -> None:
        for p in self.plugins:
            try:
                logger.debug("Plugin on_run_start: %s", p.name)
                p.on_run_start(options)
            except Exception:
                logger.exception("Plugin on_run_start failed: %s", getattr(p, "name", p))

    def should_skip(self, src_path: Path, rel_path: Path, context: dict) -> bool:
        for p in self.plugins:
            try:
                if p.should_skip(src_path, rel_path, context):
                    logger.debug("Plugin requested skip: %s -> %s", p.name, rel_path)
                    return True
            except Exception:
                logger.exception("Plugin should_skip failed: %s", getattr(p, "name", p))
        return False

    def pre_render(self, src_path: Path, rel_path: Path, dest_path: Path, context: dict) -> dict:
        ctx = context
        for p in self.plugins:
            try:
                ctx = p.pre_render(src_path, rel_path, dest_path, ctx) or ctx
            except Exception:
                logger.exception("Plugin pre_render failed: %s", getattr(p, "name", p))
        return ctx

    def post_render(self, src_path: Path, rel_path: Path, dest_path: Path, rendered: str) -> str:
        content = rendered
        for p in self.plugins:
            try:
                maybe = p.post_render(src_path, rel_path, dest_path, content)
                if maybe is not None:
                    content = maybe
            except Exception:
                logger.exception("Plugin post_render failed: %s", getattr(p, "name", p))
        return content

    def on_run_end(self, result: RenderResult) -> None:
        for p in self.plugins:
            try:
                logger.debug("Plugin on_run_end: %s", p.name)
                p.on_run_end(result)
            except Exception:
                logger.exception("Plugin on_run_end failed: %s", getattr(p, "name", p))
