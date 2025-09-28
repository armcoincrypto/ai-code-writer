#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
A command-line tool to print Fibonacci numbers up to a specified limit N.

This script demonstrates the use of the `argparse` module for command-line
argument processing, generators for efficient sequence creation, and modern
Python best practices like type hinting and f-strings.

Python 3.11+ is recommended.

Example Usage:
    # Print Fibonacci numbers up to 100
    python fibonacci_argparse.py 100

    # Get help message
    python fibonacci_argparse.py -h
"""

import argparse
from typing import Iterator


def fibonacci_generator(max_n: int) -> Iterator[int]:
    """
    A memory-efficient generator for the Fibonacci sequence.

    This function yields Fibonacci numbers one by one as long as they are
    less than or equal to the specified maximum value.

    Args:
        max_n: The non-negative integer upper bound for the sequence.

    Yields:
        Integers in the Fibonacci sequence up to max_n.
    """
    a, b = 0, 1
    while a <= max_n:
        yield a
        a, b = b, a + b


def main() -> None:
    """
    Parses command-line arguments and prints the Fibonacci sequence.
    """
    # 1. Set up the argument parser
    parser = argparse.ArgumentParser(
        description="Print Fibonacci numbers up to a specified limit N.",
        epilog="Example: python %(prog)s 50",
    )

    # 2. Define the command-line arguments
    parser.add_argument(
        "N",
        type=int,
        help="The upper limit for the Fibonacci sequence (a non-negative integer).",
    )

    # 3. Parse the arguments from the command line
    args = parser.parse_args()
    limit = args.N

    # 4. Validate the input
    if limit < 0:
        # Use parser.error() for a clean exit with a helpful message
        parser.error("The limit N must be a non-negative integer.")

    # 5. Generate and print the results
    print(f"Fibonacci sequence up to {limit}:")

    # Generate the sequence. We can convert the generator to a list to print.
    fib_numbers = list(fibonacci_generator(limit))

    if not fib_numbers:
        print("(No Fibonacci numbers are less than or equal to the limit)")
    else:
        # The * operator unpacks the list into individual arguments for print()
        # This prints them space-separated by default.
        print(*fib_numbers)


# 6. Standard boilerplate to run the main() function
if __name__ == "__main__":
    main()
