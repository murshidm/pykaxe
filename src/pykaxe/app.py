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

from pykaxe import __version__, config

try:
    import resource
except ImportError:  # Windows has no resource module
    resource = None

from textual import events
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.theme import Theme
from textual.widgets import (
    DirectoryTree,
    Footer,
    Input,
    OptionList,
    RichLog,
    Static,
)
from textual.widgets.option_list import Option
from rich.markup import escape as escape_markup
from rich.rule import Rule
from rich.text import Text

# Palette: one background, borrowed from the terminal (BG = "ansi_default"),
# not an app-owned hex fill — an earlier version of this round tried a
# solid Dracula-style background plus a separate elevated PANEL tone; that
# added more distinct background colors than the app needed and made the
# borders/Rule dividers (the app's actual structural language) compete
# with filled color blocks instead of standing out against a neutral
# field. BORDER stays a plain neutral grey for the same reason — it needs
# to read clearly against *any* terminal background, not just one specific
# hex tone. PRIMARY/ACCENT/SUCCESS/ERROR/WARNING are unaffected; those are
# foreground/text colors, not backgrounds, and terminal-transparency never
# applied to them.
FG = "#f2f2f2"
MUTED = "#8a8a8a"
BORDER = "#3a3a3a"
BG = "ansi_default"
PRIMARY = "#bd93f9"  # app/brand identity (headings), distinct from ACCENT,
# which stays reserved for "this is a tool" and nothing else
SUCCESS = "#7ee787"
ACCENT = "#f2c94c"
ERROR = "#e5534b"
WARNING = "#e5c07b"

PYKAXE_THEME = Theme(
    name="pykaxe",
    primary=PRIMARY,
    accent=ACCENT,
    foreground=FG,
    background=BG,
    surface=BG,
    panel=BG,
    success=SUCCESS,
    warning=WARNING,
    error=ERROR,
    dark=True,
)
"""Registered in Pykaxe.__init__ so built-in widgets we adopt (Footer)
pick up the same palette automatically via their own `$primary` /
`$foreground` / etc. CSS variables, instead of needing hand-written CSS
overrides for every one of them. background/surface/panel are all BG
(ansi_default) — confirmed via run_test() that Textual accepts
"ansi_default" as a Theme background without error, so there's one
background concept everywhere, not three. Widgets pykaxe defines itself
(RichLog content, #suggestions, the file picker) keep using the plain
constants above directly, same as before."""


def _alpha(hex_color: str, alpha: float) -> str:
    """Textual CSS has no `color 30%` shorthand — alpha has to be baked
    into an rgba()/hex-with-alpha value up front (confirmed against
    Textual's own <color> CSS type reference)."""
    r, g, b = int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16)
    return f"rgba({r}, {g}, {b}, {alpha})"


# Textual's own built-in themes highlight an unfocused list cursor with the
# primary color at ~30% alpha rather than a solid block (see
# block-cursor-blurred-background in textual/design.py) — ACCENT_TINT
# mirrors that same restraint for our suggestion list, using our own
# tool-identity color instead of a generic "primary".
ACCENT_TINT = _alpha(ACCENT, 0.3)

# Protection limits for running tools. Tool scripts are user-authored and
# untrusted, so every guard here lives on the app side rather than relying
# on the script to behave.
MAX_OUTPUT_LINES = 2000  # scrollback kept per shell (and in the RichLog widget)
MAX_OUTPUT_BYTES = 4 * 1024 * 1024  # auto-kill a tool that floods stdout/stderr
MAX_TOOL_MEMORY_BYTES = 256 * 1024 * 1024  # RLIMIT_AS ceiling for a tool process
MAX_TOOL_CPU_SECONDS = 120  # RLIMIT_CPU ceiling; catches tight busy-loops fast
MAX_TOOL_RUNTIME_SECONDS = 30 * 60  # wall-clock safety net for polling loops

POSIX = sys.platform != "win32"


# Semantic output helpers (DESIGN.md §"output semantics"): every pykaxe
# feedback line goes through one of these instead of an ad-hoc f-string, so
# what a message *means* (info/success/warning/error/cancelled) is decided
# once here rather than re-decided — inconsistently — at each call site.
def info(text: str) -> str:
    return f"[{MUTED}]{text}[/]"


def prompt(text: str) -> str:
    """An argument prompt ("enter text:") — what requires action next, as
    opposed to the MUTED help line that may follow it. FG + a `›` lead-in
    keeps it one clear step above `info()` without going all the way to
    bold, which would get shouty across a tool with several arguments in a
    row."""
    return f"[{FG}]› {text}[/]"


