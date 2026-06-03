""" "Config loader and manager for the fishy-config CLI."""

from .models import BuildConfig
from .exceptions import InvalidBuildFileError
from .migrations import apply_migrations

from ruamel.yaml import YAML, YAMLError
from pathlib import Path
from pydantic import ValidationError
import json

def load_config(config_path: Path, write: bool = True) -> BuildConfig:
    """Load and parse the build configuration from a YAML file."""
    config_data = _read_config(config_path)

    # Apply migrations to ensure the config is in the latest format
    migrated_config_data = apply_migrations(config_data)

    if migrated_config_data != config_data and write:
        _write_config(config_path, migrated_config_data)

    # Validate and create a BuildConfig instance
    config = _validate_config(migrated_config_data, config_path)
    
    if config.context_file:
        context_data = load_context_file(config.context_file)
        config.context.update(context_data)
    
    return config

def load_context_file(context_path: Path) -> dict:
    """Load the context file and return it as a dictionary."""
    if context_path.suffix == ".json":
        return _read_config_json(context_path)
    else:
        return _read_config(context_path)

def _read_config(config_path: Path) -> dict:
    """Read the configuration file and return it as a dictionary."""
    yaml = YAML()
    yaml.preserve_quotes = True
    try:
        with config_path.open("r") as f:
            config_data = yaml.load(f)
    except YAMLError as e:
        raise InvalidBuildFileError(f"Failed to read config file {config_path}: {e}") from e

    if not isinstance(config_data, dict):
        raise InvalidBuildFileError(
            f"Config file {config_path} must contain a YAML dictionary at the top level."
        )
            
    return config_data

def _read_config_json(config_path: Path) -> dict:
    """Read the configuration file in JSON format and return it as a dictionary."""
    try:
        with config_path.open("r") as f:
            config_data = json.load(f)
    except json.JSONDecodeError as e:
        raise InvalidBuildFileError(f"Failed to read config file {config_path} as JSON: {e}") from e

    if not isinstance(config_data, dict):
        raise InvalidBuildFileError(
            f"Config file {config_path} must contain a JSON object at the top level."
        )
            
    return config_data

def _write_config(config_path: Path, config_data: dict) -> None:
    """Write the updated configuration back to the YAML file."""
    try:
        yaml = YAML()
        yaml.preserve_quotes = True
        with config_path.open("w") as f:
            yaml.dump(config_data, f)
    except YAMLError as e:
        raise InvalidBuildFileError(f"Failed to write updated config to {config_path}: {e}") from e


def _validate_config(config_data: dict, config_path: Path) -> BuildConfig:
    """Validate the configuration data and create a BuildConfig instance."""
    try:
        config = BuildConfig(**config_data)
    except ValidationError as e:
        raise InvalidBuildFileError(f"Config file {config_path} is invalid: {e}") from e
    return config
