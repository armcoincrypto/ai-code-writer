#!/usr/bin/env python3
"""
Recursive Folder Watcher
Usage:
  python3 watcher.py --path . --interval 2
Requirements:
  None (uses only stdlib)
"""
import argparse
import logging
import os
import sys
import time


def collect_paths(root):
    paths = set()
    for dirpath, _, files in os.walk(root):
        for f in files:
            rel = os.path.relpath(os.path.join(dirpath, f), root)
            paths.add(rel)
    return paths


def main():
    p = argparse.ArgumentParser("Recursively watch a folder for new files.")
    p.add_argument("--path", required=True, help="Directory to watch")
    p.add_argument("--interval", type=float, default=2.0, help="Polling interval")
    args = p.parse_args()

    if not os.path.isdir(args.path):
        print(f"❌ Not a directory: {args.path}")
        sys.exit(1)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    log = logging.getLogger()

    log.info("Starting recursive watcher on %s", args.path)
    seen = collect_paths(args.path)
    log.info("Found %d initial file(s).", len(seen))

    try:
        while True:
            time.sleep(args.interval)
            current = collect_paths(args.path)
            new = current - seen
            if new:
                for rel in sorted(new):
                    log.info("New file detected: %s", rel)
                seen = current
    except KeyboardInterrupt:
        log.info("Watcher stopped.")
        sys.exit(0)


if __name__ == "__main__":
    main()
