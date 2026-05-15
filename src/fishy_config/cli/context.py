"""Context management for the CLI."""

from deepmerge.merger import Merger
from jsonschema import validate, ValidationError

from .models import ContextSource, ContextSourceType
from .exceptions import InvalidContextError, InvalidContextSchemaError

context_merger = Merger(
    [
        (dict, ["merge"]),
        (list, ["override"]),
        (set, ["union"]),
    ],
    ["override"],
    ["override"],
)

def schema_as_defaults(schema: dict) -> dict:
    """
    Convert a JSON schema into a dictionary of default values.

    Args:
        schema (dict): The JSON schema to convert.

    Returns:
        dict: A dictionary containing the default values from the schema.
    """
    defaults = {}
    properties = schema.get("properties", {})
    for key, value in properties.items():
        if "default" in value:
            defaults[key] = value["default"]
        elif value.get("type") == "object":
            defaults[key] = schema_as_defaults(value)
        elif value.get("type") == "array":
            defaults[key] = []
    return defaults

class ContextManager:
    """
    Manages the context for the CLI, allowing for merging of context from various sources.

    Attributes:
        context (dict): The current context.
        sources (list): A list of ContextSource instances representing the sources of the context.
    """

    def __init__(self):
        self._context: dict = {}
        self.sources: list[ContextSource] = []
        self._schema: dict | None = None

    def add_source(self, source: ContextSource):
        """
        Adds a new source of context and merges it into the current context.

        Args:
            source (ContextSource): The source to add.
        """
        self.sources.append(source)
        self._context = context_merger.merge(self._context, source.data)
        
    def set_schema(self, schema: dict):
        """
        Sets the JSON schema for context validation.

        Args:
            schema (dict): The JSON schema to set.
        """
        self._schema = schema

    def validate_context(self, schema: dict | None) -> None:
        """
        Validates the current context against a provided JSON schema.

        Args:
            schema (dict | None): The JSON schema to validate against. If None, internal schema is used.

        Raises:
            InvalidContextSchemaError: If the context does not conform to the schema.
        """
        schema = schema or self._schema
        if schema is None:
            raise InvalidContextSchemaError("No schema provided for context validation.")
        try:
            validate(instance=self._context, schema=schema)
        except ValidationError as e:
            raise InvalidContextSchemaError(f"Context validation failed: {e.message}") from e

    @property
    def context(self) -> dict:
        """
        Returns the current context.

        Returns:
            dict: The current context.
        """
        return self._context
    @property
    def schema(self) -> dict | None:
        """
        Returns the current JSON schema for context validation.

        Returns:
            dict | None: The current JSON schema, or None if not set.
        """
        return self._schema