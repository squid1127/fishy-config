"""Common types used across the project."""

from typing import Any, Dict, List, Optional, Union
from pathlib import Path

ContextValue = Union[Path, str, int, float, bool, None, Dict[str, Any], List[Any]]