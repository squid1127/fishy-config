"""Source directory scanner for fishy-config."""

from pathlib import Path
from typing import Iterator, TypeVar
from logging import getLogger
import yaml
from pydantic import ValidationError

from .models.files import FileMetadata, DirectoryMetadata, EnqueuedFile
from .models.config import EngineConfig
from .models.exceptions import InvalidMetadataError, TemplateRenderError
from .models.enums import FileType
from .renderer import TemplateRenderer

logger = getLogger(__name__)

MetadataModel = TypeVar("MetadataModel", FileMetadata, DirectoryMetadata)


class SourceScanner:
    """Scans a source directory and produces metadata for files and directories.

    The implementation here factors out metadata reading and yields
    EnqueuedFile objects from a single recursive generator, keeping the
    relative-path resolution logic in one place.
    """

    def __init__(self, config: EngineConfig, renderer: TemplateRenderer):
        self.config = config
        self.renderer = renderer

    def scan(self, source_dir: Path) -> Iterator[EnqueuedFile]:
        """Return an iterator of EnqueuedFile objects representing the files to be rendered from the source directory."""
        logger.info(f"Scanning source directory {source_dir} for files to render...")

        if not source_dir.is_dir():
            raise ValueError(f"Source directory {source_dir} does not exist or is not a directory.")
        yield from self._iter_enqueued_files(source_dir, Path())

    def _iter_enqueued_files(self, path: Path, rel_path: Path) -> Iterator[EnqueuedFile]:
        """Recursively iterate EnqueuedFile objects under `path`.

        `rel_path` is the path to use for files under `path` unless overridden by
        directory or file metadata.
        """
        if not path.is_dir():
            raise ValueError(f"Path {path} is not a directory.")

        dir_meta = self._read_directory_metadata_or_skip(path, rel_path)
        if dir_meta is None or dir_meta.skip:
            return

        base_rel = self._resolve_directory_base_path(rel_path, dir_meta)

        for item in sorted(path.iterdir()):
            if item.is_dir():
                yield from self._iter_enqueued_files(item, base_rel / item.name)
                continue

            enqueued = self._build_enqueued_file(item, base_rel)
            if enqueued is not None:
                yield enqueued

    def _read_directory_metadata_or_skip(
        self, path: Path, rel_path: Path
    ) -> DirectoryMetadata | None:
        """Read directory metadata, returning None when metadata is invalid."""
        try:
            return self._read_dir_metadata(path, rel_path)
        except InvalidMetadataError as e:
            logger.warning(f"Skipping directory {path} due to invalid metadata: {e}")
            return None

    def _resolve_directory_base_path(self, rel_path: Path, dir_meta: DirectoryMetadata) -> Path:
        """Resolve the relative output base path for a directory."""
        if not dir_meta.path:
            return rel_path
        return dir_meta.path if dir_meta.path.is_absolute() else rel_path / dir_meta.path

    def _build_enqueued_file(self, item: Path, base_rel: Path) -> EnqueuedFile | None:
        """Build an EnqueuedFile for `item`, or return None when it should be skipped."""
        file_meta = self._read_file_metadata_or_skip(item, base_rel)
        if file_meta is None or file_meta.skip:
            return None

        relative = self._resolve_file_relative_path(item, base_rel, file_meta)
        file_type = (
            FileType.TEMPLATE if item.suffix == self.config.template_suffix else FileType.RAW
        )
        return EnqueuedFile(
            source=item, relative_path=relative, file_type=file_type, metadata=file_meta
        )

    def _read_file_metadata_or_skip(self, file_path: Path, rel_path: Path) -> FileMetadata | None:
        """Read file metadata, returning None when metadata is invalid."""
        try:
            return self._read_file_metadata(file_path, rel_path)
        except InvalidMetadataError as e:
            logger.warning(f"Skipping file {file_path} due to invalid metadata: {e}")
            return None

    def _resolve_file_relative_path(
        self, item: Path, base_rel: Path, file_meta: FileMetadata
    ) -> Path:
        """Resolve relative output path for a file after metadata overrides."""
        relative = base_rel / item.name

        if file_meta.path:
            try:
                relative = (
                    file_meta.path.relative_to("/")
                    if file_meta.path.is_absolute()
                    else base_rel / file_meta.path
                )
            except ValueError:
                logger.warning(
                    f"Invalid file path metadata {file_meta.path} for {item}, using base relative path {base_rel}"
                )
                relative = base_rel / item.name

        if file_meta.rename:
            relative = relative.with_name(file_meta.rename)

        return relative

    def _read_dir_metadata(self, path: Path, rel_path: Path) -> DirectoryMetadata:
        """Read and validate directory metadata from the configured suffix."""
        config_file = path / self.config.metadata_suffix
        meta = self._read_metadata(config_file, DirectoryMetadata, "directory", rel_path)
        logger.debug(f"Read directory metadata from {config_file}")
        return meta

    def _read_file_metadata(self, file_path: Path, rel_path: Path) -> FileMetadata:
        """Read and validate file-level metadata (file + metadata_suffix).

        Metadata files are expected at `file.<suffix><metadata_suffix>` to
        preserve the previous behavior.
        """
        metadata_file = file_path.with_suffix(file_path.suffix + self.config.metadata_suffix)
        meta = self._read_metadata(metadata_file, FileMetadata, "file", rel_path)
        if metadata_file.is_file():
            logger.debug(f"Read file metadata from {metadata_file}")
        return meta

    def _read_metadata(
        self,
        metadata_path: Path,
        metadata_model: type[MetadataModel],
        metadata_kind: str,
        rel_path: Path,
    ) -> MetadataModel:
        """Read and parse metadata from `metadata_path` into a typed model."""
        if not metadata_path.is_file():
            return metadata_model()

        try:
            data = self._read_yaml_metadata(metadata_path, rel_path)
            return metadata_model(**data)
        except (InvalidMetadataError, ValidationError) as e:
            raise InvalidMetadataError(
                f"Failed to read {metadata_kind} metadata from {metadata_path}: {e}"
            ) from e

    def _read_yaml_metadata(self, yaml_path: Path, relative_path: Path) -> dict:
        """Read and validate metadata from a YAML file."""
        if not yaml_path.is_file():
            raise InvalidMetadataError(f"Metadata file {yaml_path} does not exist.")

        try:
            text = yaml_path.read_text(encoding="utf-8")
        except OSError:
            logger.exception(f"Failed to read metadata file {yaml_path}")
            raise InvalidMetadataError(f"Failed to read metadata file {yaml_path}") from None

        try:
            context = self.config.context.copy()
            context[self.config.internal_template_namespace] = {
                "source_path": yaml_path,
                "relative_path": relative_path,
                "config": self.config,
            }
            rendered_text = self.renderer.render(text, context)
        except TemplateRenderError:
            logger.exception(f"Failed to render metadata template {yaml_path}")
            raise InvalidMetadataError(f"Failed to render metadata template {yaml_path}") from None

        try:
            data = yaml.safe_load(rendered_text)
            if not isinstance(data, dict):
                logger.error(f"Metadata file {yaml_path} is not a dictionary at top level")
                raise InvalidMetadataError(
                    f"Metadata file {yaml_path} must contain a YAML dictionary at the top level."
                )
            return data
        except yaml.YAMLError:
            logger.exception(f"Failed to parse YAML metadata from {yaml_path}")
            raise InvalidMetadataError(f"Failed to read metadata from {yaml_path}") from None
