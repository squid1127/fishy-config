# Configuration Reference

This document describes the `build.yaml` top-level keys and the file/metadata conventions used by the engine.

Top-level `build.yaml` keys

- `source` (string, required): path to the source/templates directory (relative to the build working directory).
- `output` (string, required): path to the output directory where rendered files will be written.
- `context` (object, optional): a JSON Schema-like object describing context properties and defaults. Defaults in the schema are extracted and applied as initial context values.
- `presets` (mapping, optional): named context presets. Each preset is a mapping of context key → value.
- `flows` (mapping of flow-name → flow config, optional): named build flows. Each flow can include `artifacts`, `dry_run` and `presets`.
- `artifacts` (array, optional): list of artifact definitions to generate after rendering.
- `clean_output` (boolean, optional): if true, the output directory will be cleaned before writing files.
- `overwrite` (boolean, optional): if true, existing files in output will be overwritten.

Notes about paths

- `source` and `output` are expected to be relative paths. If the directory does not exist it will be created by the validator.

Example `build.yaml`

```yaml
source: src
output: dist
context:
  type: object
  properties:
    db_host:
      type: string
      default: localhost
    db_port:
      type: integer
      default: 5432
presets:
  prod:
    db_host: db.example.com
    db_port: 5432
artifacts:
  - id: release
    artifact_type: zip
    path: dist/release.zip
```

File metadata

- Metadata files sit next to source files and use the metadata suffix (default `.meta.yaml`).
- Directory-level metadata (a metadata file placed directly in a directory) applies to files under that directory.

Common metadata keys

- `skip` (boolean): skip rendering/copying this file.
- `output_name` (string): override filename for rendered output.

Context merging and priorities

Context values are merged from multiple sources. The effective merge order (lowest → highest priority) used by the CLI is:

1. Defaults extracted from the `context` schema in `build.yaml` (lowest priority)
2. Presets applied from the `presets` section when requested by the CLI or a flow
3. CLI `--context`/`-c` arguments (highest priority)

The CLI currently supports adding context via `-c/--context key=value` and by applying `presets`. The code includes types for `FILE` and `ENV` context sources, but using external context files is not wired into the top-level CLI yet.

Artifacts

Each artifact entry must include:

- `id` (string): unique identifier for the artifact.
- `artifact_type` (one of `zip`, `directory`, `custom_builder`): how the artifact is produced.
- `path` (string): path for the generated artifact (for `custom_builder` this is used as the command CWD).
- `command` (string, required only for `custom_builder`): a Jinja2-templated command to run.
- `overwrite` (boolean): whether to overwrite an existing artifact. For `custom_builder` artifacts this must be true.

See the API reference for the Python models used to represent artifacts and config: [docs/API.md](docs/API.md)
