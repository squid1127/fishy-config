"""Unit tests for the CLI factory."""

from types import SimpleNamespace

from pydantic import BaseModel, Field
from typer.testing import CliRunner

from fishy_config.cli.core import create_app
from fishy_config.project import ProjectConfig
from fishy_config.cli.tui import WizardResult

runner = CliRunner()


class WizardContext(BaseModel):
    name: str = Field(default="Fishy", description="Project name", examples=["demo-app"])
    replicas: int = Field(default=2, description="Replica count")


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


def test_cli_wizard_uses_project_defaults_and_renders(tmp_path, monkeypatch):
    config_dir = tmp_path / "config"
    dest_dir = tmp_path / "out"
    config_dir.mkdir()

    calls = {}

    def fake_render(request):
        calls["request"] = request
        return SimpleNamespace(success=True, total_files=0, errors=[], artifacts=[])

    def fake_run_wizard_tui(session):
        return WizardResult(
            config_dir=config_dir,
            dest_dir=dest_dir,
            context={"name": "Fishy", "replicas": 2},
            strict_undefined=False,
            dry_run=False,
            overwrite=True,
            clean_dest=False,
            skip_patterns=[],
        )

    app = create_app(
        render_fn=fake_render,
        project_config=ProjectConfig(
            name="demo",
            context_model=WizardContext,
            default_config_dir=config_dir,
            default_dest_dir=dest_dir,
            wizard_enabled=True,
        ),
    )

    monkeypatch.setattr("fishy_config.wizard_tui.run_wizard_tui", fake_run_wizard_tui)
    result = runner.invoke(app, ["wizard"])

    assert result.exit_code == 0
    assert calls["request"].config_dir == config_dir
    assert calls["request"].dest_dir == dest_dir
    assert calls["request"].context["name"] == "Fishy"
    assert calls["request"].typed_context.name == "Fishy"
    assert calls["request"].typed_context.replicas == 2


def test_cli_wizard_is_omitted_when_disabled():
    app = create_app(project_config=ProjectConfig(name="demo"))

    result = runner.invoke(app, ["wizard"])

    assert result.exit_code != 0
    assert "No such command" in result.output
