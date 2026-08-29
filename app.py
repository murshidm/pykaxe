import asyncio
import importlib.util
import sys
from pathlib import Path
from types import ModuleType

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Input, RichLog, Static

WHITE = "#f2f2f2"
MUTED = "#8a8a8a"
BORDER = "#2c2c2c"

TOOLS_DIR = Path(__file__).resolve().parent / "tools"

SHORTCUTS = (
    f"[{WHITE}]ctrl+q[/] [{MUTED}]quit[/]   "
    f"[{WHITE}]ctrl+n[/] [{MUTED}]new shell[/]   "
    f"[{WHITE}]tab[/] [{MUTED}]cycle shell[/]"
)


def discover_tools() -> dict[str, ModuleType]:
    tools: dict[str, ModuleType] = {}
    if not TOOLS_DIR.is_dir():
        return tools
    for script in TOOLS_DIR.glob("*.py"):
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


class Shell:
    def __init__(self) -> None:
        self.lines: list[str] = []
        self.tool: str | None = None
        self.script: Path | None = None
        self.pending_args: list = []
        self.arg_index: int = 0
        self.values: dict[str, str] = {}


class StatusBar(Horizontal):
    def compose(self) -> ComposeResult:
        yield Button("esc interrupt", id="interrupt")
        yield Static("", id="shelllabel")
        yield Static(SHORTCUTS, id="shortcuts")


class Pykaxe(App):
    CSS = f"""
    #badge {{
        height: 1;
        content-align: right middle;
        padding: 0 1;
    }}
    RichLog {{
        border: round {BORDER};
    }}
    #bottom {{
        dock: bottom;
        height: auto;
    }}
    Input {{
        border: round {BORDER};
    }}
    StatusBar {{
        height: 1;
        padding: 0 1;
    }}
    #interrupt {{
        min-width: 0;
        height: 1;
        border: none;
    }}
    #shelllabel {{
        width: 1fr;
        content-align: center middle;
    }}
    #shortcuts {{
        width: auto;
        content-align: right middle;
    }}
    """

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("tab", "cycle_shell", "Cycle shell", priority=True),
        Binding("ctrl+n", "new_shell", "New shell"),
        Binding("escape", "interrupt", "Interrupt"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.shells: list[Shell] = [Shell()]
        self.current = 0
        self.process: asyncio.subprocess.Process | None = None

    def compose(self) -> ComposeResult:
        yield Static("", id="badge")
        yield RichLog(markup=True, wrap=True)
        with Vertical(id="bottom"):
            yield Input(placeholder="Type your message here...")
            yield StatusBar()

    def on_mount(self) -> None:
        self.refresh_content()

    def write_line(self, text: str) -> None:
        self.shells[self.current].lines.append(text)
        self.query_one(RichLog).write(text)

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value
        event.input.value = ""
        self.write_line(text)

        shell = self.shells[self.current]
        if text.startswith("/"):
            await self.load_tool(text[1:].strip())
        elif shell.tool is not None and shell.arg_index < len(shell.pending_args):
            await self.collect_argument(text)

    async def load_tool(self, name: str) -> None:
        module = discover_tools().get(name)
        if module is None:
            self.write_line(f"[{MUTED}]no such tool: {name}[/]")
            return
        if not hasattr(module, "build_parser"):
            self.write_line(f"[{MUTED}]{name} has no build_parser()[/]")
            return

        parser = module.build_parser()
        actions = [
            action
            for action in parser._actions
            if action.option_strings and action.option_strings[0] != "-h"
        ]

        shell = self.shells[self.current]
        shell.tool = name
        shell.script = Path(module.__file__)
        shell.pending_args = actions
        shell.arg_index = 0
        shell.values = {}

        self.update_badge()
        self.prompt_next_arg()

    def prompt_next_arg(self) -> None:
        shell = self.shells[self.current]
        action = shell.pending_args[shell.arg_index]
        self.write_line(f"enter {action.dest}")

    async def collect_argument(self, value: str) -> None:
        shell = self.shells[self.current]
        action = shell.pending_args[shell.arg_index]
        shell.values[action.dest] = value
        shell.arg_index += 1

        if shell.arg_index < len(shell.pending_args):
            self.prompt_next_arg()
        else:
            await self.run_tool(shell)

    async def run_tool(self, shell: Shell) -> None:
        args = []
        for action in shell.pending_args:
            args.append(action.option_strings[0])
            args.append(shell.values[action.dest])

        self.process = await asyncio.create_subprocess_exec(
            sys.executable,
            str(shell.script),
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await self.process.communicate()
        killed = self.process is None
        self.process = None

        if killed:
            return
        if stdout:
            self.write_line(stdout.decode().rstrip())
        if stderr:
            self.write_line(f"[{MUTED}]{stderr.decode().rstrip()}[/]")

        shell.arg_index = 0
        shell.values = {}
        self.prompt_next_arg()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "interrupt":
            self.action_interrupt()

    def action_new_shell(self) -> None:
        self.shells.append(Shell())
        self.current = len(self.shells) - 1
        self.refresh_content()

    def action_cycle_shell(self) -> None:
        if len(self.shells) > 1:
            self.current = (self.current + 1) % len(self.shells)
            self.refresh_content()

    def action_interrupt(self) -> None:
        if self.process is not None:
            self.process.kill()
            self.process = None
            self.write_line(f"[{MUTED}]interrupted[/]")

    def update_badge(self) -> None:
        shell = self.shells[self.current]
        badge = self.query_one("#badge", Static)
        if shell.tool:
            badge.update(f"[{WHITE} on {BORDER}] {shell.tool} [/]")
        else:
            badge.update("")

    def refresh_content(self) -> None:
        log = self.query_one(RichLog)
        log.clear()
        for line in self.shells[self.current].lines:
            log.write(line)
        self.query_one("#shelllabel", Static).update(
            f"shell {self.current + 1}/{len(self.shells)}"
        )
        self.update_badge()


if __name__ == "__main__":
    Pykaxe().run()
