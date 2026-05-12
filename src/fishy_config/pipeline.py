"""Pipeline orchestration for rendering config."""

import shutil
import time
from pathlib import Path

import pathspec

from .exceptions import FileIOError, TemplateRenderError
from .loader import load_context
from .models import RenderOptions, RenderResult
from .renderer import Jinja2Renderer


class RenderPipeline:
    """Orchestrates the full render pipeline."""

    def __init__(self, options: RenderOptions):
        """Initialize pipeline with render options.

        Args:
            options: Render configuration
        """
        self.options = options
        self.renderer = Jinja2Renderer(
            options.config_dir,
            strict_undefined=options.strict_undefined,
        )
        self.result = RenderResult()

    def _should_skip(self, path: Path) -> bool:
        """Check if a file should be skipped based on skip patterns.

        Args:
            path: File path (relative to config_dir)

        Returns:
            True if file should be skipped
        """
        # Build pathspec from patterns
        spec = pathspec.PathSpec.from_lines("gitwildmatch", self.options.skip_patterns)
        return spec.match_file(str(path))

    def _process_file(self, file_path: Path, rel_path: Path) -> None:
        """Process a single file (render or copy).

        Args:
            file_path: Absolute path to file
            rel_path: Path relative to config_dir
        """
        # Check if should skip
        if self._should_skip(rel_path):
            return

        # Determine destination path
        dest_path = self.options.dest_dir / rel_path

        # Handle template files (.j2)
        if file_path.suffix == self.options.template_extension:
            self._render_template(file_path, rel_path, dest_path)
        else:
            # Copy as-is
            self._copy_file(file_path, dest_path, rel_path)

    def _render_template(self, src_path: Path, rel_path: Path, dest_path: Path) -> None:
        """Render a single template file.

        Args:
            src_path: Absolute source path
            rel_path: Relative path for context
            dest_path: Destination path (will strip .j2)
        """
        try:
            # Strip template extension from destination
            dest_path = dest_path.with_suffix("")

            # Skip if exists and not overwriting
            if dest_path.exists() and not self.options.overwrite:
                return

            # Render template
            content = self.renderer.render_file(rel_path, self.options.context.data)

            if not self.options.dry_run:
                # Ensure destination directory exists
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                # Write rendered content
                dest_path.write_text(content, encoding="utf-8")

            self.result.files_rendered.append(str(dest_path))
        except TemplateRenderError as e:
            self.result.add_error(
                file=str(rel_path),
                error_type="template",
                message=e.message,
                line_number=e.line,
            )
        except Exception as e:
            self.result.add_error(
                file=str(rel_path),
                error_type="io",
                message=f"Failed to render template: {e}",
            )

    def _copy_file(self, src_path: Path, dest_path: Path, rel_path: Path) -> None:
        """Copy a file as-is to destination.

        Args:
            src_path: Absolute source path
            dest_path: Destination path
            rel_path: Relative path for logging
        """
        try:
            # Skip if exists and not overwriting
            if dest_path.exists() and not self.options.overwrite:
                return

            if not self.options.dry_run:
                # Ensure destination directory exists
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                # Copy file
                shutil.copy2(src_path, dest_path)

            self.result.files_copied.append(str(rel_path))
        except Exception as e:
            self.result.add_error(
                file=str(rel_path),
                error_type="io",
                message=f"Failed to copy file: {e}",
            )

    def run(self) -> RenderResult:
        """Execute the full render pipeline.

        Returns:
            RenderResult with counts and errors
        """
        start_time = time.time()

        try:
            # Validate config_dir exists
            if not self.options.config_dir.is_dir():
                self.result.add_error(
                    file="",
                    error_type="validation",
                    message=f"Config directory not found: {self.options.config_dir}",
                )
                self.result.success = False
                return self.result

            # Create destination directory if needed
            if not self.options.dry_run:
                try:
                    self.options.dest_dir.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    self.result.add_error(
                        file="",
                        error_type="io",
                        message=f"Failed to create destination directory: {e}",
                    )
                    self.result.success = False
                    return self.result

            # Walk through config directory
            for file_path in sorted(self.options.config_dir.rglob("*")):
                if file_path.is_file():
                    # Get relative path
                    rel_path = file_path.relative_to(self.options.config_dir)
                    self._process_file(file_path, rel_path)

        finally:
            duration = time.time() - start_time
            self.result.duration_ms = duration * 1000

        return self.result
