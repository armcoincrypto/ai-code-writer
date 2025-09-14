# -*- coding: utf-8 -*-
"""
A complete, runnable Python program that prints the number 2.

This script adheres to modern Python 3.11+ development practices,
including modular functions, type hints, and standard entry point construction.
"""

import sys

# This program does not require any external tokens or credentials.
# If it did, we would read them from environment variables here.
# For example:
#
# import os
#
# try:
#     # Attempt to get a required token from the environment.
#     API_TOKEN = os.environ["REQUIRED_API_TOKEN"]
# except KeyError:
#     # Fail fast with a clear error message if the token is not set.
# print("Error: Environment variable 'REQUIRED_API_TOKEN' not set.", file=sys.stderr)
#     sys.exit(1)


def perform_core_task() -> None:
    """
    Executes the primary logic of the program.

    In this case, the task is simply to print the integer 2 to standard output.
    """
    # The core action: print the number 2.
    print(2)


def main() -> int:
    """
    Main entry point for the script.

    This function orchestrates the program's execution flow.
    """
    # Call the modular function that performs the specific task.
    perform_core_task()

    # Return 0 to indicate successful execution.
    return 0


if __name__ == "__main__":
    # This conditional block ensures that the 'main' function is called
    # only when the script is executed directly (not when imported as a module).
    # sys.exit() is used to properly pass the exit code to the shell.
    sys.exit(main())
