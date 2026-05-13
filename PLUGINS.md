# Plugins Guide

This project supports a simple plugin system to extend the rendering pipeline.

Plugins are regular Python objects implementing one or more of the lifecycle
methods defined in `fishy_config.plugins.base.Plugin` (or by subclassing
`BasePlugin`). The `PluginManager` will call available methods at these points:

- `on_run_start(options: RenderOptions)` — before scanning files
- `should_skip(src_path: Path, rel_path: Path, context: dict) -> bool` — return
  True to skip processing the given file
- `pre_render(src_path, rel_path, dest_path, context) -> dict` — return a
  (possibly modified) context used for rendering the file
- `post_render(src_path, rel_path, dest_path, rendered) -> Optional[str]` —
  optionally return modified content to write
- `on_run_end(result: RenderResult)` — after pipeline completes; can append
  artifacts to `result.artifacts` or perform cleanup tasks

Built-in plugins are provided in `fishy_config.plugins.builtins`:

- `SkipIfContextMissingPlugin(key: str)` — skips files when the named context
  key (dot-separated) is missing or falsy.
- `ZipExporterPlugin(archive_name: Optional[str])` — zips the output directory
  (best-effort) and appends `path:sha256` to `RenderResult.artifacts`.

## How to Enable Plugins

**1. High-level `render()` API**

Pass plugin instances via the `plugins` field on `RenderRequest`:

```python
from fishy_config import render, RenderRequest
from fishy_config.plugins.builtins import ZipExporterPlugin

result = render(
  RenderRequest(
    config_dir="config",
    dest_dir="out",
    context={},
    plugins=[ZipExporterPlugin("app.zip")],
  )
)
```

**2. Wrapper projects (CLI with custom defaults)**

Define a `plugin_factory` function in `ProjectConfig` to create plugins based on validated context:

```python
from fishy_config import create_app, ProjectConfig
from fishy_config.plugins.builtins import SkipIfContextMissingPlugin, ZipExporterPlugin

def create_plugins(context):
    # context is already validated if you provide a context_model
    return [
        SkipIfContextMissingPlugin("music.enabled"),
        ZipExporterPlugin("release.zip"),
    ]

project_config = ProjectConfig(
    name="my-app",
    plugin_factory=create_plugins,  # called automatically by CLI
)

app = create_app(project_config=project_config)
```

**3. Direct pipeline (advanced)**

```python
from fishy_config import RenderPipeline, RenderOptions
from fishy_config.plugins.builtins import SkipIfContextMissingPlugin
from fishy_config.loader import load_context
from pathlib import Path

ctx = load_context(Path("config"), {})
options = RenderOptions(
    config_dir=Path("config"),
    dest_dir=Path("out"),
    context=ctx,
    plugins=[SkipIfContextMissingPlugin("deploy.enabled")],
)

p = RenderPipeline(options)
res = p.run()
```

## Writing Your Own Plugin

Subclass `BasePlugin` and override the hooks you need. Keep plugins small and focused — they should not perform destructive file operations without explicit consent.

**Example:**

```python
from fishy_config.plugins.base import BasePlugin
from pathlib import Path

class MyPlugin(BasePlugin):
    name = "my_plugin"

    def should_skip(self, src_path: Path, rel_path: Path, context: dict) -> bool:
        # return True to skip processing this file
        return False

    def post_render(self, src_path: Path, rel_path: Path, dest_path: Path, rendered: str) -> str:
        # optionally modify rendered content before writing
        return rendered.replace("SECRET", "REDACTED")

    def on_run_end(self, result):
        # perform post-render actions (e.g., export artifacts)
        result.artifacts.append("my-plugin:success")
```

Then use in your wrapper project:

```python
from fishy_config import create_app, ProjectConfig
from .plugins import MyPlugin

def create_plugins(context):
    return [MyPlugin()]

config = ProjectConfig(
    name="my-app",
    plugin_factory=create_plugins,
)

app = create_app(project_config=config)
```

## Notes

- Plugins are executed in the order they are provided.
- Exceptions in plugin methods are caught and logged; they will not stop the pipeline.