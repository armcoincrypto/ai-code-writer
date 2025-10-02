#!/usr/bin/env python3
"""
Вычислить хеш файла.

Примеры:
  python checksum_cli.py --path file.bin
  python checksum_cli.py --path file.bin --algo sha256 --out digest.txt
  python checksum_cli.py --path file.bin --out digest.txt --dry-run
"""
from __future__ import annotations

import argparse
import hashlib
import os
import pathlib
import sys
from typing import Callable

ALGOS: dict[str, Callable[[], "hashlib._Hash"]] = {
    "sha256": hashlib.sha256,
    "md5": hashlib.md5,
    "sha1": hashlib.sha1,
}


def digest_file(path: pathlib.Path, algo: str) -> str:
    h = ALGOS[algo]()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--path", type=pathlib.Path, required=True, help="Путь к файлу")
    p.add_argument("--out", type=pathlib.Path, help="Куда записать хеш")
    p.add_argument(
        "--dry-run", action="store_true", help="Не записывать файл, только посчитать"
    )
    p.add_argument(
        "--algo",
        choices=sorted(ALGOS.keys()),
        default="sha256",
        help="Алгоритм хеширования (по умолчанию sha256)",
    )
    p.add_argument(
        "--debug-env",
        dest="debug_env",
        action="store_true",
        help="Отладочный вывод переменных окружения (PYTHON*, PATH)",
    )
    args = p.parse_args()

    # если просили — вывести часть окружения (в stderr) и продолжить
    if args.debug_env:
        for k in sorted(os.environ):
            if k.startswith(("PYTHON", "PATH")):
                print(f"{k}={os.environ[k]}", file=sys.stderr)

    if not args.path.is_file():
        print(f"error: file not found: {args.path}", file=sys.stderr)
        return 2

    digest = digest_file(args.path, args.algo)
    line = f"Result: {digest}"

    if args.out:
        if args.dry_run:
            print(line)
        else:
            args.out.write_text(line + "\n", encoding="utf-8")
    else:
        print(line)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
