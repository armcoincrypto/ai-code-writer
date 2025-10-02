import argparse


def add_numbers(a, b):
    """Return the sum of two numbers."""
    return a + b


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A CLI to add two numbers.")
    parser.add_argument("--a", type=float, required=True, help="The first number.")
    parser.add_argument("--b", type=float, required=True, help="The second number.")

    args = parser.parse_args()

    result = add_numbers(args.a, args.b)
    print(f"Result: {result:.2f}")
