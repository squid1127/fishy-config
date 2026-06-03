# (very) fishy-config

A small Python utility for rendering configuration files using Jinja2!

This is a personal project and not intended for production use.

## Table of Contents

- [How it works](#how-it-works)
- [Features](#features)
- [Installation](#installation)
- [Development](#development)
- [API](docs/api.md)
- [Usage / CLI](docs/usage.md)
- [Configuration](docs/configuration.md)

## How it works

Start with a template file, e.g. `src/config.yaml.j2`:

```yaml
name: {{ name }}

foo:
{% for item in items %}
  - {{ item }}
{% endfor %}
```

Then, create a build file, e.g. `build.yaml`:

```yaml
version: 2

source: ./src
output: ./dist

context:
  type: object
  properties:
  name:
    type: string
    default: "fish"
  items:
    type: array
    items:
      type: string
      default: ["item1", "item2", "item3"]

options:
  clean_output: true
  overwrite: true
```

Finally, run the build:

```bash
fishy-config build build.yaml -c name=squid
```

This will render `src/config.yaml.j2` using the provided context and output it to `dist/config.yaml`.

```yaml
name: squid
foo:
  - item1
  - item2
  - item3
```

### Why?

Jinja supports all sorts of logic and features that can be very useful for generating complex configuration files, and making it easier to edit several similar files at once.

## Features

### Integrated CLI

Easily use fishy-config from the command line to build your configuration files.

### Metadata Files

Creating a `dir/.meta.yaml` or `file.meta.yaml` allows you to specify metadata for that directory or file, which can be used to change output path, name, as well as other options.

```yaml
skip: {{ skip_potatoes }}
name: "fish"
path: "No"
```

### Config Schema and Validation

The build file supports a JSON schema (As a YAML object :P) for validating the configuration before running the build. This ensures that your configuration is correct and prevents errors during the build process.

### Sophisticated Recursion

fishy-config is designed to handle complex directory structures and will recursively render all template files it finds, stacking relative paths as it goes. This allows for very flexible organization of your templates.

### Artifacts

You can specify artifacts in your build file, which will be generated after the rendering process. This can be used to create zip files. (More artifact types may be added in the future!)

```yaml
artifacts:
  main:
    artifact_type: zip
    path: ./main.zip
```

### Python API

You can also use fishy-config as a Python library, allowing you to integrate it into your own scripts and applications.

## Installation

Use at your own risk! This is a personal project and not intended for production use.

```bash
pip install git+https://github.com/squid1127/fishy-config.git
```

Alternatively, use any other python package manager, such as `pipx`.

## Development

(Why?)

Clone the repo and install with poetry:

```bash
git clone https://github.com/squid1127/fishy-config.git
cd fishy-config
poetry install
```
