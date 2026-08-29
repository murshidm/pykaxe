import argparse
import asyncio
import contextlib
import importlib.util
import os
import signal
import subprocess
import sys
from collections import deque
from pathlib import Path
from types import ModuleType

from pykaxe import config

try:
    import resource
except ImportError:  # Windows has no resource module
    resource = None

from textual import events
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Input, OptionList, RichLog, Static
from textual.widgets.option_list import Option
from rich.markup import escape as escape_markup
from rich.text import Text

WHITE = "#f2f2f2"
MUTED = "#8a8a8a"
BORDER = "#3a3a3a"
BG = "ansi_default"
RESULT = "#7ee787"
TOOL = "#f2c94c"

# Protection limits for running tools. Tool scripts are user-authored and
# untrusted, so every guard here lives on the app side rather than relying
# on the script to behave.
MAX_OUTPUT_LINES = 2000  # scrollback kept per shell (and in the RichLog widget)
MAX_OUTPUT_BYTES = 4 * 1024 * 1024  # auto-kill a tool that floods stdout/stderr
MAX_TOOL_MEMORY_BYTES = 256 * 1024 * 1024  # RLIMIT_AS ceiling for a tool process
MAX_TOOL_CPU_SECONDS = 120  # RLIMIT_CPU ceiling; catches tight busy-loops fast
MAX_TOOL_RUNTIME_SECONDS = 30 * 60  # wall-clock safety net for polling loops

POSIX = sys.platform != "win32"


def footer_label(key: str, label: str) -> str:
    return f"[{WHITE}]{escape_markup(f'[{key}]')}[/] [{MUTED}]{label}[/]"


def fuzzy_filter(query: str, names: list[str]) -> list[str]:
    query = query.lower()
    if not query:
        return sorted(names)
    scored = []
    for name in names:
        low = name.lower()
        pos = -1
        first = None
        ok = True
        for ch in query:
            pos = low.find(ch, pos + 1)
            if pos == -1:
                ok = False
                break
            if first is None:
                first = pos
        if ok:
            scored.append((first, len(name), name))
    scored.sort()
    return [name for _, _, name in scored]


def discover_tools(tools_dir: Path) -> dict[str, ModuleType]:
    tools: dict[str, ModuleType] = {}
    if not tools_dir.is_dir():
        return tools
    for script in tools_dir.glob("*.py"):
        spec = importlib.util.spec_from_file_location(script.stem, script)
        if spec is None or spec.loader is None:
            continue
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except Exception:
            continue
        name = getattr(module, "TOOL_NAME", None)
        if name:
            tools[name] = module
    return tools


def _limit_tool_resources() -> None:
    """Runs in the child process right before exec (POSIX only). Best
    effort: caps are silently skipped where the platform won't allow them,
    since this is a safety net, not the primary defense (that's the app
    being able to kill the process outright at any time)."""
    if resource is None:
        return
    try:
        resource.setrlimit(resource.RLIMIT_AS, (MAX_TOOL_MEMORY_BYTES, MAX_TOOL_MEMORY_BYTES))
    except (ValueError, OSError):
        pass
    try:
        resource.setrlimit(resource.RLIMIT_CPU, (MAX_TOOL_CPU_SECONDS, MAX_TOOL_CPU_SECONDS))
    except (ValueError, OSError):
        pass


class Shell:
    def __init__(self) -> None:
        self.lines: deque[str] = deque(maxlen=MAX_OUTPUT_LINES)
        self.tool: str | None = None
        self.script: Path | None = None
        self.pending_args: list = []
        self.arg_index: int = 0
        self.values: dict[str, str] = {}
        self.process: asyncio.subprocess.Process | None = None
        self.runner_task: asyncio.Task | None = None


class StatusBar(Horizontal):
    def compose(self) -> ComposeResult:
        yield Button(footer_label("esc", "interrupt"), id="interrupt", classes="footer-btn")
        yield Button(footer_label("ctrl+y", "copy"), id="copy_output", classes="footer-btn")
        yield Button(footer_label("ctrl+s", "scan"), id="scan_tools", classes="footer-btn")
        yield Button(footer_label("ctrl+c", "quit"), id="quit", classes="footer-btn")


