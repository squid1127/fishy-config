"""Built-in plugins for fishy-config.

Includes a simple skip-if-missing plugin and a zip-exporter plugin.
"""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path
from typing import Optional

from .base import BasePlugin
from ..models import RenderResult, RenderOptions
from ..log import get_logger

logger = get_logger(__name__)


class SkipIfContextMissingPlugin(BasePlugin):
    """Skip files when a specific context key is missing or falsy.

    Example:
        SkipIfContextMissingPlugin(key="deploy.enabled")
    """

    name = "skip_if_context_missing"

    def __init__(self, key: str):
        self.key = key

    def _get(self, ctx: dict, key: str):
        parts = key.split(".")
        v = ctx
        for p in parts:
            if not isinstance(v, dict) or p not in v:
                return None
            v = v[p]
        return v

    def should_skip(self, src_path: Path, rel_path: Path, context: dict) -> bool:
        val = self._get(context, self.key)
        skip = not bool(val)
        if skip:
            logger.debug("Skipping %s because context key %s is missing/false", rel_path, self.key)
        return skip


class ZipExporterPlugin(BasePlugin):
    """Create a zip archive of the destination directory and add artifact info.

    Initializes with `archive_name` (optional). On run end, writes a .zip and
    computes sha256, appending artifact path to result.artifacts.
    """

    name = "zip_exporter"

    def __init__(self, archive_name: Optional[str] = None):
        self.archive_name = archive_name

    def on_run_end(self, result: RenderResult) -> None:
        try:
            if result.dest_dir is None:
                logger.warning(
                    "ZipExporter: destination directory was not provided on RenderResult"
                )
                return

            dest_dir = result.dest_dir
            if not dest_dir.exists():
                logger.warning("ZipExporter: destination directory does not exist: %s", dest_dir)
                return

            archive_base = self.archive_name or f"{dest_dir.name}.zip"
            archive_path = dest_dir.parent / archive_base

            logger.info("Creating zip archive: %s (root=%s)", archive_path, dest_dir)
            shutil.make_archive(str(archive_path.with_suffix("")), "zip", root_dir=str(dest_dir))

            # Compute sha256
            h = hashlib.sha256()
            with open(archive_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    h.update(chunk)
            digest = h.hexdigest()
            artifact_info = f"{archive_path}:{digest}"
            result.artifacts.append(artifact_info)
            logger.info("Zip created: %s (sha256=%s)", archive_path, digest)
        except Exception:
            logger.exception("ZipExporter failed")
