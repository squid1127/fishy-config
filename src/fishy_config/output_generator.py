"""Output generator for FishyConfig."""

from pathlib import Path
from typing import List, Iterator
from logging import getLogger
from pydantic import ValidationError
import shutil

from .models.files import EnqueuedFile, FileResult
from .models.config import EngineConfig
from .models.exceptions import FileIOError
from .models.enums import FileType
from .renderer import TemplateRenderer

logger = getLogger(__name__)


class OutputGenerator:
    """Generates output files from rendered templates and produces a manifest of generated artifacts."""

    def __init__(self, config: EngineConfig, renderer: TemplateRenderer):
        self.config = config
        self.renderer = renderer

    def generate(self, enqueued_files: Iterator[EnqueuedFile]) -> Iterator[FileResult]:
        """Generate output files from the list or iterator of EnqueuedFile objects."""
        logger.info(f"Generating output files in {self.config.output_dir}...")
        for enqueued_file in enqueued_files:
            try:
                if enqueued_file.file_type == FileType.TEMPLATE:
                    rendered_content = self.renderer.render_file(enqueued_file)
                    yield FileResult(enqueued_file=enqueued_file, rendered_content=rendered_content)

                elif enqueued_file.file_type == FileType.RAW:
                    self._copy_raw_file(enqueued_file)
                    yield FileResult(enqueued_file=enqueued_file)

            except Exception as e:
                logger.exception(f"Failed to render file {enqueued_file.source}")
                yield FileResult(enqueued_file=enqueued_file, error=e)

    def _copy_raw_file(self, enqueued_file: EnqueuedFile) -> None:
        """Copy a raw file to the output directory without rendering."""
        output_path = Path()
        try:
            output_path = self.config.output_dir / enqueued_file.relative_path
            output_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(enqueued_file.source, output_path)
        except Exception as e:
            logger.exception(f"Failed to copy raw file {enqueued_file.source} to {output_path}")
            raise FileIOError(
                f"Failed to copy raw file {enqueued_file.source} to {output_path}: {str(e)}"
            ) from e
