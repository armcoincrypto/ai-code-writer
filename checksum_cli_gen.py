import argparse
import hashlib
import os


def calculate_checksum(path, algo):
    """Calculate checksum for given path and algorithm."""
    if algo not in ["sha256", "md5"]:
        raise ValueError(
            "Invalid algorithm. Supported algorithms are 'sha256' and 'md5'."
        )

    with open(path, "rb") as file:
        data = file.read()

    if algo == "sha256":
        return hashlib.sha256(data).hexdigest()
    else:
        return hashlib.md5(data).hexdigest()


def main():
    """Main function for the checksum CLI."""
    parser = argparse.ArgumentParser(
        description="Calculate checksum for given path and algorithm."
    )
    parser.add_argument("--path", required=True, help="Path to calculate checksum for.")
    parser.add_argument(
        "--algo",
        choices=["sha256", "md5"],
        default="sha256",
        help='Algorithm to use. Defaults to "sha256".',
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only print the result without writing it to file.",
    )
    parser.add_argument(
        "--debug-env", action="store_true", help="Print debug environment variables."
    )

    args = parser.parse_args()

    if args.debug_env:

        print("Debug Environment Variables:")
        for key, value in os.environ.items():
            print(f"{key}={value}")

    result = calculate_checksum(args.path, args.algo)

    if not args.dry_run:
        with open(args.path + ".checksum", "w") as file:
            file.write(result)

    print(f"Result: {result}")


if __name__ == "__main__":
    main()
