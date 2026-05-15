"""Constants and types used throughout the fishy_config package."""

from typing import Any, Dict, List, Optional, Union
from pathlib import Path

ContextValue = Union[Path, str, int, float, bool, None, Dict[str, Any], List[Any]]

PACKAGE_NAME = "fishy_config"