from pykaxe.cli import check_contract

VALID_TOOL = '''
import argparse
import sys

TOOL_NAME = "greet"
TOOL_DESCRIPTION = "Say hello."

def build_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(prog=TOOL_NAME)

def main() -> int:
    print("hello")
    return 0

if __name__ == "__main__":
    sys.exit(main())
'''


def test_check_contract_accepts_a_valid_tool():
    assert check_contract(VALID_TOOL) == []


def test_check_contract_flags_missing_pieces():
    missing = check_contract("TOOL_NAME = 'x'\n")
    assert any("TOOL_DESCRIPTION" in item for item in missing)
    assert any("build_parser" in item for item in missing)
    assert any("main" in item for item in missing)
