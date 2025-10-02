#!/usr/bin/env python3
"""
A simple, complete, and runnable Python program that prints 'SANDBOX'.

This script demonstrates the standard structure for a Python application,
including a main function and the common entry point guard.
"""


def main() -> None:
    """
    The primary function of the script, which executes the main task.
    """
    print("SANDBOX")


if __name__ == "__main__":
    # This block ensures that the main() function is called only when
    # the script is executed directly (not when imported as a module).
    main()
