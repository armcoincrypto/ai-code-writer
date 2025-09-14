#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
A simple, complete Python program to print a specific word.

This script demonstrates the standard structure for a runnable Python file,
including a main function and the common `if __name__ == '__main__'` guard.
"""


def main() -> None:
    """
    The primary function of the script.

    It executes the main task, which is to print the string 'QUIET'
    to standard output.
    """
    print("QUIET")


if __name__ == "__main__":
    # This block ensures that the main() function is called only when
    # the script is executed directly, not when it's imported as a module.
    main()
