import argparse
import sys
from pathlib import Path

TOOL_NAME = "line-count"
TOOL_DESCRIPTION = "Count the number of lines in a file."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=TOOL_NAME,
        description=TOOL_DESCRIPTION,
    )
    parser.add_argument(
        "--file",
        type=Path,
        required=True,
        help="Path to the file to count lines in.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    try:
        with args.file.open("r", encoding="utf-8", errors="replace") as f:
            count = sum(1 for _ in f)
        print(f"Line count: {count}")
        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
