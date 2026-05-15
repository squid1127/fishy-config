"""Exceptions for the CLI."""

from ..models.exceptions import FishyConfigError

class CLIError(FishyConfigError):
    """Base exception for CLI-related errors."""
    
class InvalidBuildFileError(CLIError):
    """Raised when the build configuration file is invalid or cannot be processed."""
    
class InvalidCommandError(CLIError):
    """Raised when an invalid command is provided to the CLI."""
    
class InvalidContextError(CLIError):
    """Raised when the context provided to the CLI is invalid or cannot be processed."""
    
class InvalidContextSchemaError(CLIError):
    """Raised when the context schema provided to the CLI is invalid or cannot be processed."""