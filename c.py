# Filename: print_three.py
# Description: A simple Python program to print the number 3, following best practices.
# Author: Your Name
# Date: 2023-10-27

import sys


def print_number() -> None:
    """
    Performs the core task of printing the number 3 to standard output.
    """
    # This program's primary function is to print the integer 3.
    # No complex logic or external tokens are needed for this operation.
    print(3)


def main() -> int:
    """
    Main entry point for the script.

    This function orchestrates the program's execution by calling the
    necessary functions to complete the task.

    Returns:
        int: An exit code (0 for success).
    """
    print_number()
    return 0


if __name__ == "__main__":
    # This conditional block ensures that the main() function is called
    # only when the script is executed directly, not when imported as a module.
    # The exit code from main() is passed to sys.exit().
    sys.exit(main())
