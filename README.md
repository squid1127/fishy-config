# fishy-config

A Python library for rendering templated configuration directories using Jinja2 and context data.

## Overview

`fishy-config` simplifies the process of generating configuration files from templates. You provide:

- A source directory with Jinja2 templates (`.j2` files) and static assets
- Context data (YAML files or runtime values)
- Optional plugins for custom processing

The library renders templates, copies static files, and produces a destination directory with your generated config. It supports:

- **Template rendering** with Jinja2 (`.j2` files)
- **Context merging** (deep merge with override semantics)
- **Gitignore-style skip patterns** to exclude files
- **File-level skip logic** via plugins
- **Plugin system** for pre-render, post-render, and artifact generation hooks
- **Validation** with Pydantic models (optional)
- **Dry-run mode** to preview changes without writing
- **Artifact generation** (e.g., zip exports)

## Quick Start

### CLI

```bash
# Render with inline context
fishy-config render ./config ./output --context env=prod --context version=1.0.0

# Render with context file
fishy-config render ./config ./output --context-file context.yaml

# Preview changes (dry-run)
fishy-config render ./config ./output --context env=prod --dry-run

# Overwrite existing files
fishy-config render ./config ./output --context env=prod --overwrite
```

### Python API

```python
from fishy_config import render, RenderRequest

result = render(RenderRequest(
    config_dir="./config",
    dest_dir="./output",
    context={"env": "prod", "version": "1.0.0"},
))

print(f"Rendered {result.total_files} files")
```

## Use Cases

- **Multi-environment config**: Render configs for dev, staging, prod with shared templates
- **Minecraft modpack building**: Generate resource packs and datapacks with dynamic content
- **Docker/Kubernetes manifests**: Template out deployments with environment-specific values
- **Application configuration**: Generate `.env`, `config.yaml`, etc. from templates
- **Build artifact generation**: Create versioned, signed packages with metadata

## Features

| Feature              | Description                                                              |
| -------------------- | ------------------------------------------------------------------------ |
| **Jinja2 Templates** | Full Jinja2 syntax support with filters, loops, conditionals             |
| **Context Merging**  | Deep merge YAML + runtime data with override semantics                   |
| **Skip Patterns**    | Gitignore-style patterns to exclude files (`.git`, `.env.local`, etc.)   |
| **Plugins**          | Hook into lifecycle events: pre-render, post-render, artifact generation |
| **Dry-Run Mode**     | Preview changes without writing files                                    |
| **Strict Mode**      | Fail if templates reference undefined variables                          |
| **Validation**       | Optional Pydantic model validation for context                           |
| **Artifact Export**  | Built-in zip exporter for release packages                               |

## Custom Projects

Wrapper projects can extend `fishy-config` by importing `create_app()` and providing:

- Custom defaults (`ProjectConfig`)
- Context validation (`context_model`)
- Plugin factory (`plugin_factory`)

```python
from fishy_config import create_app, ProjectConfig
from my_plugins import create_plugins

config = ProjectConfig(
    name="my-app",
    context_model=MyContextModel,  # optional validation
    plugin_factory=create_plugins,  # optional custom plugins
    default_overwrite=True,
)

app = create_app(project_config=config)
```

## Documentation

- [Usage Guide](./USAGE.md) — API, context loading, options
- [Plugins Guide](./PLUGINS.md) — Writing and using plugins

## Disclaimer

- This is a personal project, and is not intended for production use. (I say this in every one of my repos lol)
- This project was largely vibe coded :)
- This project will probably not be maintained, and may be replaced with a different solution in the future.
