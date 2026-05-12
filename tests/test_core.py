from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fishy_config.core import ConfigRenderer, merge_contexts


class MergeContextsTests(unittest.TestCase):
    def test_recursively_merges_nested_dictionaries(self) -> None:
        base = {"a": 1, "nested": {"one": 1, "two": 2}}
        update = {"nested": {"two": 22, "three": 3}, "b": 2}

        result = merge_contexts(base, update)

        self.assertEqual(
            result,
            {"a": 1, "b": 2, "nested": {"one": 1, "two": 22, "three": 3}},
        )


class ConfigRendererTests(unittest.TestCase):
    def test_render_directory_renders_j2_and_copies_non_templates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "src"
            target = root / "out"
            source.mkdir()
            (source / "config.yaml.j2").write_text("name: {{ name }}\n", encoding="utf-8")
            (source / "README.txt").write_text("raw-content", encoding="utf-8")
            (source / "ctx.yaml").write_text("name: fishy\n", encoding="utf-8")

            renderer = ConfigRenderer()
            renderer.render_directory(
                source,
                target,
                context_files=[source / "ctx.yaml"],
            )

            self.assertEqual(
                (target / "config.yaml").read_text(encoding="utf-8").strip(),
                "name: fishy",
            )
            self.assertEqual((target / "README.txt").read_text(encoding="utf-8"), "raw-content")

    def test_inline_context_overrides_file_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "src"
            target = root / "out"
            source.mkdir()
            (source / "config.yaml.j2").write_text("name: {{ name }}\n", encoding="utf-8")
            (source / "ctx.yaml").write_text("name: fishy\n", encoding="utf-8")

            renderer = ConfigRenderer()
            renderer.render_directory(
                source,
                target,
                context_files=[source / "ctx.yaml"],
                context={"name": "override"},
            )

            self.assertEqual(
                (target / "config.yaml").read_text(encoding="utf-8").strip(),
                "name: override",
            )


if __name__ == "__main__":
    unittest.main()
