#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
A complete, runnable Python program that prints a success message.
This script is structured with a main function and the standard
__name__ == '__main__' guard, following best practices.
"""


def main() -> None:
    """
    The main entry point for the program.

    This function performs the primary task of printing the success message
    'UNIT TEST OK' to the standard output.
    """
    print("UNIT TEST OK")


if __name__ == "__main__":
    # This conditional block is the standard entry point for a Python script.
    # It ensures that the main() function is called only when this script
    # is executed directly, and not when it is imported as a module into
    # another script.
    main()
