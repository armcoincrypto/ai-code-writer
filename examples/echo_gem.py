#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
A complete, runnable, single-file Python program that builds a CLI to echo input.

This script demonstrates basic command-line argument handling using the `sys` module.

---
Python Version: 3.11+
Dependencies: None (only standard library)
---

Usage:
    python echo_cli.py Hello world! This is a test.

    # With execute permissions:
    ./echo_cli.py "Quoted arguments are treated as a single one"

Example Output:
    Hello world! This is a test.
    Quoted arguments are treated as a single one

If run with no arguments, it will print a usage message to standard error.
"""

import sys
from typing import List


def main(args: List[str]) -> int:
    """
    The main entry point for the echo command-line interface.

    Args:
        args: A list of command-line arguments, where the first element
              is the script name itself.

    Returns:
        An integer exit code. 0 for success, 1 for an error.
    """
    # The first argument (args[0]) is always the script's name.
    # We check if there are any arguments *after* the script name.
    if len(args) > 1:
        # Slice the list to get only the user-provided arguments (from index 1 onwards).
        input_to_echo = args[1:]

        # Join the arguments with a space to form a single string.
        # This correctly handles multiple words passed as separate arguments.
        output_string = " ".join(input_to_echo)

        # Print the resulting string to standard output.
        print(output_string)

        # Return 0 for a successful execution.
        return 0
    else:
        # No arguments were provided, so print a usage message.
        # It's standard practice to print errors/usage info to stderr.
        script_name = args[0]
        print(f"Usage: python {script_name} <text to echo...>", file=sys.stderr)
        print("Error: No input provided to echo.", file=sys.stderr)

        # Return a non-zero exit code to indicate an error.
        return 1


if __name__ == "__main__":
    # The `sys.argv` list contains the command-line arguments passed to the script.
    # It is passed directly to the main function.
    # The script's exit code is determined by the return value of main().
    sys.exit(main(sys.argv))
