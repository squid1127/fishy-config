"""Plugin discovery and loading helpers."""

from __future__ import annotations

from importlib import metadata
from importlib import import_module
from inspect import isclass
from typing import Any

from .base import BasePlugin, Plugin

DEFAULT_PLUGIN_GROUP = "fishy_config.plugins"


def load_object(spec: str) -> Any:
    """Load an object from a "module:attr" or "module.attr" spec."""

    if ":" in spec:
        module_name, attr_name = spec.split(":", 1)
    else:
        module_name, attr_name = spec.rsplit(".", 1)

    module = import_module(module_name)
    return getattr(module, attr_name)


def _coerce_plugin(value: Any) -> Plugin:
    if isinstance(value, BasePlugin):
        return value

    if isinstance(value, str):
        value = load_object(value)

    if isclass(value):
        value = value()

    if not hasattr(value, "on_run_start") and not hasattr(value, "should_skip"):
        raise TypeError(f"Object is not a plugin: {value!r}")

    return value


def discover_plugins(group: str = DEFAULT_PLUGIN_GROUP) -> list[Plugin]:
    """Load plugins from entry points."""

    discovered: list[Plugin] = []
    entry_points = metadata.entry_points()
    candidates = (
        entry_points.select(group=group)
        if hasattr(entry_points, "select")
        else entry_points.get(group, [])
    )

    for entry_point in candidates:
        plugin = _coerce_plugin(entry_point.load())
        discovered.append(plugin)

    return discovered


def resolve_plugins(
    plugins: list[Any] | None = None,
    *,
    discover: bool = False,
    group: str = DEFAULT_PLUGIN_GROUP,
) -> list[Plugin]:
    """Resolve plugin specs, classes, instances, and optionally entry points."""

    resolved: list[Plugin] = []

    if discover:
        resolved.extend(discover_plugins(group=group))

    for plugin in plugins or []:
        resolved.append(_coerce_plugin(plugin))

    return resolved
