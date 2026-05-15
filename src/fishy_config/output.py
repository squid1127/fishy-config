"""Output generator for fishy-config."""

import shutil
from pathlib import Path
from typing import Iterable, Iterator, List

from pydantic import ValidationError

from .log import get_logger
from .models.files import QueuedFile, FileResult
from .models.config import EngineConfig
from .models.exceptions import FileIOError
from .models.enums import FileType
from .renderer import TemplateRenderer

logger = get_logger(__name__)


class OutputBuilder:
    """Generates output files from rendered templates and produces a list of FileResult objects for each generated file."""

    def __init__(self, config: EngineConfig, renderer: TemplateRenderer):
        self.config = config
        self.renderer = renderer

    def clean_output_directory(self) -> None:
        """Clean the output directory if the clean_output flag is set in the configuration."""
        if self.config.clean_output:
            logger.info(f"Cleaning output directory {self.config.output_dir}...")
            try:
                if self.config.output_dir.exists():
                    shutil.rmtree(self.config.output_dir)
                self.config.output_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logger.exception(f"Failed to clean output directory {self.config.output_dir}")
                raise FileIOError(
                    f"Failed to clean output directory {self.config.output_dir}: {str(e)}"
                ) from e

    def generate(
        self,
        queued_files: Iterable[QueuedFile] | List[QueuedFile],
        sort: bool = True,
        clean: bool = True,
    ) -> Iterator[FileResult]:
        """Generate output files from the list or iterator of QueuedFile objects."""
        logger.info(f"Generating output files in {self.config.output_dir}...")
        if sort and isinstance(queued_files, list):
            queued_files = self._sort_queued_files(queued_files)
        if clean:
            self.clean_output_directory()
        for queued_file in queued_files:
            try:
                if queued_file.file_type == FileType.TEMPLATE:
                    rendered_content = self.renderer.render_file(queued_file)
                    yield FileResult(queued_file=queued_file, rendered_content=rendered_content)

                elif queued_file.file_type == FileType.RAW:
                    self._copy_raw_file(queued_file)
                    yield FileResult(queued_file=queued_file)

            except Exception as e:
                logger.exception(f"Failed to render file {queued_file.source}")
                yield FileResult(queued_file=queued_file, error=e)

    def _copy_raw_file(self, queued_file: QueuedFile) -> None:
        """Copy a raw file to the output directory without rendering."""
        output_path = Path()
        try:
            output_path = self.config.output_dir / queued_file.relative_path
            output_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(queued_file.source, output_path)
            logger.debug(f"Copied raw file {queued_file.source} to {output_path}")
        except Exception as e:
            logger.exception(f"Failed to copy raw file {queued_file.source} to {output_path}")
            raise FileIOError(
                f"Failed to copy raw file {queued_file.source} to {output_path}: {str(e)}"
            ) from e

    def _sort_queued_files(self, queued_files: List[QueuedFile]) -> List[QueuedFile]:
        """Sort queued files to ensure that directories are created before files."""
        return sorted(
            queued_files,
            key=lambda f: (f.metadata.priority, f.file_type == FileType.TEMPLATE, f.relative_path),
        )
