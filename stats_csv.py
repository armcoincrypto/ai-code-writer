#!/usr/bin/env python3
"""
Read a CSV and print mean/median of a column (default: 'value').

Usage:
  # Demo mode (no args, empty stdin): prints stats of built-in sample
  python3 stats_csv.py

  # File path (positional)
  python3 stats_csv.py data.csv

  # Pipe via stdin
  cat data.csv | python3 stats_csv.py

  # Options
  python3 stats_csv.py data.csv --column price --round 4
"""
from __future__ import annotations

import argparse
import io
import sys
from typing import Optional


def _stdin_has_data() -> bool:
    """Return True if stdin is non-tty and has data ready (non-blocking)."""
    try:
        if sys.stdin is None or sys.stdin.closed or sys.stdin.isatty():
            return False
        import select  # POSIX-safe readiness check

        r, _, _ = select.select([sys.stdin], [], [], 0)
        return bool(r)
    except Exception:
        return False


def _compute_stats(series, ndigits: int) -> str:
    s = series.dropna()
    try:
        s = s.astype(float)
    except Exception:
        # If coercion fails, try to coerce with errors='coerce' and drop NaNs
        s = s.astype(str)
        import pandas as pd  # local import to avoid top-level hard dep in tests

        s = pd.to_numeric(s, errors="coerce").dropna()
    if len(s) == 0:
        return "mean=nan median=nan"
    mean = float(s.mean())
    # median may be numpy float; ensure plain float
    median = float(s.median())
    if ndigits is not None and ndigits >= 0:
        return f"mean={mean:.{ndigits}g} median={median:.{ndigits}g}"
    return f"mean={mean} median={median}"


def _read_dataframe(path: Optional[str], column: str):
    """
    Return a pandas DataFrame from:
      1) file path if provided,
      2) stdin if data present,
      3) tiny demo DataFrame otherwise.
    """
    try:
        import pandas as pd  # requires: pip install "pandas>=2.2"
    except Exception as e:
        print(f"pandas import failed: {e}", file=sys.stderr)
        sys.exit(2)

    # 1) Path provided
    if path:
        return pd.read_csv(path)

    # 2) Stdin data present
    if _stdin_has_data():
        data = sys.stdin.read()
        if data and data.strip():
            return pd.read_csv(io.StringIO(data))

    # 3) Demo dataset so zero-arg runs & tests don’t hang
    return pd.DataFrame({column: [10, 20, 40]})


def run(path: Optional[str], column: str, ndigits: int) -> int:
    try:
        df = _read_dataframe(path, column)
    except Exception as e:
        print(f"Failed to read CSV: {e}", file=sys.stderr)
        return 3

    if column not in df.columns:
        print(
            f"CSV must contain a '{column}' column. Found: {list(df.columns)}",
            file=sys.stderr,
        )
        return 4

    print(_compute_stats(df[column], ndigits))
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Print mean/median of a CSV column (default 'value')."
    )
    # ✅ Optional positional arg so `python stats_csv.py <path>` works
    ap.add_argument(
        "input", nargs="?", help="Path to CSV (omit to read stdin or run demo)"
    )
    ap.add_argument(
        "--column",
        "-c",
        default="value",
        help="Column name to analyze (default: value)",
    )
    ap.add_argument(
        "--round",
        type=int,
        default=6,
        dest="round_",
        help="Significant digits (default: 6)",
    )
    args = ap.parse_args()
    sys.exit(run(args.input, args.column, args.round_))


if __name__ == "__main__":
    main()
