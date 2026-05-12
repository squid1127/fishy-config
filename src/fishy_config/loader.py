"""Context loading and merging utilities."""

from pathlib import Path
from typing import Any

import yaml

from .exceptions import ContextLoadError, ContextMergeError
from .models import ContextConfig, ContextSource, MergeStrategy
from .log import get_logger

logger = get_logger(__name__)


def load_yaml_file(path: Path) -> dict[str, Any]:
    """Load a YAML file and return its contents as a dict.

    Args:
        path: Path to YAML file

    Returns:
        Parsed YAML content as dictionary

    Raises:
        ContextLoadError: If file cannot be read or parsed
    """
    try:
        logger.debug("Loading YAML file: %s", path)
        with open(path, "r", encoding="utf-8") as f:
            content = yaml.safe_load(f)
            if not isinstance(content, dict):
                raise ContextLoadError(f"YAML file must contain a dict, got {type(content)}")
            return content or {}
    except FileNotFoundError as e:
        raise ContextLoadError(f"Context file not found: {path}") from e
    except yaml.YAMLError as e:
        raise ContextLoadError(f"Failed to parse YAML file {path}: {e}") from e
    except Exception as e:
        raise ContextLoadError(f"Failed to load context file {path}: {e}") from e


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge override dict into base dict.

    Override values take precedence. Nested dicts are merged recursively;
    other types are replaced.

    Args:
        base: Base dictionary
        override: Override dictionary

    Returns:
        Merged dictionary (modifies base in-place)
    """
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            deep_merge(base[key], value)
        else:
            base[key] = value
    return base


def shallow_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Shallow merge: only top-level keys are merged.

    Override values take precedence at the top level; nested structures
    are replaced entirely.

    Args:
        base: Base dictionary
        override: Override dictionary

    Returns:
        Merged dictionary (modifies base in-place)
    """
    base.update(override)
    return base


def merge_contexts(
    base: dict[str, Any],
    override: dict[str, Any],
    strategy: MergeStrategy = MergeStrategy.DEEP,
) -> dict[str, Any]:
    """Merge override context into base context using specified strategy.

    Args:
        base: Base context dictionary
        override: Override context dictionary (takes precedence)
        strategy: Merge strategy to use

    Returns:
        Merged context dictionary

    Raises:
        ContextMergeError: If merge fails
    """
    try:
        if strategy == MergeStrategy.DEEP:
            return deep_merge(base.copy(), override)
        elif strategy == MergeStrategy.SHALLOW:
            return shallow_merge(base.copy(), override)
        elif strategy == MergeStrategy.REPLACE:
            return override.copy()
        else:
            raise ContextMergeError(f"Unknown merge strategy: {strategy}")
    except Exception as e:
        if isinstance(e, ContextMergeError):
            raise
        raise ContextMergeError(f"Failed to merge contexts: {e}") from e


def load_context(
    config_dir: Path,
    runtime_data: dict[str, Any] | None = None,
    context_file: str = "context.yaml",
) -> ContextConfig:
    """Load and merge context from config directory and runtime data.

    Loads context.yaml from config_dir if it exists, then merges in any
    runtime_data. Runtime data takes precedence.

    Args:
        config_dir: Root directory containing config files
        runtime_data: Runtime context data (overrides YAML)
        context_file: Name of context file in config_dir

    Returns:
        Merged ContextConfig with loaded data

    Raises:
        ContextLoadError: If context cannot be loaded
    """
    data: dict[str, Any] = {}
    sources: list[ContextSource] = []

    # Try to load context.yaml from config_dir
    yaml_path = config_dir / context_file
    if yaml_path.exists():
        try:
            logger.debug("Found context file: %s", yaml_path)
            yaml_data = load_yaml_file(yaml_path)
            data = yaml_data
            sources.append(ContextSource(path=yaml_path, merge_strategy=MergeStrategy.DEEP))
        except ContextLoadError:
            # If context file exists but can't be parsed, fail
            logger.exception("Failed to load context YAML: %s", yaml_path)
            raise

    # Merge runtime data (takes precedence)
    if runtime_data:
        logger.debug("Merging runtime context (overrides YAML)")
        data = merge_contexts(data, runtime_data, MergeStrategy.DEEP)
        sources.append(ContextSource(path=Path("<runtime>"), merge_strategy=MergeStrategy.DEEP))

    return ContextConfig(
        data=data,
        sources=sources,
        metadata={
            "config_dir": str(config_dir),
            "context_file": context_file,
        },
    )
