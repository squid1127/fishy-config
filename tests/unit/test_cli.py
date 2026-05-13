"""Unit tests for the CLI factory."""

from types import SimpleNamespace

from typer.testing import CliRunner

from fishy_config.cli import create_app
from fishy_config.project import ProjectConfig

runner = CliRunner()


def test_cli_uses_project_plugin_factory(tmp_path):
    config_dir = tmp_path / "config"
    dest_dir = tmp_path / "out"
    config_dir.mkdir()

    calls = {}

    def fake_render(request):
        calls["request"] = request
        return SimpleNamespace(success=True, total_files=0, errors=[], artifacts=[])

    def fake_plugin_factory(context):
        return ["factory-created-plugin"]

    app = create_app(
        render_fn=fake_render,
        project_config=ProjectConfig(name="demo", plugin_factory=fake_plugin_factory),
    )

    result = runner.invoke(
        app,
        [
            "render",
            str(config_dir),
            str(dest_dir),
            "--context",
            "name=demo",
        ],
    )

    assert result.exit_code == 0
    assert calls["request"].plugins == ["factory-created-plugin"]


def test_cli_passes_clean_dest_and_template_extension(tmp_path):
    config_dir = tmp_path / "config"
    dest_dir = tmp_path / "out"
    config_dir.mkdir()

    calls = {}

    def fake_render(request):
        calls["request"] = request
        return SimpleNamespace(success=True, total_files=0, errors=[], artifacts=[])

    app = create_app(
        render_fn=fake_render,
        project_config=ProjectConfig(name="demo", template_extension=".tmpl"),
    )

    result = runner.invoke(app, ["render", str(config_dir), str(dest_dir), "--clean-dest"])

    assert result.exit_code == 0
    assert calls["request"].clean_dest is True
    assert calls["request"].template_extension == ".tmpl"


def test_cli_skip_patterns_include_project_defaults_then_cli(tmp_path):
    config_dir = tmp_path / "config"
    dest_dir = tmp_path / "out"
    config_dir.mkdir()

    calls = {}

    def fake_render(request):
        calls["request"] = request
        return SimpleNamespace(success=True, total_files=0, errors=[], artifacts=[])

    app = create_app(
        render_fn=fake_render,
        project_config=ProjectConfig(name="demo", skip_patterns=["*.md"]),
    )

    result = runner.invoke(app, ["render", str(config_dir), str(dest_dir), "--skip", "*.log"])

    assert result.exit_code == 0
    assert calls["request"].skip_patterns == ["*.md", "*.log"]


def test_cli_passes_none_skip_patterns_when_no_overrides(tmp_path):
    config_dir = tmp_path / "config"
    dest_dir = tmp_path / "out"
    config_dir.mkdir()

    calls = {}

    def fake_render(request):
        calls["request"] = request
        return SimpleNamespace(success=True, total_files=0, errors=[], artifacts=[])

    app = create_app(
        render_fn=fake_render,
        project_config=ProjectConfig(name="demo", skip_patterns=[]),
    )

    result = runner.invoke(app, ["render", str(config_dir), str(dest_dir)])

    assert result.exit_code == 0
    assert calls["request"].skip_patterns is None


def test_cli_uses_project_default_overwrite(tmp_path):
    config_dir = tmp_path / "config"
    dest_dir = tmp_path / "out"
    config_dir.mkdir()

    calls = {}

    def fake_render(request):
        calls["request"] = request
        return SimpleNamespace(success=True, total_files=0, errors=[], artifacts=[])

    app = create_app(
        render_fn=fake_render,
        project_config=ProjectConfig(name="demo", default_overwrite=True),
    )

    result = runner.invoke(app, ["render", str(config_dir), str(dest_dir)])

    assert result.exit_code == 0
    assert calls["request"].overwrite is True


def test_cli_overwrite_flag_overrides_project_default(tmp_path):
    config_dir = tmp_path / "config"
    dest_dir = tmp_path / "out"
    config_dir.mkdir()

    calls = {}

    def fake_render(request):
        calls["request"] = request
        return SimpleNamespace(success=True, total_files=0, errors=[], artifacts=[])

    app = create_app(
        render_fn=fake_render,
        project_config=ProjectConfig(name="demo", default_overwrite=False),
    )

    result = runner.invoke(app, ["render", str(config_dir), str(dest_dir), "--overwrite"])

    assert result.exit_code == 0
    assert calls["request"].overwrite is True


def test_cli_uses_project_default_clean_dest(tmp_path):
    config_dir = tmp_path / "config"
    dest_dir = tmp_path / "out"
    config_dir.mkdir()

    calls = {}

    def fake_render(request):
        calls["request"] = request
        return SimpleNamespace(success=True, total_files=0, errors=[], artifacts=[])

    app = create_app(
        render_fn=fake_render,
        project_config=ProjectConfig(name="demo", default_clean_dest=True),
    )

    result = runner.invoke(app, ["render", str(config_dir), str(dest_dir)])

    assert result.exit_code == 0
    assert calls["request"].clean_dest is True


def test_cli_clean_dest_flag_overrides_project_default(tmp_path):
    config_dir = tmp_path / "config"
    dest_dir = tmp_path / "out"
    config_dir.mkdir()

    calls = {}

    def fake_render(request):
        calls["request"] = request
        return SimpleNamespace(success=True, total_files=0, errors=[], artifacts=[])

    app = create_app(
        render_fn=fake_render,
        project_config=ProjectConfig(name="demo", default_clean_dest=False),
    )

    result = runner.invoke(app, ["render", str(config_dir), str(dest_dir), "--clean-dest"])

    assert result.exit_code == 0
    assert calls["request"].clean_dest is True