class Pykaxe(App):
    CSS = f"""
    Screen {{
        background: {BG};
    }}
    #badge {{
        display: none;
        height: 1;
        background: {TOOL};
        color: #1a1a1a;
        content-align: left middle;
        padding: 0 1;
        text-style: bold;
    }}
    RichLog {{
        background: {BG};
        border: round {BORDER};
        scrollbar-background: transparent;
        scrollbar-color: transparent;
        scrollbar-corner-color: transparent;
        scrollbar-background-hover: {BG};
        scrollbar-color-hover: {MUTED};
        scrollbar-background-active: {BG};
        scrollbar-color-active: {WHITE};
    }}
    Button {{
        background: {BG};
        border: solid {BORDER};
        text-style: none;
    }}
    Button:hover {{
        background: {BG};
        border: solid {WHITE};
        text-style: none;
    }}
    Button:focus {{
        text-style: none;
    }}
    #bottom {{
        dock: bottom;
        height: auto;
        background: {BG};
    }}
    Input {{
        background: {BG};
        border: round {BORDER};
    }}
    Input:focus {{
        border: round {WHITE};
    }}
    StatusBar {{
        height: 1;
        background: {BG};
        padding: 0 1;
    }}
    .footer-btn {{
        min-width: 0;
        height: 1;
        background: {BG};
        border: none;
        margin-right: 2;
    }}
    #suggestions {{
        display: none;
        height: auto;
        max-height: 6;
        background: {BG};
        border: round {BORDER};
        scrollbar-background: transparent;
        scrollbar-color: transparent;
        scrollbar-corner-color: transparent;
        scrollbar-background-hover: {BG};
        scrollbar-color-hover: {MUTED};
        scrollbar-background-active: {BG};
        scrollbar-color-active: {WHITE};
    }}
    OptionList {{
        background: {BG};
    }}
    OptionList > .option-list--option-highlighted {{
        background: {BORDER};
        text-style: none;
    }}
    """

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", priority=True),
        Binding("ctrl+y", "copy_output", "Copy output"),
        Binding("ctrl+s", "scan_tools", "Scan tools"),
        # priority=True: this must win over whatever widget has focus (e.g.
        # the Input) so a runaway tool can always be killed immediately.
        Binding("escape", "interrupt", "Interrupt", priority=True),
    ]

    def __init__(self, tools_dir: Path) -> None:
        super().__init__(ansi_color=True)
        self.tools_dir = tools_dir
        self.shell = Shell()
        self.tools: dict[str, ModuleType] = {}

    def compose(self) -> ComposeResult:
        yield Static("", id="badge")
        yield RichLog(markup=True, wrap=True, max_lines=MAX_OUTPUT_LINES)
        with Vertical(id="bottom"):
            yield OptionList(id="suggestions")
            yield Input(placeholder="Type / to load a tool...")
            yield StatusBar()

    def on_mount(self) -> None:
        self.tools = discover_tools(self.tools_dir)
        self._show_welcome()
        self.update_badge()
        self._focus_input()

    def _clear_screen(self) -> None:
        self.shell.lines.clear()
        self.query_one(RichLog).clear()

    def _show_welcome(self) -> None:
        self.write_line(f"[{WHITE}]pykaxe[/]")
        self.write_line("")
        if self.tools:
            self.write_line(f"[{MUTED}]available tools[/]")
            width = max(len(name) for name in self.tools)
            for name in sorted(self.tools):
                desc = getattr(self.tools[name], "TOOL_DESCRIPTION", "")
                line = f"  [{TOOL}]/{escape_markup(name)}[/]"
                if desc:
                    line += f"{' ' * (width - len(name))}  [{MUTED}]{escape_markup(desc)}[/]"
                self.write_line(line)
            self.write_line("")
        self.write_line(f"[{MUTED}]type / to load a tool[/]")
        self.write_line("")

    def _focus_input(self) -> None:
        self.query_one(Input).focus()

    def on_click(self, event: events.Click) -> None:
        # The Input is the only thing worth typing into — whatever else got
        # clicked (the log, a suggestion, the interrupt button) has already
        # handled the click itself by the time this fires, so just make
        # sure a cursor is always waiting in the Input afterward.
        self._focus_input()

    def write_line_to(self, shell: Shell, text: str) -> None:
        shell.lines.append(text)
        if shell is self.shell:
            self.query_one(RichLog).write(text)

    def write_line(self, text: str) -> None:
        self.write_line_to(self.shell, text)

    def on_input_changed(self, event: Input.Changed) -> None:
        suggestions = self.query_one("#suggestions", OptionList)
        if not event.value.startswith("/"):
            suggestions.display = False
            return

        matches = fuzzy_filter(event.value[1:], list(self.tools.keys()))
        suggestions.clear_options()
        if not matches:
            suggestions.display = False
            return
        for name in matches[:8]:
            desc = getattr(self.tools[name], "TOOL_DESCRIPTION", "")
            label = f"[{TOOL}]{escape_markup(name)}[/]"
            if desc:
                label += f": {escape_markup(desc)}"
            suggestions.add_option(Option(label, id=name))
        suggestions.display = True

    async def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option_list.id != "suggestions" or event.option.id is None:
            return
        self.query_one(Input).value = ""
        self.query_one("#suggestions", OptionList).display = False
        await self.load_tool(event.option.id)
        self._focus_input()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value
        event.input.value = ""
        self.query_one("#suggestions", OptionList).display = False

        shell = self.shell
        if text.startswith("/"):
            query = text[1:].strip()
            matches = fuzzy_filter(query, list(self.tools.keys()))
            if matches:
                await self.load_tool(matches[0])
            else:
                self.write_line(text)
                self.write_line(f"[{MUTED}]no such tool: {query}[/]")
                self.write_line("")
        elif shell.tool is not None and shell.arg_index < len(shell.pending_args):
            self.write_line(text)
            self.write_line("")
            await self.collect_argument(text)
        elif shell.tool is None:
            self.write_line(f"[{MUTED}]select a tool first — type / to see available tools[/]")
            self.write_line("")
        else:
            self.write_line(text)
            self.write_line("")

    async def load_tool(self, name: str) -> None:
        shell = self.shell
        if shell.process is not None:
            self.write_line(f"[{MUTED}]a tool is running in this shell — press esc to stop it first[/]")
            self.write_line("")
            return

        module = self.tools.get(name)
        if module is None:
            self.write_line(f"[{MUTED}]no such tool: {name}[/]")
            self.write_line("")
            return
        if not hasattr(module, "build_parser"):
            self.write_line(f"[{TOOL}]{escape_markup(name)}[/] [{MUTED}]has no build_parser()[/]")
            self.write_line("")
            return

        parser = module.build_parser()
        actions = [
            action
            for action in parser._actions
            if action.option_strings and action.option_strings[0] != "-h"
        ]

        shell.tool = name
        shell.script = Path(module.__file__)
        shell.pending_args = actions
        shell.arg_index = 0
        shell.values = {}

        self._clear_screen()

        desc = getattr(module, "TOOL_DESCRIPTION", "")
        banner = f"[{TOOL}]{escape_markup(name)}[/]"
        if desc:
            banner += f" [{MUTED}]— {escape_markup(desc)}[/]"
        self.write_line(banner)
        self.write_line("")

        self.update_badge()
        if shell.pending_args:
            self.prompt_next_arg()
        else:
            await self.run_tool(shell)

    def prompt_next_arg(self) -> None:
        shell = self.shell
        if not shell.pending_args:
            return
        action = shell.pending_args[shell.arg_index]
        prompt = f"enter {action.dest}"
        if action.choices:
            prompt += f" ({'/'.join(str(c) for c in action.choices)})"
        if action.default is not None and action.default is not argparse.SUPPRESS:
            prompt += f" [{action.default}]"
        self.write_line(f"[{MUTED}]{prompt}:[/]")
        if action.help:
            self.write_line(f"[{MUTED}]{escape_markup(action.help)}[/]")
        self.write_line("")

    async def collect_argument(self, value: str) -> None:
        shell = self.shell
        action = shell.pending_args[shell.arg_index]
        value = value.strip()

        has_default = action.default is not None and action.default is not argparse.SUPPRESS
        if not value and has_default:
            value = str(action.default)

        if action.choices and value not in [str(c) for c in action.choices]:
            choices = ", ".join(str(c) for c in action.choices)
            self.write_line(f"[{MUTED}]must be one of: {choices}[/]")
            self.write_line("")
            self.prompt_next_arg()
            return

        shell.values[action.dest] = value
        shell.arg_index += 1

        if shell.arg_index < len(shell.pending_args):
            self.prompt_next_arg()
        else:
            await self.run_tool(shell)

    async def run_tool(self, shell: Shell) -> None:
        if shell.process is not None:
            self.write_line(f"[{MUTED}]a tool is already running in this shell — press esc to stop it first[/]")
            self.write_line("")
            return

        args = []
        for action in shell.pending_args:
            args.append(action.option_strings[0])
            args.append(shell.values[action.dest])

        kwargs: dict = {}
        if POSIX:
            # New session -> its own process group, so a kill reaches any
            # children the tool spawns too, not just the direct child.
            kwargs["preexec_fn"] = _limit_tool_resources
            kwargs["start_new_session"] = True

        try:
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                str(shell.script),
                *args,
                stdin=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                **kwargs,
            )
        except Exception as exc:
            self.write_line(f"[{MUTED}]failed to start {shell.tool}: {exc}[/]")
            self.write_line("")
            return

        shell.process = process
        self.update_badge()
        shell.runner_task = asyncio.create_task(self._run_and_pump(shell, process))

    async def _run_and_pump(self, shell: Shell, process: asyncio.subprocess.Process) -> None:
        """Streams a running tool's output as it arrives instead of
        buffering it all in memory until exit — that buffering is what let
        an infinite-loop tool grow without bound and look frozen while it
        produced no visible output at all."""
        watchdog = asyncio.create_task(self._watchdog(shell, process))
        total_bytes = 0
        killed_reason: str | None = None

        try:
            assert process.stdout is not None
            while True:
                try:
                    line = await process.stdout.readline()
                except (asyncio.IncompleteReadError, ValueError):
                    break
                if not line:
                    break
                total_bytes += len(line)
                text = line.decode(errors="replace").rstrip("\n")
                if text:
                    self.write_line_to(shell, f"[{RESULT}]{escape_markup(text)}[/]")
                else:
                    self.write_line_to(shell, "")
                if total_bytes > MAX_OUTPUT_BYTES:
                    killed_reason = "exceeded output limit"
                    self._kill_process(process)
                    break
        finally:
            watchdog.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await watchdog
            returncode = await process.wait()

        if shell.process is process:
            shell.process = None
        shell.runner_task = None

        if killed_reason:
            self.write_line_to(shell, f"[{MUTED}]tool killed: {killed_reason}[/]")
        elif returncode not in (0, None, -9, -15):
            self.write_line_to(shell, f"[{MUTED}]exited with code {returncode}[/]")

        self.write_line_to(shell, "")
        if shell is self.shell:
            self.update_badge()

        shell.arg_index = 0
        shell.values = {}
        if shell is self.shell:
            self.prompt_next_arg()

    async def _watchdog(self, shell: Shell, process: asyncio.subprocess.Process) -> None:
        await asyncio.sleep(MAX_TOOL_RUNTIME_SECONDS)
        self.write_line_to(
            shell, f"[{MUTED}]tool killed: exceeded {MAX_TOOL_RUNTIME_SECONDS}s runtime limit[/]"
        )
        self._kill_process(process)

    def _kill_process(self, process: asyncio.subprocess.Process) -> None:
        if process.returncode is not None:
            return
        if POSIX:
            try:
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                return
            except (ProcessLookupError, PermissionError, OSError):
                pass
        with contextlib.suppress(ProcessLookupError):
            process.kill()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "interrupt":
            self.action_interrupt()
        elif event.button.id == "copy_output":
            self.action_copy_output()
        elif event.button.id == "scan_tools":
            self.action_scan_tools()
        elif event.button.id == "quit":
            await self.action_quit()
            return
        self._focus_input()

    def action_copy_output(self) -> None:
        shell = self.shell
        text = "\n".join(Text.from_markup(line).plain for line in shell.lines)
        if not text:
            self.write_line(f"[{MUTED}]nothing to copy[/]")
            self.write_line("")
            return

        if sys.platform == "darwin":
            # OSC 52 (Textual's copy_to_clipboard) is ignored or blocked by
            # most terminals, including Terminal.app — pbcopy is the one
            # path that reliably reaches the system clipboard here.
            try:
                subprocess.run(["pbcopy"], input=text.encode(), check=True)
            except (OSError, subprocess.CalledProcessError) as exc:
                self.write_line(f"[{MUTED}]copy failed: {exc}[/]")
                self.write_line("")
                return
        else:
            self.copy_to_clipboard(text)

        self.write_line(f"[{MUTED}]output copied to clipboard[/]")
        self.write_line("")

    async def action_quit(self) -> None:
        """Stop any running tool and let its output finish draining before
        closing, instead of yanking the terminal away mid-output and
        leaving a killed process to be reaped after the app is gone. Shows
        a closing message for a couple seconds so the exit is visible
        rather than the terminal vanishing instantly."""
        if self.shell.process is not None:
            self.write_line(f"[{MUTED}]shutting down — stopping running tool...[/]")
            self._kill_process(self.shell.process)

        if self.shell.runner_task is not None:
            with contextlib.suppress(asyncio.TimeoutError):
                await asyncio.wait_for(self.shell.runner_task, timeout=5)

        self.write_line(f"[{MUTED}]closing pykaxe...[/]")
        await asyncio.sleep(2)
        self.exit()

    def action_interrupt(self) -> None:
        suggestions = self.query_one("#suggestions", OptionList)
        if suggestions.display:
            suggestions.display = False

        shell = self.shell
        if shell.process is not None:
            self._kill_process(shell.process)
            self.write_line(f"[{MUTED}]interrupted[/]")

    def action_scan_tools(self) -> None:
        self.tools = discover_tools(self.tools_dir)
        self.write_line(f"[{MUTED}]scanned {len(self.tools)} tool(s)[/]")
        self.write_line("")


    def update_badge(self) -> None:
        shell = self.shell
        badge = self.query_one("#badge", Static)
        if shell.tool:
            state = "running" if shell.process is not None else "active"
            badge.update(f"pykaxe {state} > {escape_markup(shell.tool)}")
            badge.display = True
        else:
            badge.update("")
            badge.display = False


def run() -> None:
    Pykaxe(config.ensure_tools_dir()).run()


if __name__ == "__main__":
    run()
