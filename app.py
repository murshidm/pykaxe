from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Input, RichLog, Static

WHITE = "#f2f2f2"
MUTED = "#8a8a8a"
BORDER = "#2c2c2c"

SHORTCUTS = (
    f"[{WHITE}]ctrl+q[/] [{MUTED}]quit[/]   "
    f"[{WHITE}]ctrl+n[/] [{MUTED}]new window[/]   "
    f"[{WHITE}]tab[/] [{MUTED}]cycle[/]"
)


class StatusBar(Horizontal):
    def compose(self) -> ComposeResult:
        yield Button("esc interrupt", id="interrupt")
        yield Static("", id="winlabel")
        yield Static(SHORTCUTS, id="shortcuts")


class Pykaxe(App):
    CSS = f"""
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
    #winlabel {{
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
        Binding("tab", "cycle_window", "Cycle", priority=True),
        Binding("ctrl+n", "new_window", "New"),
        Binding("escape", "interrupt", "Interrupt"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.buffers: list[list[str]] = [[]]
        self.current = 0

    def compose(self) -> ComposeResult:
        yield RichLog()
        with Vertical(id="bottom"):
            yield Input(placeholder="Type your message here...")
            yield StatusBar()

    def on_mount(self) -> None:
        self.refresh_content()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.buffers[self.current].append(event.value)
        self.query_one(RichLog).write(event.value)
        event.input.value = ""

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "interrupt":
            self.action_interrupt()

    def action_new_window(self) -> None:
        self.buffers.append([])
        self.current = len(self.buffers) - 1
        self.refresh_content()

    def action_cycle_window(self) -> None:
        if len(self.buffers) > 1:
            self.current = (self.current + 1) % len(self.buffers)
            self.refresh_content()

    def action_interrupt(self) -> None:
        pass

    def refresh_content(self) -> None:
        log = self.query_one(RichLog)
        log.clear()
        for line in self.buffers[self.current]:
            log.write(line)
        self.query_one("#winlabel", Static).update(
            f"window {self.current + 1}/{len(self.buffers)}"
        )


if __name__ == "__main__":
    Pykaxe().run()
