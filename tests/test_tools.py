import subprocess
import sys

from pykaxe.app import discover_tools


def test_discover_tools_finds_bundled_tools():
    tools = discover_tools()
    assert {"character-count", "word-count", "simple-calculator", "sci-fi-quote-loop"} <= set(tools)


def test_discovered_tools_expose_the_contract():
    for name, module in discover_tools().items():
        assert getattr(module, "TOOL_NAME", None) == name
        assert getattr(module, "TOOL_DESCRIPTION", "")
        assert hasattr(module, "build_parser")
        assert hasattr(module, "main")


def test_simple_calculator_runs_as_a_subprocess():
    tools = discover_tools()
    script = tools["simple-calculator"].__file__

    result = subprocess.run(
        [sys.executable, script, "--number1", "2", "--number2", "3"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == "Result: 5.0"
