#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
A simple Python program that prints a specific string to the console.

This script serves as a basic example of a runnable Python file,
including a main function and the standard entry point guard.
"""


def main() -> None:
    """
    The main function of the program.

    It performs the primary task, which is to print 'VERBOSE?'.
    """
    print("VERBOSE?")


if __name__ == "__main__":
    # This block ensures that the main() function is called only when
    # the script is executed directly (not when imported as a module).
    main()
