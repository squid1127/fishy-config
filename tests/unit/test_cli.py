"""Unit tests for the CLI factory."""

from types import SimpleNamespace

from typer.testing import CliRunner

from fishy_config.cli import create_app

runner = CliRunner()


def test_cli_factory_uses_injected_render_and_plugin_loader(tmp_path):
    config_dir = tmp_path / "config"
    dest_dir = tmp_path / "out"
    config_dir.mkdir()

    calls = {}

    def fake_render(**kwargs):
        calls["render_kwargs"] = kwargs
        return SimpleNamespace(success=True, total_files=3, errors=[], artifacts=[])

    def fake_plugin_resolver(plugins, discover=False, group=None):
        calls["plugin_resolver"] = {
            "plugins": list(plugins),
            "discover": discover,
            "group": group,
        }
        return ["resolved-plugin"]

    app = create_app(render_fn=fake_render, plugin_resolver=fake_plugin_resolver)

    result = runner.invoke(
        app,
        [
            "render",
            str(config_dir),
            str(dest_dir),
            "--context",
            "name=demo",
            "--plugin",
            "example.plugins:MyPlugin",
            "--discover-plugins",
        ],
    )

    assert result.exit_code == 0
    assert calls["plugin_resolver"]["plugins"] == ["example.plugins:MyPlugin"]
    assert calls["plugin_resolver"]["discover"] is True
    assert calls["render_kwargs"]["config_dir"] == config_dir
    assert calls["render_kwargs"]["dest_dir"] == dest_dir
    assert calls["render_kwargs"]["context"] == {"name": "demo"}
    assert calls["render_kwargs"]["plugins"] == ["resolved-plugin"]
