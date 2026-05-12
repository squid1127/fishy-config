from __future__ import annotations

import argparse
import json
from typing import Any

from .core import ConfigRenderer


def _parse_context_json(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    data = json.loads(value)
    if not isinstance(data, dict):
        raise argparse.ArgumentTypeError("--context-json must be a JSON object")
    return data


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="fishy-config")
    parser.add_argument("source_dir")
    parser.add_argument("target_dir")
    parser.add_argument(
        "-c",
        "--context-file",
        dest="context_files",
        action="append",
        default=[],
        help="Path to a YAML context file. Can be passed multiple times.",
    )
    parser.add_argument(
        "--context-json",
        help="Inline JSON object merged last with highest priority.",
    )
    parser.add_argument(
        "--strict-undefined",
        action="store_true",
        help="Fail when template variables are missing.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    renderer = ConfigRenderer(strict_undefined=args.strict_undefined)
    renderer.render_directory(
        args.source_dir,
        args.target_dir,
        context_files=args.context_files,
        context=_parse_context_json(args.context_json),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
