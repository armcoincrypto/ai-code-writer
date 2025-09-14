#!/usr/bin/env python3
"""
A complete, runnable Python program that prints the number 1.

This script demonstrates standard Python best practices including a main entry point,
modular function design, and a pattern for handling environment variables.
"""

import os
import sys
from typing import NoReturn


def _exit_with_error(message: str) -> NoReturn:
    """Prints an error message to stderr and exits with a non-zero status code."""
    print(f"Error: {message}", file=sys.stderr)
    sys.exit(1)


def get_required_env_var(var_name: str) -> str:
    """
    Retrieves a required environment variable and fails fast if it's not set.

    This function serves as a template for robustly handling configuration
    but is not used in this specific program as no tokens are needed.

    Args:
        var_name: The name of the environment variable to retrieve.

    Returns:
        The value of the environment variable.

    Raises:
        SystemExit: If the environment variable is not found.
    """
    value = os.environ.get(var_name)
    if value is None:
        # Fail fast if a required environment variable is missing.
        _exit_with_error(f"Required environment variable '{var_name}' is not set.")
    return value


def main() -> None:
    """
    Main function to execute the primary logic of the script.
    """
    # This specific task does not require any tokens or environment variables.
    # If a token were needed, it would be retrieved like this:
    # api_key = get_required_env_var("MY_API_TOKEN")

    # The primary task: print the integer 1 to standard output.
    print(1)


if __name__ == "__main__":
    # This standard entry point ensures that the main() function is called
    # only when the script is executed directly, not when imported as a module.
    main()
