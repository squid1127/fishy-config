# (very) fishy-config

A small Python utility for rendering configuration files using Jinja2 templates and a simple build configuration.

This repository contains a CLI (`fishy-config`) and a small engine that:

- scans a source directory for template and static files,
- renders Jinja2 templates with a merged context,
- writes outputs to a destination directory, and
- optionally produces artifacts (zip, directory, or custom builder commands).

This is a personal project and not intended for production use.

Quick links

- Usage: [docs/USAGE.md](docs/USAGE.md)
- Configuration reference: [docs/CONFIGURATION.md](docs/CONFIGURATION.md)
- Python API: [docs/API.md](docs/API.md)

Quickstart

1. Create a `build.yaml` in your project root (see docs for schema).
2. Run the build: `fishy-config build` (uses `build.yaml` by default).
3. To pass simple context values inline: `fishy-config build -c key=value -c other=val`.

Commands

- `fishy-config version` — show package version.
- `fishy-config build [build_file]` — run a build using the provided config file (defaults to `build.yaml`).
- `fishy-config wizard` — (not implemented).

If you want to dig into the code, see `src/fishy_config/cli` for the CLI and `src/fishy_config` for engine components.