def success(text: str) -> str:
    return f"[{SUCCESS}]✓ {text}[/]"


def warning(text: str) -> str:
    return f"[{WARNING}]! {text}[/]"


def error(text: str) -> str:
    return f"[{ERROR}]× {text}[/]"


def cancelled(text: str) -> str:
    return f"[{MUTED}]cancelled — {text}[/]"


def tool_name(name: str) -> str:
    return f"[{ACCENT}]{escape_markup(name)}[/]"


def user_input(text: str) -> str:
    """What the user just typed, echoed back into the log. FG makes it read
    as a third voice distinct from pykaxe's own MUTED chrome and a tool's
    SUCCESS-colored stdout. escape_markup is required here, not decorative:
    without it, a submitted value containing "[" would be parsed as Rich
    markup instead of shown literally."""
    return f"[{FG}]{escape_markup(text)}[/]"


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
        # Set by whichever pykaxe-initiated kill site (interrupt/quit/
        # watchdog) already printed its own explanation for why the process
        # is dying, so _run_and_pump's completion tail doesn't also print a
        # second, redundant line for the same termination.
        self.kill_announced: bool = False


class FilePickerScreen(ModalScreen[Path | None]):
    """Modal file browser pushed with ctrl+o while pykaxe is prompting for a
    Path-typed argument. Dismisses with the chosen path, or None on
    escape/cancel — the caller decides what to do with the result, so this
    screen never touches the Input or the shell itself.

    No escape binding here: Pykaxe's own "escape" binding is priority=True,
    which Textual always checks before a pushed screen ever sees the key —
    so escape is handled centrally in Pykaxe.action_interrupt() instead."""

    BINDINGS = [
        Binding("backspace", "go_up", "Up a directory"),
    ]

    CSS = f"""
    FilePickerScreen {{
        align: center middle;
    }}
    #picker {{
        width: 80%;
        height: 80%;
        background: {BG};
        border: round {FG};
    }}
    #picker-title {{
        height: 1;
        padding: 0 1;
        background: {BG};
        color: {MUTED};
    }}
    FilePickerScreen DirectoryTree {{
        background: {BG};
    }}
    """

    def __init__(self, start_dir: Path) -> None:
        super().__init__()
        self.start_dir = start_dir

    def compose(self) -> ComposeResult:
        with Vertical(id="picker"):
            yield Static(self._title_text(), id="picker-title")
            yield DirectoryTree(str(self.start_dir), id="picker-tree")

    def _title_text(self) -> str:
        return f"{self.start_dir} — esc to cancel, backspace to go up"

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        self.dismiss(event.path)

    def action_go_up(self) -> None:
        parent = self.start_dir.parent
        if parent == self.start_dir:
            return  # already at the filesystem root
        self.start_dir = parent
        self.query_one("#picker-tree", DirectoryTree).path = str(parent)
        self.query_one("#picker-title", Static).update(self._title_text())


