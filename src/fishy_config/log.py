"""Basic logging utilities for fishy-config.

Provides a small wrapper around Python logging so callers can enable/disable
and configure a consistent logger for the package.
"""

from __future__ import annotations

import logging
from typing import Optional

_ROOT_NAME = "fishy_config"


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Return a logger scoped to the fishy-config package.

    Use `configure_logging` to adjust global logging behavior.
    """
    if name:
        return logging.getLogger(f"{_ROOT_NAME}.{name}")
    return logging.getLogger(_ROOT_NAME)


def configure_logging(level: int = logging.INFO, *, enable: bool = True) -> None:
    """Configure package logging.

    Args:
        level: Logging level to set when enabled (default: INFO).
        enable: If False, disables all logging from this process (via
            logging.disable). When True, re-enables logging and applies
            a simple basicConfig.
    """
    if not enable:
        logging.disable(logging.CRITICAL)
        return

    # Re-enable and set up a minimal configuration if none existed.
    logging.disable(logging.NOTSET)
    # If root has handlers, don't reconfigure (allow host apps to control)
    root = logging.getLogger()
    if not root.handlers:
        logging.basicConfig(
            level=level,
            format="[%(levelname)s] %(name)s: %(message)s",
        )
    # Ensure package logger has at least requested level
    get_logger().setLevel(level)


def enable_logging(level: int = logging.INFO) -> None:
    """Enable package logging at the given level."""
    configure_logging(level=level, enable=True)


def disable_logging() -> None:
    """Disable logging output entirely."""
    configure_logging(enable=False)
