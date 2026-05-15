"""Basic logging utilities for fishy-config.

Provides a small wrapper around Python logging so callers can enable/disable
and configure a consistent logger for the package.
"""

from __future__ import annotations

import logging
from typing import Optional

try:
    from rich.logging import RichHandler
except ImportError:  # pragma: no cover - fallback when rich isn't installed
    RichHandler = None  # type: ignore[assignment]

from .models.constants import PACKAGE_NAME


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Return a logger scoped to the fishy-config package.

    Use `configure_logging` to adjust global logging behavior.
    """
    if name:
        return logging.getLogger(f"{PACKAGE_NAME}.{name}")
    return logging.getLogger(PACKAGE_NAME)


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

    # Re-enable and set up a colorful configuration if none existed.
    logging.disable(logging.NOTSET)
    root = logging.getLogger()

    # If root has handlers, don't reconfigure (allow host apps to control).
    if not root.handlers:
        if RichHandler is not None:
            handler = RichHandler(
                rich_tracebacks=True,
                show_time=False,
                show_path=False,
                markup=False,
            )
            handler.setFormatter(logging.Formatter("%(message)s"))
            root.addHandler(handler)
            root.setLevel(level)
        else:
            logging.basicConfig(
                level=level,
                format="[%(levelname)s] %(name)s: %(message)s",
            )

    # Ensure loggers inherit and respect requested level.
    root.setLevel(level)
    get_logger().setLevel(level)


def enable_logging(level: int = logging.INFO) -> None:
    """Enable package logging at the given level."""
    configure_logging(level=level, enable=True)


def disable_logging() -> None:
    """Disable logging output entirely."""
    configure_logging(enable=False)
