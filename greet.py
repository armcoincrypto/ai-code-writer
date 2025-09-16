#!/usr/bin/env python3
import argparse


def main() -> None:
    p = argparse.ArgumentParser(description="Greets a person by name.")
    p.add_argument("-n", "--name", default="World", help="Name to greet")
    args = p.parse_args()
    print(f"Hello, {args.name}!")


if __name__ == "__main__":
    main()
