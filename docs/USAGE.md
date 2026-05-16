# Usage Guide

This document shows how to run the CLI and how the source tree is interpreted.

Running the CLI

- Default build file: `build.yaml` in the current directory. You can pass an alternate file as the positional argument to `fishy-config build`.
- Example: `fishy-config build` or `fishy-config build my-config.yaml`.
- Pass simple context values on the CLI with `-c/--context key=value` (repeatable):
  `fishy-config build -c db_host=localhost -c db_port=5432`.
- Apply named presets from the build file with `-p/--preset NAME`.
- Select a named flow from `build.yaml` with `-f/--flow NAME`.
- Enable interactive confirmation with `-i/--interactive`.

Files and templates

- Template files: files ending with the template suffix (default `.j2`) are rendered with Jinja2. The rendered output filename excludes the template suffix.
- Static files: files without the template suffix are copied to the output location.
- Metadata files: file-level metadata uses the metadata suffix (default `.meta.yaml`). Place a metadata file next to a source file or in a directory to control behavior for files in that directory.

Typical metadata keys

- `skip` (boolean): if true, the file is skipped and not rendered/copied.
- `output_name` (string): override the output filename for the rendered file.

Build flows and dry-run

- The `flows` section in `build.yaml` declares named flows. A flow can include a `dry_run` boolean and a list of `presets` to apply.
- When a flow with `dry_run: true` is selected the build will validate and show render diffs but will not write files.

Artifacts

- Artifacts are declared in `build.yaml` and may be one of: `zip` (zip archive), `directory` (copy to a directory), or `custom_builder` (run a template command).
- For `custom_builder` artifacts the `command` field is required and `overwrite` must be `true`.

Where outputs appear

- The build writes files into the `output` directory defined in `build.yaml` (examples use `dist/` by convention).

See the configuration reference for `build.yaml` schema and examples: [docs/CONFIGURATION.md](docs/CONFIGURATION.md)
