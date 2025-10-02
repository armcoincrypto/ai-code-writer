#!/usr/bin/env python3

"""
A complete, runnable Python program that prints 'ALL FLAGS'.

This script is a self-contained example demonstrating basic Python
structure, including a main function and the standard
`__name__ == '__main__'` guard.
"""


def main() -> None:
    """
    The main function of the script.

    It performs the primary task: printing the string 'ALL FLAGS' to standard output.
    """
    print("ALL FLAGS")


if __name__ == "__main__":
    # This block ensures that the main() function is called only when
    # the script is executed directly (not when imported as a module).
    main()
