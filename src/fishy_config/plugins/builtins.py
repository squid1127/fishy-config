"""Built-in plugins for fishy-config.

Includes a simple skip-if-missing plugin and a zip-exporter plugin.
"""

from __future__ import annotations

import hashlib
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Optional

from .base import BasePlugin, HookContext, PostRunContext
from ..models import RenderResult, RenderOptions
from ..log import get_logger

logger = get_logger(__name__)


class SkipIfContextMissingPlugin(BasePlugin):
    """Skip files when a specific context key is missing or falsy.

    Example:
        SkipIfContextMissingPlugin(key="deploy.enabled")
    """

    name = "skip_if_context_missing"

    def __init__(self, key: str, path_prefix: str | Path | None = None):
        self.key = key
        self.path_prefix = Path(path_prefix) if path_prefix is not None else None

    def _get(self, ctx: dict, key: str):
        parts = key.split(".")
        v = ctx
        for p in parts:
            if not isinstance(v, dict) or p not in v:
                return None
            v = v[p]
        return v

    def should_skip(self, ctx: HookContext) -> bool:
        if self.path_prefix is not None and not ctx.rel_path.is_relative_to(self.path_prefix):
            return False

        val = self._get(ctx.context, self.key)
        skip = not bool(val)
        if skip:
            logger.debug(
                "Skipping %s because context key %s is missing/false",
                ctx.rel_path,
                self.key,
            )
        return skip


class RewriteRelativePathPlugin(BasePlugin):
    """Rewrite a rendered file's output-relative path when a source path matches.

    This is useful for cases where a consumer wants one source file to land in a
    different output location without subclassing the render pipeline.
    """

    name = "rewrite_relative_path"

    def __init__(
        self,
        source_rel_path: str | Path,
        rewrite_to: str | Path | Callable[[HookContext], str | Path],
    ):
        self.source_rel_path = Path(source_rel_path)
        self.rewrite_to = rewrite_to

    def _resolve_target(self, ctx: HookContext) -> Path:
        if callable(self.rewrite_to):
            return Path(self.rewrite_to(ctx))
        return Path(self.rewrite_to)

    def pre_render(self, ctx: HookContext) -> dict:
        if ctx.rel_path == self.source_rel_path:
            new_rel = self._resolve_target(ctx)
            ctx.output_rel_path = new_rel
            ctx.dest_path = ctx.options.dest_dir / new_rel
            logger.debug("Rewriting output path for %s -> %s", ctx.rel_path, new_rel)
        return super().pre_render(ctx)


class ZipExporterPlugin(BasePlugin):
    """Create a zip archive of the destination directory and add artifact info.

    Initializes with `archive_name` (optional). On run end, writes a .zip and
    computes sha256, appending artifact path to result.artifacts.
    """

    name = "zip_exporter"

    def __init__(self, archive_name: Optional[str] = None):
        self.archive_name = archive_name

    def _resolve_archive_path(self, dest_dir: Path) -> Path:
        archive_name = self.archive_name or dest_dir.name
        archive_path = dest_dir.parent / archive_name
        if archive_path.suffix != ".zip":
            archive_path = archive_path.with_suffix(".zip")
        return archive_path

    def on_run_end(self, ctx: PostRunContext) -> None:
        try:
            dest_dir = ctx.options.dest_dir
            if dest_dir is None:
                logger.warning("ZipExporter: destination directory not present on options")
                return

            if not dest_dir.exists():
                logger.warning("ZipExporter: destination directory does not exist: %s", dest_dir)
                return

            archive_path = self._resolve_archive_path(dest_dir)

            logger.debug("Creating zip archive: %s (root=%s)", archive_path, dest_dir)
            shutil.make_archive(str(archive_path.with_suffix("")), "zip", root_dir=str(dest_dir))

            # Compute sha256
            h = hashlib.sha256()
            with open(archive_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    h.update(chunk)
            digest = h.hexdigest()
            artifact_info = f"{archive_path}:{digest}"
            ctx.result.artifacts.append(artifact_info)
            logger.debug("Zip created: %s (sha256=%s)", archive_path, digest)
        except Exception:
            logger.exception("ZipExporter failed")
