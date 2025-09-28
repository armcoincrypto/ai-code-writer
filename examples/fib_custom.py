#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
A complete, runnable Python script to print Fibonacci numbers up to a given limit N.

This program uses the standard library's `argparse` module to handle
command-line arguments. It is designed to be modular and follows modern
Python 3.11+ best practices, including type hinting.

No external tokens or environment variables are required for this task.

Usage:
    python this_script_name.py <N>

Example:
    python this_script_name.py 100
"""

import argparse
import sys
from typing import Generator


def non_negative_int(value: str) -> int:
    """
    Custom argparse type for a non-negative integer.

    This function is used by argparse to validate that the input 'N' is an
    integer and is not negative.

    Args:
        value: The command-line argument value as a string.

    Returns:
        The value as an integer if it is a valid non-negative integer.

    Raises:
        argparse.ArgumentTypeError: If the value is not a valid non-negative integer.
    """
    try:
        ivalue = int(value)
        if ivalue < 0:
            # Raise an error if the number is negative.
            raise argparse.ArgumentTypeError(f"{value} is not a non-negative integer")
        return ivalue
    except ValueError:
        # Catches cases where `int(value)` fails, e.g., for non-numeric input.
        raise argparse.ArgumentTypeError(f"invalid integer value: '{value}'")


def fibonacci_generator(limit: int) -> Generator[int, None, None]:
    """
    Generates Fibonacci numbers up to a specified limit (inclusive).

    This function uses a generator to be memory-efficient, especially for
    large limits, as it yields numbers one by one instead of storing the
    entire sequence in memory.

    Args:
        limit: The maximum value for the Fibonacci numbers to be generated.

    Yields:
        The next Fibonacci number in the sequence that is less than or equal to the limit.  # noqa: E501
    """
    a, b = 0, 1  # Initialize the first two Fibonacci numbers
    while a <= limit:
        yield a
        a, b = b, a + b  # Calculate the next number in the sequence


def main() -> None:
    """
    Main function to parse arguments and print the Fibonacci sequence.
    """
    # Set up the command-line argument parser with a description and example.
    parser = argparse.ArgumentParser(
        description="Print Fibonacci numbers up to a specified limit N.",
        epilog="Example: python %(prog)s 100",
    )

    # Add the required positional argument 'N'.
    # It must be a non-negative integer, validated by our custom type function.
    parser.add_argument(
        "n",
        type=non_negative_int,
        help="The upper limit (a non-negative integer) for the Fibonacci sequence.",
    )

    # Parse the command-line arguments.
    # If arguments are invalid, argparse will automatically print help and exit.
    args = parser.parse_args()
    limit: int = args.n

    try:
        # Generate the list of Fibonacci numbers from our generator.
        fib_numbers = list(fibonacci_generator(limit))

        # Print the results in a user-friendly format.
        print(f"Fibonacci sequence up to {limit}:")
        if not fib_numbers:
            # This case is only possible if the limit is negative, which our
            # type checker prevents. It's included for robustness.
            print("No Fibonacci numbers within the specified limit.")
        else:
            # Use the splat operator (*) to print list elements separated by spaces.
            print(*fib_numbers)

    except Exception as e:
        # Catch any unexpected errors during execution and report them.
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)


# Standard Python entry point.
if __name__ == "__main__":
    main()
