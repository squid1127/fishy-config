"""Simple utility to generate create JSON schema files for Pydantic models defined in the codebase."""

from pathlib import Path
from pydantic import BaseModel, Field
import json

from .models import BuildConfig
from ..models.files import FileMetadata, DirectoryMetadata

SCHEMAS: dict[tuple[str, str], type[BaseModel]] = {
    ("fishy-config_file_metadata", "**/*.meta.yaml"): FileMetadata,
    ("fishy-config_directory_metadata", "**/.meta.yaml"): DirectoryMetadata,
    ("fishy-config_build", "**/build.yaml"): BuildConfig,
}
ID_KEY = "x-fishy-config-schema-id"
JSON_SETTINGS_KEY = "json.schemas"

def generate_schemas(output_dir: Path) -> None:
    """Generate JSON schema files for the defined Pydantic models."""
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[tuple[str, str], Path] = {}
    for (name, pattern), model in SCHEMAS.items():
        schema = model.model_json_schema()
        schema_file = output_dir / f"{name}.schema.json"
        paths[name, pattern] =  schema_file
        with schema_file.open("w") as f:
            json.dump(schema, f, indent=4)

def generate_vs_code_settings(vs_code_settings: Path) -> None:
        if vs_code_settings.exists():
            with vs_code_settings.open("r") as f:
                settings = json.load(f)
        else:
            settings = {}
        if JSON_SETTINGS_KEY not in settings:
            settings[JSON_SETTINGS_KEY] = []
        for schema in settings[JSON_SETTINGS_KEY].copy():
            if ID_KEY in schema:
                settings[JSON_SETTINGS_KEY].remove(schema)
        for (name, pattern), model in SCHEMAS.items():
            settings[JSON_SETTINGS_KEY].append({
                "fileMatch": [
                    pattern
                ],
                "schema": model.model_json_schema(),
                ID_KEY: True
            })
        with vs_code_settings.open("w") as f:
            json.dump(settings, f, indent=4)