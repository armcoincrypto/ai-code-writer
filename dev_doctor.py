from __future__ import annotations

import importlib
import sys
from typing import Tuple


def python_meets_requirement(req_major: int, req_minor: int) -> bool:
    """
    True if current interpreter version >= (req_major, req_minor).

    Example:
        python_meets_requirement(3, 11) -> True on Python 3.11+
    """
    cur_major, cur_minor = sys.version_info[:2]  # type: Tuple[int, int]
    return (cur_major, cur_minor) >= (req_major, req_minor)


def has_module(name: str) -> Tuple[bool, str]:
    """
    Try to import a module by name. Return (ok, error_message).
    ok=True if import succeeded; otherwise ok=False and error_message contains details.
    """
    try:
        importlib.import_module(name)
        return True, ""
    except Exception as e:  # pragma: no cover - exact text not asserted
        return False, f"{type(e).__name__}: {e}"


if __name__ == "__main__":
    print(
        {
            "python": ".".join(map(str, sys.version_info[:3])),
            "meets_3_11": python_meets_requirement(3, 11),
            "has_sys": has_module("sys")[0],
        }
    )
