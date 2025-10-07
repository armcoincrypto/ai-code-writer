from __future__ import annotations

import importlib
import sys
from typing import Tuple


def python_meets_requirement(req_major: int, req_minor: int) -> bool:
    cur: Tuple[int, int] = sys.version_info[:2]
    return cur >= (req_major, req_minor)


def has_module(name: str) -> tuple[bool, str | None]:
    try:
        mod = importlib.import_module(name)
        ver = getattr(mod, "__version__", None)
        return True, ver
    except Exception:
        return False, None
