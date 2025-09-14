#!/usr/bin/env python3
"""
A complete, runnable single-file Python program that builds a CLI to echo input.

This script demonstrates best practices for a modern Python 3.11+ CLI application,
including type hints, docstrings, and the use of the standard `argparse` library.

---
Usage examples from your terminal:
---
1. Run with text to echo:
   python echo_cli.py Hello, modern Python world!
   # Expected output: Hello, modern Python world!

2. Run with quoted text to treat it as a single argument (though the result is the same):  # noqa: E501
   python echo_cli.py "This is one argument"
   # Expected output: This is one argument

3. Run without any text (mimics the shell `echo` command):
   python echo_cli.py
   # Expected output: (a blank line)

4. See the auto-generated help message:
   python echo_cli.py -h
   # Expected output:
   # usage: echo_cli.py [-h] [TEXT ...]
   #
   # A Python CLI that echoes the text you provide.
   #
   # positional arguments:
   #   TEXT        The text to be echoed to the console.
   #
   # options:
   #   -h, --help  show this help message and exit
   #
   # Example: python echo_cli.py hello world
"""

# Import the standard library for parsing command-line arguments.
import argparse


def main() -> None:
    """
    The main function to set up the CLI, parse arguments, and perform the echo action.
    """
    # 1. Initialize the Argument Parser
    # We provide a description and an epilog for a rich `--help` message.
    parser = argparse.ArgumentParser(
        prog="echo_cli",  # The name of the program to show in help messages
        description="A Python CLI that echoes the text you provide.",
        epilog="Example: python echo_cli.py hello world",
    )

    # 2. Define the arguments the CLI will accept
    # We define a single "positional" argument to capture the input text.
    parser.add_argument(
        "text_to_echo",
        metavar="TEXT",  # A name for the argument in usage messages
        type=str,  # The type of the argument
        nargs="*",  # '*' means it will gather 0 or more arguments into a list
        help="The text to be echoed to the console.",
    )

    # 3. Parse the arguments provided by the user from the command line
    args = parser.parse_args()

    # 4. Execute the core logic of the program
    # The parsed arguments are stored in `args.text_to_echo` as a list of strings.
    if args.text_to_echo:
        # If the list is not empty, join its elements with a space and print.
        output_string = " ".join(args.text_to_echo)
        print(output_string)
    else:
        # If no arguments were given, `args.text_to_echo` will be an empty list.
        # In this case, we print an empty line, mimicking the behavior of the
        # standard 'echo' command in Unix-like shells.
        print()


# 5. The standard Python entry point
# This ensures that the `main()` function is called only when the script is
# executed directly (not when it's imported as a module).
if __name__ == "__main__":
    main()
