"""Integration tests for the render API."""

from pathlib import Path

import pytest
from pydantic import BaseModel

from fishy_config import render
from fishy_config.plugins.base import BasePlugin, HookContext
from fishy_config.exceptions import FishyConfigError


class DemoContext(BaseModel):
    app_name: str


class CaptureTypedContextPlugin(BasePlugin):
    name = "capture_typed_context"

    def __init__(self):
        self.seen = None

    def pre_render(self, ctx: HookContext) -> dict:
        self.seen = ctx.typed_context
        return super().pre_render(ctx)


class TestRenderAPI:
    """Tests for the high-level render() API."""

    def test_render_end_to_end(self, simple_config, tmp_dest_dir):
        """Test complete render flow from API."""
        result = render(simple_config, tmp_dest_dir)

        assert result.success
        assert (tmp_dest_dir / "config.yaml").exists()

        # Verify rendered content
        content = (tmp_dest_dir / "config.yaml").read_text()
        assert "TestProject" in content
        assert "1.0.0" in content

    def test_render_with_runtime_context(self, tmp_config_dir, tmp_dest_dir):
        """Test render with runtime context override."""
        template_file = tmp_config_dir / "config.txt.j2"
        template_file.write_text("Name: {{ app_name }}")

        result = render(
            tmp_config_dir,
            tmp_dest_dir,
            context={"app_name": "MyApp"},
        )

        assert result.success
        content = (tmp_dest_dir / "config.txt").read_text()
        assert "MyApp" in content

    def test_render_dry_run(self, simple_config, tmp_dest_dir):
        """Test render with dry_run=True doesn't write files."""
        result = render(simple_config, tmp_dest_dir, dry_run=True)

        assert result.success
        assert len(result.files_rendered) > 0
        # But files should not exist on disk
        assert not (tmp_dest_dir / "config.yaml").exists()

    def test_render_with_skip_patterns(self, tmp_config_dir, tmp_dest_dir):
        """Test render with skip patterns."""
        (tmp_config_dir / "include.txt").write_text("included")
        (tmp_config_dir / "skip.log").write_text("skipped")

        result = render(
            tmp_config_dir,
            tmp_dest_dir,
            skip_patterns=["*.log"],
        )

        assert result.success
        assert (tmp_dest_dir / "include.txt").exists()
        assert not (tmp_dest_dir / "skip.log").exists()

    def test_render_with_strict_undefined(self, tmp_config_dir, tmp_dest_dir):
        """Test render with strict_undefined=True."""
        template_file = tmp_config_dir / "config.txt.j2"
        template_file.write_text("Value: {{ missing }}")

        result = render(
            tmp_config_dir,
            tmp_dest_dir,
            strict_undefined=True,
        )

        assert not result.success
        assert len(result.errors) > 0

    def test_render_result_structure(self, simple_config, tmp_dest_dir):
        """Test that render result has expected structure."""
        result = render(simple_config, tmp_dest_dir)

        assert hasattr(result, "files_rendered")
        assert hasattr(result, "files_copied")
        assert hasattr(result, "errors")
        assert hasattr(result, "duration_ms")
        assert hasattr(result, "success")
        assert result.total_files > 0

    def test_render_nested_structure(self, nested_config, tmp_dest_dir):
        """Test render preserves nested directory structure."""
        result = render(nested_config, tmp_dest_dir)

        assert result.success
        assert (tmp_dest_dir / "db" / "postgres.conf").exists()
        assert (tmp_dest_dir / "app" / "config.json").exists()

    def test_render_accepts_path_strings(self, simple_config, tmp_dest_dir):
        """Test that render accepts string paths."""
        result = render(str(simple_config), str(tmp_dest_dir))

        assert result.success
        assert (tmp_dest_dir / "config.yaml").exists()

    def test_render_accepts_typed_context(self, tmp_config_dir, tmp_dest_dir):
        """Test that a consumer-provided typed context is available to plugins."""
        template_file = tmp_config_dir / "config.txt.j2"
        template_file.write_text("Name: {{ app_name }}")

        plugin = CaptureTypedContextPlugin()
        typed_context = DemoContext(app_name="MyApp")

        result = render(
            tmp_config_dir,
            tmp_dest_dir,
            context={"app_name": "MyApp"},
            typed_context=typed_context,
            plugins=[plugin],
        )

        assert result.success
        assert plugin.seen is not None
        assert plugin.seen.app_name == "MyApp"
        content = (tmp_dest_dir / "config.txt").read_text()
        assert "MyApp" in content
