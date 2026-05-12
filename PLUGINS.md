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

How to enable plugins

1. High-level `render()` call

```python
from fishy_config import render
from fishy_config.plugins.builtins import ZipExporterPlugin

result = render("config", "out", context={}, plugins=[ZipExporterPlugin()])
```

2. Direct `RenderPipeline`

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

Writing your own plugin

Subclass `BasePlugin` and override the hooks you need. Keep plugins small and
focused — they should not perform destructive file operations without
explicit consent (e.g., via options).

Example skeleton

```python
from fishy_config.plugins.base import BasePlugin

class MyPlugin(BasePlugin):
    name = "my_plugin"

    def should_skip(self, src_path, rel_path, context):
        # decide whether to skip
        return False

    def post_render(self, src_path, rel_path, dest_path, rendered):
        # modify and return content
        return rendered.replace("SECRET", "REDACTED")

    def on_run_end(self, result):
        # append artifact or cleanup
        result.artifacts.append("my-plugin:done")
```

Notes

- Plugins are executed in the order they are provided.
- Exceptions in plugin methods are caught and logged; they will not stop the
  pipeline but may add errors to the `RenderResult` in future iterations.
- The `ZipExporterPlugin` is best-effort: it attempts to infer the dest
  directory from rendered/copied file paths. For reliable behavior, ensure
  `dest_dir` contains output before running the plugin.
