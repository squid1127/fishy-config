"""Migration scripts for the fishy-config CLI."""

from ruamel.yaml import YAML
from pathlib import Path


def v1_to_v2(config: dict) -> dict:
    """Migration function to convert a v1 build configuration to v2."""
    config = config.copy()  # Avoid mutating the original config

    # Move output-related options into the 'options' section
    move_to_options = (
        "clean_output",
        "overwrite",
        "template_skip_prefix",
        "metadata_suffix",
        "template_suffix",
        "skip_patterns",
    )

    for key in move_to_options:
        if key in config:
            config.setdefault("options", {})[key] = config.pop(key)

    # Change 'artifacts' from a list to a dictionary if it's still a list
    if isinstance(config.get("artifacts"), list):
        artifacts_list = config.pop("artifacts")
        artifacts = {}
        for i, artifact in enumerate(artifacts_list):
            if "id" not in artifact:
                raise ValueError("Each artifact in the list must have a 'id' field.")
            artifact_id = artifact.pop("id", f"artifact_{i}")
            artifacts[artifact_id] = artifact
        config["artifacts"] = artifacts

    return config


VERSION_CURRENT = 2
MIGRATIONS = {
    1: v1_to_v2,
}


def apply_migrations(config: dict) -> dict:
    """Apply necessary migrations to the provided configuration dictionary."""
    if "version" not in config:
        config["version"] = 1

    version = config["version"]  # Default to version 1 if not specified
    if version > VERSION_CURRENT:
        raise ValueError(
            f"Config version {version} is newer than the current supported version {VERSION_CURRENT}."
        )

    while version < VERSION_CURRENT:
        migration_func = MIGRATIONS.get(version)
        if not migration_func:
            raise ValueError(f"No migration function found for version {version}.")
        config = migration_func(config)
        version += 1

    config["version"] = VERSION_CURRENT

    return config
