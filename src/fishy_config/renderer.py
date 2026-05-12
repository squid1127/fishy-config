"""Jinja2 template rendering utilities."""

from pathlib import Path

import jinja2

from .exceptions import TemplateRenderError
from .log import get_logger

logger = get_logger(__name__)


class Jinja2Renderer:
    """Wrapper around Jinja2 for template rendering with error handling."""

    def __init__(self, config_dir: Path, strict_undefined: bool = False):
        """Initialize renderer with a config directory.

        Args:
            config_dir: Directory containing templates
            strict_undefined: If True, raises error on undefined variables;
                            if False, renders them as empty strings
        """
        self.config_dir = Path(config_dir)
        undefined_class = jinja2.StrictUndefined if strict_undefined else jinja2.DebugUndefined

        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(self.config_dir)),
            undefined=undefined_class,
            autoescape=False,  # Don't escape HTML—we're rendering config files
            trim_blocks=False,
            lstrip_blocks=False,
        )

    def render_file(self, template_path: Path, context: dict) -> str:
        """Render a single template file.

        Args:
            template_path: Path to template file (relative to config_dir)
            context: Context dictionary for rendering

        Returns:
            Rendered template content as string

        Raises:
            TemplateRenderError: If rendering fails
        """
        try:
            logger.debug("Rendering template: %s", template_path)
            # Get relative path for Jinja2 loader
            if template_path.is_absolute():
                rel_path = template_path.relative_to(self.config_dir)
            else:
                rel_path = template_path

            template = self.env.get_template(str(rel_path))
            rendered = template.render(**context)
            logger.debug("Rendered template: %s (len=%d)", template_path, len(rendered))
            return rendered
        except jinja2.TemplateNotFound as e:
            logger.exception("Template not found: %s", template_path)
            raise TemplateRenderError(
                file=str(template_path),
                line=None,
                message=f"Template not found: {e}",
            ) from e
        except jinja2.UndefinedError as e:
            logger.exception("Undefined variable while rendering: %s", template_path)
            raise TemplateRenderError(
                file=str(template_path),
                line=None,
                message=f"Undefined variable: {e}",
            ) from e
        except jinja2.TemplateSyntaxError as e:
            logger.exception("Template syntax error: %s line %s", template_path, e.lineno)
            raise TemplateRenderError(
                file=str(template_path),
                line=e.lineno,
                message=f"Template syntax error: {e.message}",
            ) from e
        except jinja2.TemplateError as e:
            logger.exception("Template rendering error: %s", template_path)
            raise TemplateRenderError(
                file=str(template_path),
                line=None,
                message=f"Template rendering error: {e}",
            ) from e
        except Exception as e:
            logger.exception("Unexpected error rendering template: %s", template_path)
            raise TemplateRenderError(
                file=str(template_path),
                line=None,
                message=f"Unexpected error rendering template: {e}",
            ) from e

    def render_string(self, template_string: str, context: dict) -> str:
        """Render a template from a string.

        Args:
            template_string: Template content as string
            context: Context dictionary for rendering

        Returns:
            Rendered content as string

        Raises:
            TemplateRenderError: If rendering fails
        """
        try:
            template = self.env.from_string(template_string)
            return template.render(**context)
        except jinja2.TemplateError as e:
            raise TemplateRenderError(
                file="<string>",
                line=None,
                message=f"Template rendering error: {e}",
            ) from e
        except Exception as e:
            raise TemplateRenderError(
                file="<string>",
                line=None,
                message=f"Unexpected error rendering template: {e}",
            ) from e
