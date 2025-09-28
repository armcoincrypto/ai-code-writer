#!/usr/bin/env python3
"""
checksum_cli: compute a file's digest with a safe dry-run and env debug.

Usage:
  python3 checksum_cli.py --path FILE [--algo sha256|md5] [--out OUT]
                          [--dry-run] [--debug-env]

Behavior:
  - Prints "Result: <hexdigest>" to stdout on success.
  - If --out is provided and not --dry-run, writes the hex digest to that file.
  - --debug-env prints a JSON of environment keys that are NOT secrets.
  - Exits 2 with a helpful message on invalid args or missing file.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Iterable

_CHUNK: int = 1024 * 1024  # 1 MiB
_SECRET_MARKERS = ("KEY", "TOKEN", "SECRET", "PASS")


def _filter_env(environ: Iterable[tuple[str, str]]) -> Dict[str, str]:
    """Return a dict of non-secret env keys/values (basic heuristic)."""
    safe: Dict[str, str] = {}
    for k, v in environ:
        upper = k.upper()
        if any(marker in upper for marker in _SECRET_MARKERS):
            continue
        # keep short values only (avoid dumping huge blobs)
        if len(v) > 200:
            continue
        safe[k] = v
    return safe


def _compute_digest(path: Path, algo: str) -> str:
    """Compute md5/sha256 digest of a file by streaming."""
    if algo == "md5":
        h = hashlib.md5()  # noqa: S324 - CLI helper, not for cryptographic security
    else:
        h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(_CHUNK)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Compute a file digest.")
    p.add_argument("--path", required=True, help="Path to input file")
    p.add_argument(
        "--algo",
        choices=("sha256", "md5"),
        default="sha256",
        help="Hash algorithm (default: sha256)",
    )
    p.add_argument("--out", help="Optional file path to write hex digest")
    p.add_argument(
        "--dry-run", action="store_true", help="Compute but do not write files"
    )
    p.add_argument(
        "--debug-env",
        action="store_true",
        help="Print a JSON of safe environment keys (filters secrets)",
    )
    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    in_path = Path(args.path)
    if not in_path.is_file():
        parser.exit(2, f"error: file not found: {in_path}\n")

    if args.debug_env:
        safe_env = _filter_env(os.environ.items())
        print(json.dumps({"env": safe_env}, indent=2, sort_keys=True))

    digest = _compute_digest(in_path, args.algo)
    print(f"Result: {digest}")

    if args.out:
        out_path = Path(args.out)
        if args.dry_run:
            # Skip writing
            return 0
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(digest + "\n", encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
