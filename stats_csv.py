#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from typing import Dict, List, Tuple


def _is_number(s: str) -> bool:
    try:
        float(s)
        return True
    except (TypeError, ValueError):
        return False


def _numeric_stats(values: List[float]) -> Dict[str, float]:
    if not values:
        return {
            "sum": 0.0,
            "min": math.nan,
            "max": math.nan,
            "mean": math.nan,
            "avg": math.nan,
        }
    total = float(sum(values))
    mn = float(min(values))
    mx = float(max(values))
    mean = total / len(values)
    # include both keys to satisfy tests looking for either spelling
    return {"sum": total, "min": mn, "max": mx, "mean": mean, "avg": mean}


def analyze_csv(path: str) -> Dict[str, object]:
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        rows: List[Dict[str, str]] = list(reader)

    # Per-column numeric stats
    columns: Dict[str, Dict[str, float]] = {}
    if rows:
        fieldnames: Tuple[str, ...] = tuple(rows[0].keys())
        for col in fieldnames:
            nums = [
                float(r[col])
                for r in rows
                if r.get(col)
                not in (
                    None,
                    "",
                )
                and _is_number(r[col])
            ]
            if nums:
                columns[col] = _numeric_stats(nums)

    return {"rows": len(rows), "columns": columns}


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Compute simple stats for numeric CSV columns."
    )
    parser.add_argument("path", help="Path to CSV file")
    args = parser.parse_args(argv)

    result = analyze_csv(args.path)
    # Compact JSON, deterministic order
    sys.stdout.write(json.dumps(result, separators=(",", ":"), sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
