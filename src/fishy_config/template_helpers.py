"""Collection of jinja functions and filters used in templates."""

import json
import yaml
import pathlib
import uuid
import base64
import re

# File Serialization Filters
def to_json(value) -> str:
    """Convert a value to a JSON string."""
    return json.dumps(value)
def to_yaml(value) -> str:
    """Convert a value to a YAML string."""
    return yaml.dump(value)

# Path Manipulation Filters
def as_posix(value) -> str:
    """Convert a pathlib.Path to a POSIX-style string."""
    if not isinstance(value, pathlib.Path):
        value = pathlib.Path(value)
    return value.as_posix()

# UUID Filter
def uuid4() -> str:
    """Generate a random UUID4 string."""
    return str(uuid.uuid4())

# Base64 Encoding/Decoding Filters
def to_base64(value: str) -> str:
    """Encode a string as base64."""
    return base64.b64encode(value.encode("utf-8")).decode("utf-8")
def from_base64(value: str) -> str:
    """Decode a base64 string."""
    return base64.b64decode(value.encode("utf-8")).decode("utf-8")

# String Manipulation Filters
def snake_case(value: str) -> str:
    """Convert a string to snake_case."""
    return value.lower().replace(" ", "_").replace("-", "_")
def camel_case(value: str) -> str:
    """Convert a string to camelCase."""
    parts = value.replace("-", " ").replace("_", " ").split()
    return parts[0].lower() + "".join(word.capitalize() for word in parts[1:])
def pascal_case(value: str) -> str:
    """Convert a string to PascalCase."""
    parts = value.replace("-", " ").replace("_", " ").split()
    return "".join(word.capitalize() for word in parts)

# Regex methods
def regex_replace(value: str, pattern: str, replacement: str) -> str:
    """Replace occurrences of a regex pattern in a string."""
    return re.sub(pattern, replacement, value)
def regex_search(value: str, pattern: str) -> str | None:
    """Search for a regex pattern in a string and return the first match or None."""
    match = re.search(pattern, value)
    return match.group(0) if match else None

FILTERS = {
    "to_json": to_json,
    "to_yaml": to_yaml,
    "as_posix": as_posix,
    "uuid4": uuid4,
    "to_base64": to_base64,
    "from_base64": from_base64,
    "b64encode": to_base64,
    "b64decode": from_base64,
    "snake_case": snake_case,
    "camel_case": camel_case,
    "pascal_case": pascal_case,
}
CONTEXT = {
    "regex_replace": regex_replace,
    "regex_search": regex_search,
}