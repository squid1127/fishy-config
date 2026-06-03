# Configuration Reference

This document describes the `build.yaml` top-level keys and the file/metadata conventions used by the engine.

| Key            | Type    | Description                                                                                   |
| -------------- | ------- | --------------------------------------------------------------------------------------------- |
| `version`      | integer | The version of the build file format. See below.                                              |
| `source`       | string  | Path to the source directory containing Jinja2 templates and static files.                    |
| `output`       | string  | Path to the output directory where rendered files will be written.                            |
| `context`      | object  | (Optional) A JSON/YAML object providing context variables for rendering.                      |
| `context_file` | string  | (Optional) Path to a JSON/YAML file containing context variables to use instead of `context`. |
| `options`      | object  | (Optional) Additional build options. See below.                                               |
| `artifacts`    | object  | (Optional) A mapping of artifact names to their configuration. See below.                     |
| `presets`      | object  | (Optional) A mapping of preset names to context objects that can be applied via CLI flags.    |

## Build Options

| Key                           | Type         | Description                                                                                                                                  |
| ----------------------------- | ------------ | -------------------------------------------------------------------------------------------------------------------------------------------- |
| `clean_output`                | boolean      | If true, the output directory will be cleared before writing new files. Defaults to false.                                                   |
| `overwrite`                   | boolean      | If true, existing files in the output directory will be overwritten. Defaults to false.                                                      |
| `internal_template_namespace` | string       | (Optional) An object containing built-in context variables. Defaults to `_fishy`.                                                            |
| `template_skip_prefix`        | string       | (Optional) If a template starts with this prefix, it will be skipped. Defaults to `_`.                                                       |
| `metadata_suffix`             | string       | (Optional) If a template file has a sibling file with the same name plus this suffix, it will be used as metadata. Defaults to `.meta.yaml`. |
| `template_suffix`             | string       | (Optional) Only files with this suffix will be treated as templates and rendered. Others will be copied as-is. Defaults to `.j2`.            |
| `skip_patterns`               | list[string] | (Optional) A list of glob patterns to match files that should be skipped during scanning.                                                    |

## Artifact Configuration

Artifacts are optional outputs that can be generated after rendering. They can be used to produce zip files, directory copies, or custom builder commands.

| Key             | Type   | Description                                                                                                                                                                        |
| --------------- | ------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `artifact_type` | string | The type of artifact to generate. Supported types include `zip`, `custom_builder`, and `custom_command`.                                                                           |
| `source`        | string | For `zip` and `directory_copy`, the path to the directory to include in the artifact. For `custom_command`, the command to execute to generate the artifact, as a Jinja2 template. |
| `path`          | string | The path where the generated artifact should be saved. For `custom_builder`, this is the working directory where the command will be executed.                                     |

## Versioning

| File Version | Engine Version | Description                                                                            |
| ------------ | -------------- | -------------------------------------------------------------------------------------- |
| 1            | 0.1.0          | Initial version. Artifacts is a list of objects, and the options object doesn't exist. |
| 2            | 0.2.0+         | Artifacts is a mapping of name to config, and options object has been added.           |

## Example

Here's a simple example of a `build.yaml` file:

```yaml
version: 2

source: src
output: dist/raw

context:
  type: object
  properties:
    name:
      type: string
      description: The name of the project.
    friendly_name:
      type: string
      description: A user-friendly name for the project.
    description:
      type: string
      description: A description of the project.
      default: ""

    fancy_gui:
      type: boolean
      description: Whether to include the fancy GUI in the build.
      default: false

    theme:
      type: string
      description: The theme to use for the pack. Can be "legacy", "bunny", or "none".
      enum: ["legacy", "bunny", "none"]
      default: "bunny"

presets:
  theserver:
    name: "theserver"
    friendly_name: "The Server"

  theos:
    name: "theos"
    friendly_name: "Theos SMP"
    fancy_gui: true

options:
  clean_output: true
  overwrite: true
  skip_patterns:
    - "*.mp3"
    - "*.yaml"

artifacts:
  pack:
    artifact_type: "zip"
    path: "dist/pack.zip"
```
