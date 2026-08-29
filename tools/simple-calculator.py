import argparse
import sys

TOOL_NAME = "simple-calculator"
TOOL_DESCRIPTION = "Add two numbers together."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=TOOL_NAME,
        description=TOOL_DESCRIPTION,
    )
    parser.add_argument(
        "--number1",
        type=float,
        required=True,
        help="First number.",
    )
    parser.add_argument(
        "--number2",
        type=float,
        required=True,
        help="Second number.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    try:
        result = args.number1 + args.number2
        print(f"Result: {result}")
        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
