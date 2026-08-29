import argparse
import sys

TOOL_NAME = "character-count"
TOOL_DESCRIPTION = "Count the number of characters in text."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=TOOL_NAME,
        description=TOOL_DESCRIPTION,
    )
    parser.add_argument(
        "--text",
        type=str,
        required=True,
        help="Text to count characters in.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    try:
        count = len(args.text)
        print(f"Character count: {count}")
        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())