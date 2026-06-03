# Usage

## Build file

See [configuration reference](configuration.md) for details on the build file format and options.

## CLI

The CLI is built with Typer and provides a `build` command that takes a path to a build file and optional context overrides.

```bash
fishy-config build [BUILD_FILE] [OPTIONS]
```

### CLI flags

- `-p` / `--preset`: Apply a named preset from the build file, which is a predefined context object.
- `-c` / `--context`: Override individual context variables. Can be used multiple times. Values will be parsed as YAML, so you can pass strings, numbers, lists, etc.
- `--dry-run`: Print the preview of rendered files to the console instead of writing to disk.

Pass `--debug` before `build` to enable debug logging.

## Metadata files

By creating a `dir/.meta.yaml` or `file.meta.yaml`, you can specify metadata for that directory or file, which can be used to change output path, name, as well as other options. This file is rendered as a Jinja2 template before parsing, so you can use context variables to conditionally set metadata values.

```yaml
skip: { { context_variable } } # true or false
name: "fish" # override output name to "fish"
```

### Metadata options

| Key             | Type   | Description                                                                                                                                                                       |
| --------------- | ------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `skip`          | bool   | If true, this file or directory will be skipped and not rendered or copied to the output.                                                                                         |
| `name`          | string | Override the output name of this file or directory.                                                                                                                               |
| `path`          | string | Override the output path of this file or directory. Can be an absolute path or relative to the output directory.                                                                  |
| `path_absolute` | bool   | If true, the `path` value will be treated as an absolute path. Otherwise, it will be relative to the original path.                                                               |
| `variant`       | string | (Directories only) Hoists the subdirectory with a matching name, so `fish/hi.txt` will be rendered as `hi.txt` in the output if `variant` is set to `fish` and otherwise skipped. |
| `flatten`       | bool   | (Directories only) Flattens all nested files into the output directory, so `fish/hi.txt` will be rendered as `hi.txt` in the output if `flatten` is true.                         |
