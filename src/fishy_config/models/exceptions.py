"""Custom exception classes for fishy-config."""


class FishyConfigError(Exception):
    """Base exception for all fishy-config errors."""

    pass


class ContextLoadError(FishyConfigError):
    """Raised when context cannot be loaded (YAML parsing, file not found, schema)."""

    pass


class ScanError(FishyConfigError):
    """Raised when scanning the source directory fails."""

    pass


class InvalidMetadataError(ScanError):
    """Raised when metadata is invalid or missing required fields."""

    pass


class FileIOError(FishyConfigError):
    """Raised when file read/write operations fail."""

    pass


class InvalidFileSyntaxError(ScanError):
    """Raised when a file has invalid syntax (e.g. invalid YAML in metadata)."""

    pass


class TemplateRenderError(FishyConfigError):
    """Raised when rendering a template fails."""


class TemplateUndefinedError(TemplateRenderError):
    """Raised when a template references an undefined variable."""

class ArtifactGenerationError(FishyConfigError):
    """Raised when generation of a build artifact fails."""