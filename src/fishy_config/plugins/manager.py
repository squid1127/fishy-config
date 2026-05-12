"""Plugin manager to coordinate plugin lifecycles."""

from __future__ import annotations

from typing import Iterable
from pathlib import Path

from .base import Plugin, HookContext, PostRunContext
from ..models import RenderOptions, RenderResult, ContextConfig
from ..log import get_logger

logger = get_logger(__name__)


class PluginManager:
    def __init__(self, plugins: Iterable[Plugin] | None = None) -> None:
        self.plugins = list(plugins or [])
        self.options: RenderOptions | None = None

    def register(self, plugin: Plugin) -> None:
        self.plugins.append(plugin)

    def on_run_start(self, options: RenderOptions) -> None:
        # Keep a copy of options for use in hook contexts
        try:
            self.options = options.model_copy(deep=True)
        except Exception:
            self.options = options

        for p in self.plugins:
            try:
                logger.debug("Plugin on_run_start: %s", p.name)
                p.on_run_start(options)
            except Exception:
                logger.exception("Plugin on_run_start failed: %s", getattr(p, "name", p))

    def should_skip(self, src_path: Path, rel_path: Path, context: dict) -> bool:
        # Build a minimal HookContext for skip checks. Plugins will receive a
        # copy of options if available on the manager caller.
        opts = self.options or RenderOptions(
            config_dir=src_path, dest_dir=src_path, context=ContextConfig()
        )
        for p in self.plugins:
            try:
                hook = HookContext(
                    src_path=src_path,
                    rel_path=rel_path,
                    dest_path=src_path,
                    context=context,
                    options=opts,
                )
                if p.should_skip(hook):
                    logger.debug("Plugin requested skip: %s -> %s", p.name, rel_path)
                    return True
            except Exception:
                logger.exception("Plugin should_skip failed: %s", getattr(p, "name", p))
        return False

    def pre_render(self, hook_ctx: HookContext) -> dict:
        ctx = hook_ctx.context
        for p in self.plugins:
            try:
                updated = p.pre_render(hook_ctx)
                if updated is not None:
                    ctx = updated
                    hook_ctx.context = ctx
            except Exception:
                logger.exception("Plugin pre_render failed: %s", getattr(p, "name", p))
        return ctx

    def post_render(self, hook_ctx: HookContext, rendered: str) -> str:
        content = rendered
        for p in self.plugins:
            try:
                maybe = p.post_render(hook_ctx, content)
                if maybe is not None:
                    content = maybe
            except Exception:
                logger.exception("Plugin post_render failed: %s", getattr(p, "name", p))
        return content

    def on_run_end(self, post_ctx: PostRunContext) -> None:
        for p in self.plugins:
            try:
                logger.debug("Plugin on_run_end: %s", p.name)
                p.on_run_end(post_ctx)
            except Exception:
                logger.exception("Plugin on_run_end failed: %s", getattr(p, "name", p))
