"""Template renderer for fishy config."""

from pathlib import Path
from typing import List
from logging import getLogger
from jinja2 import Environment, StrictUndefined
from jinja2.exceptions import TemplateError, TemplateSyntaxError, UndefinedError

from .models.files import EnqueuedFile
from .models.config import EngineConfig
from .models.exceptions import TemplateRenderError, TemplateUndefinedError, FileIOError

logger = getLogger(__name__)


class TemplateRenderer:
    """Renders templates using Jinja2."""

    def __init__(self, config: EngineConfig):
        self.config = config
        self.env = Environment(undefined=StrictUndefined)

    def render(self, text: str, context: dict) -> str:
        """Render a template string with the given context, raising TemplateRenderError on failure."""
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

    def render_file(self, enqueued_file: EnqueuedFile) -> str:
        """Render a file and write the output to the configured output directory. Returns the rendered output as a string."""
        logger.debug(f"Rendering {enqueued_file.source} to {enqueued_file.relative_path}")
        try:
            context = self._build_context_for_file(enqueued_file)
            content = self._read_file(enqueued_file)
            rendered = self.render(content, context)
            self._write_file(enqueued_file, rendered)
            return rendered
        except Exception:
            logger.exception(f"Failed to render {enqueued_file.source}")
            raise

    def _build_context_for_file(self, enqueued_file: EnqueuedFile) -> dict:
        """Build the Jinja2 context for a given EnqueuedFile, including the file's metadata and relative path."""
        context = self.config.context.copy()
        context[self.config.internal_template_namespace] = {
            "metadata": enqueued_file.metadata,
            "relative_path": enqueued_file.relative_path,
            "source_path": enqueued_file.source,
        }
        return context

    def _read_file(self, enqueued_file: EnqueuedFile) -> str:
        """Read the contents of a file as text."""
        return enqueued_file.source.read_text(encoding="utf-8")

    def _write_file(self, enqueued_file: EnqueuedFile, content: str):
        """Write the rendered content to the output path."""
        output_path = self.config.output_dir / enqueued_file.relative_path
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(content, encoding="utf-8")
            logger.debug(f"Wrote {output_path}")
        except OSError:
            logger.exception(f"Failed to write {output_path}")
            raise