class Pykaxe(App):
    # pykaxe doesn't design around Textual's generic command palette (theme
    # switching, its own screenshot action, etc.) — it isn't part of the
    # tested feature set documented here, so it stays off rather than
    # exposing an unreviewed surface behind an undocumented ctrl+p.
    ENABLE_COMMAND_PALETTE = False

    CSS = f"""
    Screen {{
        background: {BG};
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
        scrollbar-color-active: {FG};
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
        border: round {FG};
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
        scrollbar-color-active: {FG};
    }}
    OptionList {{
        background: {BG};
    }}
    OptionList > .option-list--option-highlighted {{
        background: {ACCENT_TINT};
        text-style: none;
    }}
    """

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", priority=True, tooltip="Stop any running tool and exit"),
        Binding("ctrl+y", "copy_output", "Copy", tooltip="Copy the visible output to your clipboard"),
        Binding("ctrl+s", "scan_tools", "Scan", tooltip="Re-scan the tools directory for new tools"),
        Binding(
            "ctrl+o",
            "browse_file",
            "Browse file",
            show=False,  # contextual (only while collecting a Path argument), not a standing shortcut
            tooltip="Browse for a file",
        ),
        # priority=True: this must win over whatever widget has focus (e.g.
        # the Input) so a runaway tool can always be killed immediately.
        # key_display: Footer would otherwise print the raw key id
        # ("escape") instead of the short form everyone actually calls it.
        Binding(
            "escape",
            "interrupt",
            "Interrupt",
            key_display="esc",
            priority=True,
            tooltip="Stop the running tool, or cancel argument entry",
        ),
    ]

    def __init__(self, tools_dir: Path) -> None:
        super().__init__(ansi_color=True)
        self.tools_dir = tools_dir
        self.shell = Shell()
        self.tools: dict[str, ModuleType] = {}
        self.register_theme(PYKAXE_THEME)
        self.theme = "pykaxe"

    def compose(self) -> ComposeResult:
        yield RichLog(markup=True, wrap=True, max_lines=MAX_OUTPUT_LINES)
        with Vertical(id="bottom"):
            yield OptionList(id="suggestions")
            yield Input(placeholder="Type / to load a tool...")
            yield Footer(show_command_palette=False)

    def on_mount(self) -> None:
        self.tools = discover_tools(self.tools_dir)
        self._show_welcome()
        self.update_input_placeholder()
        self._focus_input()

    def _clear_screen(self) -> None:
        self.shell.lines.clear()
        self.query_one(RichLog).clear()

    def _show_welcome(self) -> None:
        title = Text()
        title.append("pykaxe", style=f"bold {PRIMARY}")
        title.append(f" v{__version__}", style=MUTED)
        self._write_heading(title, f"pykaxe v{__version__}")
        self.write_line("")
        if self.tools:
            self.write_line(info("available tools"))
            width = max(len(name) for name in self.tools)
            for name in sorted(self.tools):
                desc = getattr(self.tools[name], "TOOL_DESCRIPTION", "")
                line = f"  {tool_name('/' + name)}"
                if desc:
                    line += f"{' ' * (width - len(name))}  [{MUTED}]{escape_markup(desc)}[/]"
                self.write_line(line)
            self.write_line("")
        else:
            self.write_line(info(f"no tools found in {escape_markup(str(self.tools_dir))}"))
            self.write_line(info("drop a .py tool in there, then press ctrl+s to re-scan"))
            self.write_line("")
        self.write_line(info("type / to load a tool"))
        self.write_line("")

    def _focus_input(self) -> None:
        self.query_one(Input).focus()

    def _modal_active(self) -> bool:
        """True while a screen (e.g. the file picker) is pushed on top of
        the main one. Every App-level click handler and non-priority
        binding below assumes the base screen's widgets (Input, RichLog,
        #suggestions) exist — they don't on a modal, so each of those must
        stand down while one is active rather than crash with NoMatches."""
        return len(self.screen_stack) > 1

    def on_click(self, event: events.Click) -> None:
        # The Input is the only thing worth typing into — whatever else got
        # clicked (the log, a suggestion, the interrupt button) has already
        # handled the click itself by the time this fires, so just make
        # sure a cursor is always waiting in the Input afterward.
        if self._modal_active():
            return
        self._focus_input()

    def write_line_to(self, shell: Shell, text: str) -> None:
        shell.lines.append(text)
        if shell is self.shell:
            self.query_one(RichLog).write(text)

    def write_line(self, text: str) -> None:
        self.write_line_to(self.shell, text)

    def _write_heading(self, title: Text, copy_text: str) -> None:
        """A quiet Rule anchors each new top-level context — the welcome
        banner, or a freshly loaded tool's banner — the same way the rest
        of the app marks "what state it's in" with structure (a border)
        rather than color alone. `style=BORDER` keeps the rule line
        itself quiet/structural; the colored `title` Text carries the
        actual emphasis, same division of labor as `§5 Borders` elsewhere.
        Used sparingly — only at genuine context transitions — so it stays
        a signal rather than becoming wallpaper. This is the only "what
        state is the app in" indicator once a tool loads — no separate
        badge widget anymore, so the tool name/description shown here and
        the running-state placeholder text (`update_input_placeholder`)
        are the full story.

        RichLog.write() accepts any Rich renderable, not just markup
        strings, so this bypasses write_line_to entirely — a Rule can't be
        expressed as a markup string. shell.lines still gets a plain-text
        `copy_text` so ctrl+y keeps working; the decorative dashes aren't
        worth reproducing in copied text, only the title's content is."""
        self.shell.lines.append(copy_text)
        self.query_one(RichLog).write(Rule(title=title, style=BORDER, align="left"))

    def _awaiting_argument(self) -> bool:
        shell = self.shell
        return shell.tool is not None and shell.arg_index < len(shell.pending_args)

    def on_input_changed(self, event: Input.Changed) -> None:
        suggestions = self.query_one("#suggestions", OptionList)
        if self._awaiting_argument() or not event.value.startswith("/"):
            # Mid argument-collection, "/" has no special meaning — it's
            # just a character an absolute path can start with — so the
            # tool-picker dropdown must stay out of the way here.
            suggestions.display = False
            return

        matches = fuzzy_filter(event.value[1:], list(self.tools.keys()))
        suggestions.clear_options()
        if not matches:
            suggestions.display = False
            return
        for name in matches[:8]:
            desc = getattr(self.tools[name], "TOOL_DESCRIPTION", "")
            label = tool_name(name)
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
        if self._awaiting_argument():
            self.write_line(user_input(text))
            self.write_line("")
            await self.collect_argument(text)
        elif text.startswith("/"):
            query = text[1:].strip()
            matches = fuzzy_filter(query, list(self.tools.keys()))
            if matches:
                await self.load_tool(matches[0])
            else:
                self.write_line(user_input(text))
                self.write_line(error(f"no such tool: {query}"))
                self.write_line("")
        elif shell.tool is None:
            self.write_line(info("select a tool first — type / to see available tools"))
            self.write_line("")
        else:
            self.write_line(user_input(text))
            self.write_line("")

    async def load_tool(self, name: str) -> None:
        shell = self.shell
        if shell.process is not None:
            self.write_line(warning("a tool is running in this shell — press esc to stop it first"))
            self.write_line("")
            return

        module = self.tools.get(name)
        if module is None:
            self.write_line(error(f"no such tool: {name}"))
            self.write_line("")
            return
        if not hasattr(module, "build_parser"):
            self.write_line(error(f"{name} has no build_parser()"))
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
        title = Text()
        title.append(name, style=f"bold {ACCENT}")
        copy_text = name
        if desc:
            title.append(f" — {desc}", style=MUTED)
            copy_text += f" — {desc}"
        self._write_heading(title, copy_text)
        self.write_line("")

        if shell.pending_args:
            self.prompt_next_arg()
        else:
            await self.run_tool(shell)

    def _arg_prompt_text(self, action: argparse.Action) -> str:
        prompt = f"enter {action.dest}"
        if action.choices:
            prompt += f" ({'/'.join(str(c) for c in action.choices)})"
        if action.default is not None and action.default is not argparse.SUPPRESS:
            prompt += f" [{action.default}]"
        if action.type is Path:
            prompt += " (ctrl+o to browse)"
        return prompt

    def update_input_placeholder(self) -> None:
        """Keeps the Input's placeholder tied to what typing into it will
        actually do right now, instead of a static hint that's wrong
        whenever a tool is mid argument-collection or running."""
        shell = self.shell
        input_widget = self.query_one(Input)
        if shell.process is not None:
            input_widget.placeholder = f"{shell.tool} is running — press esc to stop..."
        elif shell.tool is not None and shell.arg_index < len(shell.pending_args):
            action = shell.pending_args[shell.arg_index]
            input_widget.placeholder = self._arg_prompt_text(action) + "..."
        else:
            input_widget.placeholder = "Type / to load a tool..."

    def prompt_next_arg(self) -> None:
        self.update_input_placeholder()
        shell = self.shell
        if not shell.pending_args:
            return
        action = shell.pending_args[shell.arg_index]
        arg_prompt = escape_markup(self._arg_prompt_text(action))
        self.write_line(prompt(f"{arg_prompt}:"))
        if action.help:
            self.write_line(info(escape_markup(action.help)))
        self.write_line("")

    async def collect_argument(self, value: str) -> None:
        shell = self.shell
        action = shell.pending_args[shell.arg_index]
        value = value.strip()

        has_default = action.default is not None and action.default is not argparse.SUPPRESS
        if not value and has_default:
            value = str(action.default)

        if not value:
            self.write_line(error(f"{action.dest} is required — enter a value"))
            self.write_line("")
            self.prompt_next_arg()
            return

        if action.choices and value not in [str(c) for c in action.choices]:
            choices = ", ".join(str(c) for c in action.choices)
            self.write_line(error(f"must be one of: {choices}"))
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
            self.write_line(warning("a tool is already running in this shell — press esc to stop it first"))
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
            self.write_line(error(f"failed to start {shell.tool} — {exc}"))
            self.write_line("")
            return

        shell.process = process
        self.update_input_placeholder()
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
                    self.write_line_to(shell, f"[{SUCCESS}]{escape_markup(text)}[/]")
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
            self.write_line_to(shell, error(f"{shell.tool} killed — {killed_reason}"))
        elif shell.kill_announced:
            pass  # interrupt/quit/watchdog already explained this termination
        elif returncode not in (0, None):
            self.write_line_to(shell, error(f"{shell.tool} failed — exit {returncode}"))
        elif returncode == 0:
            self.write_line_to(shell, success(f"{shell.tool} finished"))
        shell.kill_announced = False

        self.write_line_to(shell, "")

        shell.arg_index = 0
        shell.values = {}
        if shell is self.shell:
            self.prompt_next_arg()

    async def _watchdog(self, shell: Shell, process: asyncio.subprocess.Process) -> None:
        await asyncio.sleep(MAX_TOOL_RUNTIME_SECONDS)
        self.write_line_to(
            shell, error(f"{shell.tool} killed — exceeded {MAX_TOOL_RUNTIME_SECONDS}s runtime limit")
        )
        shell.kill_announced = True
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

    def action_copy_output(self) -> None:
        if self._modal_active():
            return
        shell = self.shell
        text = "\n".join(Text.from_markup(line).plain for line in shell.lines)
        if not text:
            self.write_line(info("nothing to copy"))
            self.write_line("")
            return

        if sys.platform == "darwin":
            # OSC 52 (Textual's copy_to_clipboard) is ignored or blocked by
            # most terminals, including Terminal.app — pbcopy is the one
            # path that reliably reaches the system clipboard here.
            try:
                subprocess.run(["pbcopy"], input=text.encode(), check=True)
            except (OSError, subprocess.CalledProcessError) as exc:
                self.write_line(error(f"copy failed — {exc}"))
                self.write_line("")
                return
        else:
            self.copy_to_clipboard(text)

        self.write_line(success(f"copied — {len(shell.lines)} lines"))
        self.write_line("")

    async def action_quit(self) -> None:
        """Stop any running tool and let its output finish draining before
        closing, instead of yanking the terminal away mid-output and
        leaving a killed process to be reaped after the app is gone. Shows
        a closing message for a couple seconds so the exit is visible
        rather than the terminal vanishing instantly."""
        if self.shell.process is not None:
            self.write_line(info("shutting down — stopping running tool..."))
            self.shell.kill_announced = True
            self._kill_process(self.shell.process)

        if self.shell.runner_task is not None:
            with contextlib.suppress(asyncio.TimeoutError):
                await asyncio.wait_for(self.shell.runner_task, timeout=5)

        self.write_line(info("closing pykaxe..."))
        await asyncio.sleep(1)
        self.exit()

    def action_interrupt(self) -> None:
        # This binding is priority=True, so it's checked before a pushed
        # screen (e.g. the file picker) ever sees the key — closing that
        # screen has to happen here rather than via its own binding, which
        # would never be reached.
        if self._modal_active():
            self.screen.dismiss(None)
            return

        suggestions = self.query_one("#suggestions", OptionList)
        if suggestions.display:
            suggestions.display = False

        shell = self.shell
        if shell.process is not None:
            shell.kill_announced = True
            self._kill_process(shell.process)
            self.write_line(cancelled(f"{shell.tool} (terminated)"))
        elif self._awaiting_argument():
            cancelled_tool = shell.tool
            shell.tool = None
            shell.script = None
            shell.pending_args = []
            shell.arg_index = 0
            shell.values = {}
            self._clear_screen()
            self._show_welcome()
            self.write_line(cancelled(cancelled_tool))
            self.write_line("")
            self.update_input_placeholder()

    def action_scan_tools(self) -> None:
        if self._modal_active():
            return
        self.tools = discover_tools(self.tools_dir)
        self.write_line(info(f"scanned {len(self.tools)} tool(s)"))
        self.write_line("")

    def action_browse_file(self) -> None:
        if self._modal_active():
            return
        shell = self.shell
        if shell.tool is None or shell.arg_index >= len(shell.pending_args):
            return
        action = shell.pending_args[shell.arg_index]
        if action.type is not Path:
            return
        documents = Path.home() / "Documents"
        start_dir = documents if documents.is_dir() else Path.home()
        self.push_screen(FilePickerScreen(start_dir), self._on_file_picked)

    def _on_file_picked(self, path: Path | None) -> None:
        if path is None:
            return
        input_widget = self.query_one(Input)
        input_widget.value = str(path)
        input_widget.focus()


def run() -> None:
    Pykaxe(config.resolve_tools_dir()).run()


if __name__ == "__main__":
    run()
