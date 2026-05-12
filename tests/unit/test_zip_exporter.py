"""Unit tests for the zip exporter plugin."""

from pathlib import Path

from fishy_config.models import RenderResult, RenderOptions, ContextConfig
from fishy_config.plugins.builtins import CopyArtifactPlugin, ZipExporterPlugin
from fishy_config.plugins.base import PostRunContext


def test_zip_exporter_bare_name_creates_expected_zip(tmp_path):
    dest_dir = tmp_path / "output"
    dest_dir.mkdir()
    (dest_dir / "file.txt").write_text("hello", encoding="utf-8")

    result = RenderResult(files_rendered=[str(dest_dir / "file.txt")])
    opts = RenderOptions(config_dir=dest_dir, dest_dir=dest_dir, context=ContextConfig())

    plugin = ZipExporterPlugin("pack")
    plugin.on_run_end(PostRunContext(options=opts, result=result))

    archive_path = tmp_path / "pack.zip"
    assert archive_path.exists()
    assert any(item.startswith(str(archive_path)) for item in result.artifacts)


def test_zip_exporter_explicit_zip_name_creates_expected_zip(tmp_path):
    dest_dir = tmp_path / "output"
    dest_dir.mkdir()
    (dest_dir / "file.txt").write_text("hello", encoding="utf-8")

    result = RenderResult(files_rendered=[str(dest_dir / "file.txt")])
    opts = RenderOptions(config_dir=dest_dir, dest_dir=dest_dir, context=ContextConfig())

    plugin = ZipExporterPlugin("out.zip")
    plugin.on_run_end(PostRunContext(options=opts, result=result))

    archive_path = tmp_path / "out.zip"
    assert archive_path.exists()
    assert any(item.startswith(str(archive_path)) for item in result.artifacts)


def test_copy_artifact_plugin_copies_archive(tmp_path):
    dest_dir = tmp_path / "output"
    dest_dir.mkdir()
    archive_path = tmp_path / "pack.zip"
    archive_path.write_text("zip-data", encoding="utf-8")

    result = RenderResult(files_rendered=[])
    opts = RenderOptions(config_dir=dest_dir, dest_dir=dest_dir, context=ContextConfig())

    plugin = CopyArtifactPlugin(tmp_path / "exports", "pack.zip")
    plugin.on_run_end(PostRunContext(options=opts, result=result))

    copied = tmp_path / "exports" / "pack.zip"
    assert copied.exists()
    assert copied.read_text(encoding="utf-8") == "zip-data"
