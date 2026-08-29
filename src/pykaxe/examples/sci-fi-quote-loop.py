import argparse
import random
import sys
import time

TOOL_NAME = "sci-fi-quote-loop"
TOOL_DESCRIPTION = "Print random original sci-fi cartoon-style messages every 2 seconds."


MESSAGES = [
    "A portal opened, and unfortunately the warranty expired.",
    "We have invented a machine that makes Mondays slightly worse.",
    "Never trust a dimension where everyone owns a space hamster.",
    "The universe is infinite, but our snack supply isn't.",
    "I accidentally taught the robot sarcasm. We're doomed.",
    "Today's experiment requires goggles and questionable judgment.",
    "The portal is stable. Your decision-making is not.",
    "Somewhere in the multiverse, you're already regretting this.",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=TOOL_NAME,
        description=TOOL_DESCRIPTION,
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=2.0,
        help="Seconds between messages.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    if args.interval <= 0:
        print("Error: interval must be greater than 0.", file=sys.stderr)
        return 1

    try:
        while True:
            message = random.choice(MESSAGES)
            print(message, flush=True)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nStopped.", file=sys.stderr)
        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
