"""Custom exception classes for fishy-config."""


class FishyConfigError(Exception):
    """Base exception for all fishy-config errors."""

    pass


class ContextLoadError(FishyConfigError):
    """Raised when context cannot be loaded (YAML parsing, file not found, schema)."""

    pass


class ContextMergeError(FishyConfigError):
    """Raised when context merge operation fails."""

    pass


class TemplateRenderError(FishyConfigError):
    """Raised when Jinja2 template rendering fails."""

    def __init__(self, file: str, line: int | None, message: str):
        self.file = file
        self.line = line
        self.message = message
        line_info = f":{line}" if line is not None else ""
        super().__init__(f"{file}{line_info} - {message}")


class FileIOError(FishyConfigError):
    """Raised when file read/write operations fail."""

    pass


class ConfigValidationError(FishyConfigError):
    """Raised when config validation fails."""

    pass


class PluginError(FishyConfigError):
    """Raised when plugin hook execution fails."""

    pass
