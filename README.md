# fish-config

A "simple" python-based library for templating config.

## What it's supposed to do

You give it a directory of config files, j2 templates, and it renders them to a target directory, with input context and a fancy CLI.

## Current implementation

The initial implementation now includes:
- Recursive context merge support
- YAML context loading from one or more files
- Directory rendering for `*.j2` templates (written without the `.j2` suffix)
- File copy-through for non-template files
- A CLI entrypoint: `fishy-config <source_dir> <target_dir> -c context.yaml`

## Disclaimer

This is a personal project, and is not intended for production use. (I say this in every one of my repos lol)
