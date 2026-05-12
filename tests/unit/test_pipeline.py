"""Unit tests for pipeline module."""

from pathlib import Path

import pytest

from fishy_config.loader import load_context
from fishy_config.models import ContextConfig, RenderOptions
from fishy_config.pipeline import RenderPipeline
from fishy_config.plugins.builtins import RewriteRelativePathPlugin, SkipIfContextMissingPlugin


class TestRenderPipeline:
    """Tests for RenderPipeline class."""

    def test_pipeline_simple_render(self, simple_config, tmp_dest_dir):
        """Test basic pipeline execution with simple config."""
        ctx = load_context(simple_config)
        options = RenderOptions(
            config_dir=simple_config,
            dest_dir=tmp_dest_dir,
            context=ctx,
        )

        pipeline = RenderPipeline(options)
        result = pipeline.run()

        # Check that files were processed
        assert result.success
        assert len(result.files_rendered) > 0
        assert len(result.files_copied) > 0

    def test_pipeline_template_rendering(self, simple_config, tmp_dest_dir):
        """Test that templates are rendered correctly."""
        ctx = load_context(simple_config)
        options = RenderOptions(
            config_dir=simple_config,
            dest_dir=tmp_dest_dir,
            context=ctx,
        )

        pipeline = RenderPipeline(options)
        result = pipeline.run()

        # Check rendered file
        rendered_file = tmp_dest_dir / "config.yaml"
        assert rendered_file.exists()
        content = rendered_file.read_text()
        assert "TestProject" in content
        assert "1.0.0" in content

    def test_pipeline_static_file_copy(self, tmp_config_dir, tmp_dest_dir):
        """Test that static files are copied (not .md as those are skipped by default)."""
        # Create context and static file (not .md which is skipped by default)
        (tmp_config_dir / "context.yaml").write_text("name: test")
        (tmp_config_dir / "config.txt").write_text("Static content")

        ctx = load_context(tmp_config_dir)
        options = RenderOptions(
            config_dir=tmp_config_dir,
            dest_dir=tmp_dest_dir,
            context=ctx,
        )

        pipeline = RenderPipeline(options)
        result = pipeline.run()

        # Check static file was copied
        static_file = tmp_dest_dir / "config.txt"
        assert static_file.exists()
        content = static_file.read_text()
        assert "Static content" in content

    def test_pipeline_dry_run(self, simple_config, tmp_dest_dir):
        """Test dry-run mode doesn't write files."""
        ctx = load_context(simple_config)
        options = RenderOptions(
            config_dir=simple_config,
            dest_dir=tmp_dest_dir,
            context=ctx,
            dry_run=True,
        )

        pipeline = RenderPipeline(options)
        result = pipeline.run()

        # Files should be in result but not on disk
        assert len(result.files_rendered) > 0
        assert not (tmp_dest_dir / "config.yaml").exists()

    def test_pipeline_skip_patterns(self, tmp_config_dir, tmp_dest_dir):
        """Test that skip patterns exclude files."""
        # Create test files
        (tmp_config_dir / "include.txt").write_text("included")
        (tmp_config_dir / "skip.md").write_text("skipped")

        ctx = load_context(tmp_config_dir)
        options = RenderOptions(
            config_dir=tmp_config_dir,
            dest_dir=tmp_dest_dir,
            context=ctx,
            skip_patterns=["*.md"],
        )

        pipeline = RenderPipeline(options)
        result = pipeline.run()

        # Check that .md file was skipped
        assert (tmp_dest_dir / "include.txt").exists()
        assert not (tmp_dest_dir / "skip.md").exists()

    def test_pipeline_nested_directory_structure(self, nested_config, tmp_dest_dir):
        """Test that nested directory structure is preserved."""
        ctx = load_context(nested_config)
        options = RenderOptions(
            config_dir=nested_config,
            dest_dir=tmp_dest_dir,
            context=ctx,
        )

        pipeline = RenderPipeline(options)
        result = pipeline.run()

        # Check directory structure
        assert (tmp_dest_dir / "db" / "postgres.conf").exists()
        assert (tmp_dest_dir / "app" / "config.json").exists()

    def test_pipeline_invalid_config_dir(self, tmp_dest_dir):
        """Test error handling for invalid config directory."""
        invalid_dir = Path("/nonexistent/path")
        ctx = (
            load_context(invalid_dir)
            if invalid_dir.exists()
            else type("obj", (object,), {"data": {}})()
        )

        from fishy_config.models import ContextConfig

        if not isinstance(ctx, ContextConfig):
            ctx = ContextConfig()

        options = RenderOptions(
            config_dir=invalid_dir,
            dest_dir=tmp_dest_dir,
            context=ctx,
        )

        pipeline = RenderPipeline(options)
        result = pipeline.run()

        # Should have error
        assert not result.success
        assert len(result.errors) > 0

    def test_pipeline_missing_context_var(self, tmp_config_dir, tmp_dest_dir):
        """Test error on missing template variable in strict mode."""
        template_file = tmp_config_dir / "config.txt.j2"
        template_file.write_text("Value: {{ missing_var }}")

        ctx = load_context(tmp_config_dir)
        options = RenderOptions(
            config_dir=tmp_config_dir,
            dest_dir=tmp_dest_dir,
            context=ctx,
            strict_undefined=True,
        )

        pipeline = RenderPipeline(options)
        result = pipeline.run()

        # Should have error
        assert not result.success
        assert len(result.errors) > 0
        assert "Undefined variable" in result.errors[0].message

    def test_pipeline_rewrite_output_path(self, tmp_config_dir, tmp_dest_dir):
        """Test that a plugin can rewrite the output relative path."""
        source_file = tmp_config_dir / "assets" / "server" / "icon.png"
        source_file.parent.mkdir(parents=True, exist_ok=True)
        source_file.write_text("icon-data")

        ctx = ContextConfig()
        options = RenderOptions(
            config_dir=tmp_config_dir,
            dest_dir=tmp_dest_dir,
            context=ctx,
            plugins=[
                RewriteRelativePathPlugin(
                    source_rel_path=Path("assets/server/icon.png"),
                    rewrite_to=Path("icon.png"),
                )
            ],
        )

        pipeline = RenderPipeline(options)
        result = pipeline.run()

        assert result.success
        assert (tmp_dest_dir / "icon.png").exists()
        assert not (tmp_dest_dir / "assets" / "server" / "icon.png").exists()

    def test_pipeline_skip_prefix_with_context_flag(self, tmp_config_dir, tmp_dest_dir):
        """Test that prefix-scoped skip rules only apply to matching paths."""
        skipped_file = tmp_config_dir / "assets" / "theserver" / "sounds" / "music.ogg"
        skipped_file.parent.mkdir(parents=True, exist_ok=True)
        skipped_file.write_text("sound-data")

        kept_file = tmp_config_dir / "notes.txt"
        kept_file.write_text("keep me")

        ctx = ContextConfig(data={"music": False})
        options = RenderOptions(
            config_dir=tmp_config_dir,
            dest_dir=tmp_dest_dir,
            context=ctx,
            plugins=[
                SkipIfContextMissingPlugin(
                    "music",
                    path_prefix="assets/theserver/sounds",
                )
            ],
        )

        pipeline = RenderPipeline(options)
        result = pipeline.run()

        assert result.success
        assert not (tmp_dest_dir / "assets" / "theserver" / "sounds" / "music.ogg").exists()
        assert (tmp_dest_dir / "notes.txt").exists()
