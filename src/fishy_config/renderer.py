"""Template renderer for fishy-config."""

from jinja2 import Environment, StrictUndefined, BaseLoader, TemplateNotFound
from jinja2.exceptions import TemplateError, TemplateSyntaxError, UndefinedError
from pathlib import Path
from typing import List
from .template_helpers import FILTERS, CONTEXT

from .log import get_logger
from .models.files import QueuedFile
from .models.config import EngineConfig
from .models.exceptions import TemplateRenderError, TemplateUndefinedError, FileIOError

logger = get_logger(__name__)


class TemplateLoader(BaseLoader):
    """Custom Jinja2 template loader that loads templates from the file system based on the queued files."""

    def __init__(self, queued_files: List[QueuedFile] | None = None):
        self.update_queued_files(queued_files or [])

    def update_queued_files(self, queued_files: List[QueuedFile]) -> None:
        """Update the internal mapping of queued files. This can be used to refresh the loader if new files are added after initialization."""
        self.queued_files = {str(qf.relative_path): qf for qf in queued_files}

    def get_source(self, environment: Environment, template: str):
        """Load a template by its relative path from the queued files."""
        if template not in self.queued_files:
            raise TemplateNotFound(f"Template not found: {template}")
        queued_file = self.queued_files[template]
        try:
            source = queued_file.source.read_text(encoding="utf-8")
            return source, str(queued_file.source), lambda: True
        except OSError as e:
            logger.exception(f"Failed to read template file {queued_file.source}")
            raise FileIOError(f"Failed to read template file {queued_file.source}: {str(e)}") from e


class TemplateRenderer:
    """Renders templates using Jinja2."""

    def __init__(self, config: EngineConfig):
        self.config = config
        self.loader = TemplateLoader()
        self.env = Environment(
            undefined=StrictUndefined, loader=self.loader
        )
        self.env.filters.update(FILTERS)
        self.env.globals.update(CONTEXT)

    def render(self, text: str, context: dict | None, internal_context: dict | None) -> str:
        """Render a template string with the given context, raising TemplateRenderError on failure."""
        context = context or self.config.context or {}
        context = context.copy()  # Avoid mutating the original context

        if internal_context:
            context[self.config.output_config.internal_template_namespace] = internal_context
        try:
            template = self.env.from_string(text)
            return template.render(context)
        except UndefinedError as e:
            logger.exception("Undefined variable in template")
            raise TemplateUndefinedError(f"Undefined variable in template: {str(e)}") from e
        except TemplateSyntaxError as e:
            logger.exception("Template syntax error")
            raise TemplateRenderError(f"Syntax error in template: {str(e)}") from e
        except TemplateError as e:
            logger.exception("Template render error")
            raise TemplateRenderError(f"Error rendering template: {str(e)}") from e

    def render_file(self, queued_file: QueuedFile) -> str:
        """Render a file and write the output to the configured output directory. Returns the rendered output as a string."""
        logger.debug(f"Rendering {queued_file.source} to {queued_file.relative_path}")
        try:
            content = self._read_file(queued_file)
            internal_context = self._build_internal_context(queued_file)
            rendered = self.render(content, self.config.context, internal_context)
            self._write_file(queued_file, rendered)
            return rendered
        except Exception:
            logger.exception(f"Failed to render {queued_file.source}")
            raise

    def _build_internal_context(self, queued_file: QueuedFile) -> dict:
        """Build the internal context for a queued file, which includes metadata and other information that can be used in templates."""
        return {
            "metadata": queued_file.metadata,
            "relative_path": queued_file.relative_path,
            "path": queued_file.relative_path,
            "source_path": queued_file.source,
        }

    def _read_file(self, queued_file: QueuedFile) -> str:
        """Read the contents of a file as text."""
        return queued_file.source.read_text(encoding="utf-8")

    def _write_file(self, queued_file: QueuedFile, content: str):
        """Write the rendered content to the output path."""
        output_path = self.config.output_dir / queued_file.relative_path
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(content, encoding="utf-8")
            logger.debug(f"Wrote {output_path}")
        except OSError:
            logger.exception(f"Failed to write {output_path}")
            raise
