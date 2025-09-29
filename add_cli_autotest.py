#!/usr/bin/env python3
"""
Простой CLI для автотеста.
По умолчанию складывает 2 и 3.
Можно передать аргументы: --a 2 --b 5
Вывод обязательно содержит 'Result:' (так требует тест).
"""
from __future__ import annotations

import argparse


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--a", type=float, default=2.0, help="Первое число")
    p.add_argument("--b", type=float, default=3.0, help="Второе число")
    args = p.parse_args()
    s = args.a + args.b
    print(f"Result: {s:.2f}")


if __name__ == "__main__":
    main()
