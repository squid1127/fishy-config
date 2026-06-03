"""Source directory scanner for fishy-config."""

from fnmatch import fnmatchcase
import yaml
from pathlib import Path
from typing import Iterator, TypeVar
from pydantic import ValidationError

from .log import get_logger
from .models.files import FileMetadata, DirectoryMetadata, QueuedFile, FailedFile
from .models.config import EngineConfig
from .models.exceptions import InvalidMetadataError, TemplateRenderError
from .models.enums import FileType
from .renderer import TemplateRenderer

logger = get_logger(__name__)

MetadataModel = TypeVar("MetadataModel", FileMetadata, DirectoryMetadata)


class SourceTreeScanner:
    """
    Scans a source directory and generates QueuedFile objects representing discovered files and their associated metadata.
    """

    def __init__(
        self, config: EngineConfig, renderer: TemplateRenderer, source_dir: Path | None = None
    ):
        self.config = config
        self.renderer = renderer
        self.source_dir = source_dir or config.source_dir
        if not (self.source_dir and self.source_dir.is_dir()):
            raise ValueError(
                f"Source directory {self.source_dir} does not exist or is not a directory."
            )

    def scan_and_raise(self) -> Iterator[QueuedFile]:
        """Scan the source directory and yield QueuedFile objects, raising exceptions on errors."""
        for result in self.scan():
            if isinstance(result, FailedFile):
                logger.error(f"Failed to queue file {result.source}: {result.error}")
                raise result.error
            yield result

    def scan(self) -> Iterator[QueuedFile | FailedFile]:
        """Return an iterator of QueuedFile objects representing the files to be rendered from the source directory."""

        logger.info(f"Scanning source directory {self.source_dir} for files to render...")

        if not self.source_dir.is_dir():
            raise ValueError(
                f"Source directory {self.source_dir} does not exist or is not a directory."
            )

        yield from self._iter_queued_files(self.source_dir, Path())

    def _iter_queued_files(self, path: Path, rel_path: Path) -> Iterator[QueuedFile | FailedFile]:
        """Recursively iterate QueuedFile objects under `path`.

        `rel_path` is the path to use for files under `path` unless overridden by
        directory or file metadata.
        """

        if not path.is_dir():
            raise ValueError(f"Path {path} is not a directory.")

        try:
            # Read directory metadata
            meta = self._read_dir_metadata(path, rel_path)
            if meta.skip or self._matches_skip_patterns(rel_path.as_posix(), is_dir=True):
                logger.debug(f"Skipping directory {path} due to metadata skip flag")
                return

            rel_path = self._manipulate_rel_path(rel_path, meta)
            items = self._get_items(path, meta)

        except Exception as e:
            logger.exception(f"Error processing directory {path}")
            yield FailedFile(source=path, relative_path=rel_path, error=e)
            return

        for item in items:
            if item.is_dir():
                yield from self._iter_queued_files(item, rel_path / item.name)
                continue
            result = self._build_queued_file(item, rel_path / item.name)
            if result is not None:
                yield result

    def _build_queued_file(self, item: Path, item_rel: Path) -> QueuedFile | FailedFile | None:
        """Build an QueuedFile for `item`, or return a FailedFile when it should be skipped or an error occurs."""
        try:
            item_path = item_rel

            if item.name.endswith(self.config.output_config.metadata_suffix):
                logger.debug(f"Skipping metadata file {item}")
                return

            if self._matches_skip_patterns((item_rel).as_posix(), is_dir=False):
                logger.debug(f"Skipping file {item} due to skip patterns")
                return

            file_meta = self._read_file_metadata(item, item_rel)
            if file_meta.skip:
                logger.debug(f"Skipping file {item} due to metadata skip flag")
                return
            item_path = self._manipulate_rel_path(item_rel, file_meta)
            if item_path.suffix == self.config.output_config.template_suffix:
                item_path = item_path.with_suffix("")
            file_type = (
                FileType.TEMPLATE
                if item.suffix == self.config.output_config.template_suffix
                else FileType.RAW
            )
            return QueuedFile(
                source=item, relative_path=item_path, file_type=file_type, metadata=file_meta
            )

        except Exception as e:
            logger.exception(f"Error processing file {item}")
            return FailedFile(source=item, relative_path=item_rel, error=e)

    def _get_items(self, path: Path, meta: DirectoryMetadata) -> list[Path]:
        """Get the list of items to process under a directory, applying flattening if specified."""
        if meta.variant:
            path = path / meta.variant
            if not path.is_dir():
                if meta.variant_skip_if_missing:
                    logger.debug(f"Skipping directory {path} due to missing variant")
                    return []
                raise InvalidMetadataError(
                    f"Variant directory {path} does not exist for variant key {meta.variant} (Set variant_skip_if_missing to true to skip instead of erroring)"
                )

        if meta.flatten:
            return sorted(path.glob("**/*"))
        else:
            return sorted(path.iterdir())

    def _manipulate_rel_path(
        self,
        path: Path,
        meta: FileMetadata | DirectoryMetadata,
    ) -> Path:
        """Manipulate relative path based on metadata overrides."""
        if meta.path:
            if meta.path_absolute:
                path = meta.path
            else:
                path = path / meta.path

        if meta.name:
            path = path.with_name(meta.name)

        return path

    def _read_dir_metadata(self, path: Path, rel_path: Path) -> DirectoryMetadata:
        """Read and validate directory metadata from the configured suffix."""
        return DirectoryMetadata(
            **self._read_metadata_raw(
                path,
                internal_context={
                    "source_path": path,
                    "relative_path": rel_path,
                    "config": self.config,
                },
            )
        )

    def _read_file_metadata(self, file_path: Path, rel_path: Path) -> FileMetadata:
        """Read and validate file-level metadata (file + metadata_suffix).

        Metadata files are expected at `file.<suffix><metadata_suffix>` to
        preserve the previous behavior.
        """
        return FileMetadata(
            **self._read_metadata_raw(
                file_path,
                internal_context={
                    "source_path": file_path,
                    "relative_path": rel_path,
                    "config": self.config,
                },
            )
        )

    def _read_metadata_raw(self, path: Path, internal_context: dict | None = None) -> dict:
        """Read and return raw metadata from a YAML file."""
        if path.is_file():
            metadata_path = path.with_name(path.name + self.config.output_config.metadata_suffix)
        elif path.is_dir():
            metadata_path = path / self.config.output_config.metadata_suffix
        else:
            raise ValueError(f"Path {path} is neither a file nor a directory.")

        if not metadata_path.is_file():
            return {}
        return self._read_yaml(metadata_path, internal_context=internal_context)

    def _read_yaml(
        self, yaml_path: Path, template: bool = True, internal_context: dict | None = None
    ) -> dict:
        """Read and return data from a YAML file. If `template` is True, render the file as a template before parsing."""
        try:
            text = yaml_path.read_text(encoding="utf-8")
            if template:
                text = self.renderer.render(text, None, internal_context)
            return yaml.safe_load(text) or {}
        except OSError as e:
            logger.exception(f"Failed to read metadata file {yaml_path}")
            raise InvalidMetadataError(f"Failed to read metadata file {yaml_path}") from e
        except yaml.YAMLError as e:
            logger.exception(f"Failed to parse YAML metadata from {yaml_path}")
            raise InvalidMetadataError(f"Failed to read metadata from {yaml_path}") from e

    def _matches_skip_patterns(self, relative: str, is_dir: bool) -> bool:
        """Check whether a relative path matches any configured skip pattern."""
        patterns = self.config.output_config.skip_patterns
        candidates = [relative, f"{relative}/"] if is_dir else [relative]
        for pattern in patterns:
            if any(fnmatchcase(candidate, pattern) for candidate in candidates):
                return True
            if is_dir and pattern.endswith("/**"):
                base = pattern[:-3].rstrip("/")
                if base and (relative == base or relative.startswith(f"{base}/")):
                    return True
        return False
