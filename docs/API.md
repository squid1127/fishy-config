# Python API Reference

This section lists the public API surfaces and common usage patterns.

Running a build programmatically

```python
from fishy_config.builder import build
from fishy_config.models.config import EngineConfig

cfg = EngineConfig(
    source_dir=Path("src"),
    output_dir=Path("dist"),
    context={"key": "value"},
)
artifacts = build(cfg)
```

CLI helpers

The CLI Typer app is exposed in `fishy_config.cli.app`. The main executor class is `fishy_config.cli.main.FishyConfigCLI` which reads a `build.yaml`, merges context sources and runs the scan/render/artifact steps.

Core engine components

- `TemplateRenderer` (`fishy_config.renderer`) — renders Jinja2 templates with a provided context.
- `SourceTreeScanner` (`fishy_config.scanner`) — walks the `source_dir` and yields `QueuedFile` objects describing files to render or copy.
- `OutputBuilder` (`fishy_config.output`) — writes rendered outputs to `output_dir` and applies metadata rules.
- `ArtifactGenerator` (`fishy_config.artifact_generator`) — produces configured artifacts (zip, directory copy, or custom builder commands).

Configuration models

- `BuildConfig` (`fishy_config.cli.models`) — Pydantic model matching the `build.yaml` keys used by the CLI: `source`, `output`, `context`, `presets`, `flows`, `artifacts`, `clean_output`, `overwrite`.
- `EngineConfig` (`fishy_config.models.config`) — internal engine config used by renderer/scanner/output. Fields include `source_dir`, `output_dir`, `context`, `artifacts`, `clean_output`, `overwrite`, `metadata_suffix` and `template_suffix`.

Exceptions and logging

Use the package logging helpers in `fishy_config.log` to enable consistent logging. The codebase defines a small hierarchy of exceptions under `fishy_config.models.exceptions` and `fishy_config.cli.exceptions` used by the CLI.

See the source modules for full method signatures and examples: `src/fishy_config`.
