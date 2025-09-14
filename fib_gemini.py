#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A complete, runnable Python program to print Fibonacci numbers up to a
specified limit N, using the argparse standard library for command-line parsing.

This script is compatible with Python 3.11+.

Usage:
    python fibonacci_argparse.py <N>

Example:
    python fibonacci_argparse.py 100
    Fibonacci numbers up to 100:
    0 1 1 2 3 5 8 13 21 34 55 89
"""

# Standard library imports
import argparse
import sys
from typing import Generator, Sequence


def fibonacci_generator(limit: int) -> Generator[int, None, None]:
    """
    Generates Fibonacci numbers up to a given limit (inclusive).

    This function uses an iterative approach which is memory-efficient
    and avoids recursion depth limits.

    Args:
        limit: The non-negative integer upper bound for the sequence.

    Yields:
        The next Fibonacci number in the sequence that is less than or
        equal to the limit.
    """
    a, b = 0, 1  # Initialize the first two Fibonacci numbers
    while a <= limit:
        yield a
        a, b = b, a + b  # Update to the next pair in the sequence


def parse_arguments(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """
    Parses command-line arguments using argparse.

    This setup ensures that the user provides a single, non-negative integer
    argument for the upper limit N.

    Args:
        argv: A sequence of command-line arguments. If None, sys.argv[1:] is used.

    Returns:
        An argparse.Namespace object containing the parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="Print Fibonacci numbers up to a specified limit N.",
        epilog="Example: python %(prog)s 100",
    )

    parser.add_argument(
        "N",
        type=int,
        help="The upper limit for the Fibonacci sequence (a non-negative integer).",
    )

    args = parser.parse_args(argv)

    # Add a specific check for negative numbers, as argparse's `type=int`
    # will accept them. We fail fast with a clear, user-friendly error.
    if args.N < 0:
        parser.error("The limit N must be a non-negative integer.")

    return args


def main() -> None:
    """
    Main function to execute the script's logic.

    It parses arguments, generates the Fibonacci sequence, and prints the result.
    """
    # This script does not require any secret tokens or API keys.
    # If it did, we would check for them here using os.getenv()
    # and fail fast if they were not set, like so:
    #
    # import os
    # MY_TOKEN = os.getenv("MY_APP_TOKEN")
    # if not MY_TOKEN:
    #     print("Error: MY_APP_TOKEN environment variable not set.", file=sys.stderr)
    #     sys.exit(1)

    try:
        # 1. Parse command-line arguments to get the upper limit N
        args = parse_arguments()
        limit = args.N

        print(f"Fibonacci numbers up to {limit}:")

        # 2. Generate the Fibonacci numbers using our modular generator
        fib_numbers = list(fibonacci_generator(limit))

        # 3. Print the results in a clean, space-separated format
        if not fib_numbers:
            # This case is technically unreachable due to our N >= 0 check,
            # but it's good practice for robustness.
            print("No Fibonacci numbers are less than or equal to the specified limit.")
        else:
            # Use the splat (*) operator to print list elements separated by spaces
            print(*fib_numbers)

    except Exception as e:
        # A general catch-all for any other unexpected errors.
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)


# The standard entry point for a Python script.
# This ensures that main() is called only when the script is executed directly.
if __name__ == "__main__":
    main()
