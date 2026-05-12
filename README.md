# fishy-config

A "simple" python-based library for templating config.

## What it's supposed to do

You give it a directory of config files, j2 templates, and it renders them to a target directory, with input context and a fancy CLI.

## CLI

The package installs a `fishy-config` command. The default command shape is:

```bash
fishy-config render ./config ./output --context name=demo --plugin mypkg.plugins:MyPlugin
```

The CLI is intentionally thin. External projects can reuse the same command surface by importing `create_app()` from `fishy_config.cli` and passing their own render function or plugin resolver.

## Disclaimer

This is a personal project, and is not intended for production use. (I say this in every one of my repos lol)

## How much of it is vibe coded?

Most of it lol.
