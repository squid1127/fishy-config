# Usage Guide

## Python API

### Basic Render

Render templates from a config directory using the high-level API:

```python
from fishy_config import render

result = render(
    config_dir="./config",
    dest_dir="./output",
    context={"app_name": "MyApp", "version": "1.0.0"}
)

print(f"Rendered {result.total_files} files")
if result.errors:
    for error in result.errors:
        print(f"Error in {error.file}: {error.message}")
```

### Config Directory Structure

```
config/
├── context.yaml          # Base context (optional, overridden by runtime args)
├── app/
│   ├── config.yaml.j2   # Jinja2 template → renders to config.yaml
│   └── secrets.env      # Copied as-is
└── docs/
    └── README.md        # Copied as-is (skipped by default, see skip_patterns)
```

### Context Loading

Context is merged in order (override wins):

1. **YAML file**: `config/context.yaml` (if exists)
2. **Runtime data**: `context` parameter to `render()`

```python
# context.yaml
database:
  host: localhost
  port: 5432

# Runtime override
result = render(
    "config",
    "output",
    context={"database": {"host": "prod.example.com"}}
)
# Result: host="prod.example.com", port=5432 (deep merge)
```

### Template Variables

Templates use standard Jinja2 syntax:

```yaml
# app/config.yaml.j2
database:
  host: {{ database.host }}
  port: {{ database.port }}

services:
  {% for service in services %}
  - name: {{ service.name }}
    port: {{ service.port }}
  {% endfor %}
```

### Error Handling

```python
from fishy_config import render, FishyConfigError

try:
    result = render("config", "output", context={"app": "test"})
    if not result.success:
        print(f"Render completed with {len(result.errors)} error(s)")
except FishyConfigError as e:
    print(f"Fatal error: {e}")
```

### Options

```python
result = render(
    "config",
    "output",
    context={...},
    strict_undefined=True,      # Fail on missing template vars
    dry_run=True,               # Simulate without writing files
    skip_patterns=["*.log"],    # Skip matching files (gitignore syntax)
    overwrite=True,             # Overwrite existing dest files
)
```

### Plugins

The rendering pipeline supports plugins which can hook into lifecycle events to
influence skipping, mutate context before rendering, modify rendered output,
and perform post-run actions (for example exporting artifacts).

Pass plugin instances via the `plugins` field on `RenderOptions` or the
high-level `render()` call using the `plugins` keyword.

Example (using built-ins):

```python
from fishy_config import render
from fishy_config.plugins.builtins import ZipExporterPlugin, SkipIfContextMissingPlugin

result = render(
  "config",
  "output",
  context={"deploy": {"enabled": True}},
  plugins=[
    SkipIfContextMissingPlugin("deploy.enabled"),
    ZipExporterPlugin("release.zip"),
  ],
)

print(result.artifacts)  # zip exporter will append archive path and hash
```

### Advanced: Direct Pipeline

For more control, use the pipeline directly:

```python
from fishy_config import RenderPipeline, RenderOptions
from fishy_config.loader import load_context
from pathlib import Path

ctx = load_context(Path("config"), {"env": "prod"})
options = RenderOptions(
    config_dir=Path("config"),
    dest_dir=Path("output"),
    context=ctx,
    strict_undefined=True,
)

pipeline = RenderPipeline(options)
result = pipeline.run()
```

## Key Concepts

**Template Extension**: Only `.j2` files are treated as templates. The `.j2` extension is stripped in output:

- `config.yaml.j2` → `config.yaml`
- `app.conf.j2` → `app.conf`

**Skip Patterns**: Use gitignore-style patterns to exclude files. Defaults: `.git`, `.gitkeep`

**Merge Strategy**: By default, nested dicts are merged recursively (runtime data takes precedence). Other types are replaced.

**Strict Mode**: Set `strict_undefined=True` to fail if a template references a variable not in context.

**Dry Run**: Use `dry_run=True` to simulate rendering without writing files. Useful for validation.
