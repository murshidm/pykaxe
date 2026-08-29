from textual.app import App, ComposeResult
from textual.widgets import Input, RichLog


class Pykaxe(App):
    CSS = """
    RichLog {
        border: round #2c2c2c;
    }
    Input {
        border: round #2c2c2c;
        dock: bottom;
    }
    """

    def compose(self) -> ComposeResult:
        yield RichLog()
        yield Input(placeholder="Type your message here...")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.query_one(RichLog).write(event.value)
        event.input.value = ""


if __name__ == "__main__":
    Pykaxe().run()
