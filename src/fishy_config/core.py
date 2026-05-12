from __future__ import annotations

from pathlib import Path
from shutil import copy2
from typing import Any

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined


def merge_contexts(base: dict[str, Any], update: dict[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = dict(base)
    for key, value in update.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = merge_contexts(merged[key], value)
        else:
            merged[key] = value
    return merged


class ConfigRenderer:
    def __init__(self, *, strict_undefined: bool = False) -> None:
        self.strict_undefined = strict_undefined

    def load_context(self, context_files: list[str | Path] | None = None) -> dict[str, Any]:
        context: dict[str, Any] = {}
        for context_file in context_files or []:
            with Path(context_file).open("r", encoding="utf-8") as file:
                data = yaml.safe_load(file) or {}
            if not isinstance(data, dict):
                raise TypeError(f"Context file must contain a mapping: {context_file}")
            context = merge_contexts(context, data)
        return context

    def render_directory(
        self,
        source_dir: str | Path,
        target_dir: str | Path,
        *,
        context: dict[str, Any] | None = None,
        context_files: list[str | Path] | None = None,
    ) -> None:
        source = Path(source_dir)
        target = Path(target_dir)
        target.mkdir(parents=True, exist_ok=True)

        merged_context = merge_contexts(self.load_context(context_files), context or {})
        env_kwargs: dict[str, Any] = {"loader": FileSystemLoader(str(source))}
        if self.strict_undefined:
            env_kwargs["undefined"] = StrictUndefined
        env = Environment(**env_kwargs)

        for item in source.rglob("*"):
            relative = item.relative_to(source)
            if item.is_dir():
                (target / relative).mkdir(parents=True, exist_ok=True)
                continue

            destination = target / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            if item.suffix == ".j2":
                destination = destination.with_suffix("")
                template = env.get_template(relative.as_posix())
                destination.write_text(template.render(**merged_context), encoding="utf-8")
            else:
                copy2(item, destination)
