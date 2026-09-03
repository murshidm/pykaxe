# pykaxe

A terminal UI for discovering and running small Python CLI tools.

`pykaxe` scans a tools directory you choose for standalone Python scripts,
lets you search for them and launch them from a single prompt, and streams
their output live — with sandboxing (memory/CPU/runtime limits, output caps)
so a runaway tool can't take the terminal down with it.

## Quick Start (for beginners)

New to Python? Follow these 7 steps.

### 1. Install Python

**Windows:**

1. Go to [python.org/downloads](https://www.python.org/downloads/) and click the yellow "Download Python" button.
2. Open the downloaded file. **Check the box that says "Add python.exe to PATH"**, then click "Install Now".

**Mac:**

1. Go to [python.org/downloads](https://www.python.org/downloads/) and click the yellow "Download Python" button.
2. Open the downloaded file and follow the installer steps.

### 2. Open the terminal

The terminal is a plain window where you type commands instead of clicking
buttons. You'll need it for the next few steps.

**Windows:**

1. Click the **Start** button (bottom-left corner of your screen).
2. Type `Command Prompt`.
3. Click on "Command Prompt" when it shows up in the results.

**Mac:**

1. Press `Cmd + Space` to open Spotlight search.
2. Type `Terminal`.
3. Press Enter.

A plain window with text will open. Keep it open for the next steps — you'll
type each command into it and press Enter.

### 3. Check that Python installed correctly

In the terminal window, type this and press Enter:

```bash
python3 --version
```

If you see a version number like `Python 3.12.0`, it worked. If you get an
error, go back to Step 1 and reinstall Python.

### 4. Make sure pip is ready

pip is the tool that installs Python packages for you — it comes bundled
with Python, so you likely already have it. In the same terminal window,
type this and press Enter:

```bash
pip3 --version
```

If you see a version number, you're ready for the next step.

### 5. Download the pykaxe launcher

Download [`pykaxe.command`](launchers/pykaxe.command) if you're on a Mac, or
[`pykaxe.bat`](launchers/pykaxe.bat) if you're on Windows. Save it anywhere
you'll find it again, like your Desktop.

### 6. Double-click it

**Mac:** double-click `pykaxe.command`. The first time, macOS may warn that
it's "from an unidentified developer" — right-click it, choose **Open**, and
confirm. You only need to do that once.

**Windows:** double-click `pykaxe.bat`.

A terminal window opens on its own. The first time, it may tell you it needs
[pipx](https://pipx.pypa.io/) first and show you two commands to run — do
that once, then double-click pykaxe again and it'll work from then on. It
never installs pykaxe itself; it always fetches the latest version fresh.

The very first time it actually starts, it asks where you want to keep your tools:

```
Where should pykaxe store your tools? [~/.pykaxe/tools]:
```

Press Enter to accept the default. pykaxe creates that folder and remembers
it — this is the one and only folder where your scripts need to live. Find
it in your file browser so you can save things there later:

- **Windows:** open File Explorer, and paste the path into the address bar.
- **Mac:** open Finder, press `Cmd+Shift+G`, and paste the path in.

Once you know where that folder is, you barely need the terminal again — you
only double-click pykaxe to run your tools. Everything else (getting
code from an AI and saving it) happens in your file browser.

Press `ctrl+c` to close pykaxe for now — you'll open it again once you have a
tool to run.

### 7. Use it with an AI tool

There are two kinds of AI tools you might use, and they work a little
differently with pykaxe.

**AI chatbots** — like ChatGPT, Claude.ai, or Gemini. These live in a website. They can't touch files on your computer, so they just give you code as text in the chat.

1. Ask it:

   > Write a pykaxe tool that reverses a string.

2. Copy the code it gives you.
3. Save it as a new file **directly inside your pykaxe tools folder** (the
   one from Step 6), e.g. `reverse.py`.

That's it — no terminal commands needed to add it. It'll show up next time
you open pykaxe.

**AI coding agents** — like Claude Code, Cursor, GitHub Copilot, or Codex CLI. These run inside your code editor or terminal and can create and save files for you directly. This makes things simpler — no copying, pasting, or saving needed.

1. Just ask it:

   > Create a pykaxe tool that reverses a string.

2. It writes the file straight into your tools folder. Done — no extra steps.

**In short:** with a chatbot, you're the one moving the code from chat to
file — but as long as you save it in the right folder, that's the only
manual step. With a coding agent, it does even that for you.

### Example: building a tool with the ChatGPT app

Say you're an office worker who keeps getting long email threads pasted into a
document, and you want to quickly pull out just the email addresses. Here's
the whole pykaxe workflow, start to finish, using the ChatGPT app:

1. Open the ChatGPT app and type this prompt:

   > Write a pykaxe tool that reads a block of pasted text and prints out just
   > the email addresses found in it.

2. ChatGPT replies with a code block. Copy it.
3. Paste it into a plain text editor (like Notepad or TextEdit) and save the
   file as `extract-emails.py` **inside your pykaxe tools folder** (see
   Step 6 if you haven't found it yet).
4. Double-click pykaxe (the launcher from Step 5 above).

5. Type `/`, find `extract-emails` in the list, and press Enter.
6. Paste the block of text with the email thread when pykaxe asks for input,
   and press Enter.

pykaxe runs the tool and prints out just the email addresses. From now on,
that tool is saved — next time you need it, just open pykaxe, type `/`, and
select it. No need to go back to ChatGPT, and no terminal commands beyond
opening pykaxe itself.

## Install

**Easiest — double-click a launcher, no terminal typing:**

Download [`pykaxe.command`](launchers/pykaxe.command) (macOS) or
[`pykaxe.bat`](launchers/pykaxe.bat) (Windows) and double-click it. It opens
a terminal for you, checks that Python and [pipx](https://pipx.pypa.io/) are
in place (and tells you exactly what to type if not), then runs pykaxe.
Nothing gets permanently installed — it always fetches the latest release
from PyPI. See the [Quick Start](#quick-start-for-beginners) above for the
full walkthrough.

**Comfortable with a terminal:**

```bash
pipx run pykaxe
```

Same thing without the launcher file: runs the latest PyPI release in a
throwaway environment every time. Requires [pipx](https://pipx.pypa.io/)
already installed:

```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
```

**Developers, or if you want `pykaxe` permanently on your PATH:**

```bash
pip install pykaxe
# or, kept isolated and independently upgradeable:
pipx install pykaxe
```

## Usage

If you installed with `pip install` / `pipx install`, run:

```bash
pykaxe
```

Otherwise (double-click launcher, or ad-hoc `pipx run`), the same commands
below work with `pipx run pykaxe` in place of `pykaxe` — e.g. `pipx run
pykaxe prompt --copy`.

The first time you run it, pykaxe asks where to keep your tools:

```
Where should pykaxe store your tools? [~/.pykaxe/tools]:
```

Press Enter to accept the default or type a different path. It creates that
folder, seeds it with a few example tools, and remembers your choice in
`~/.pykaxe/config.json` — you won't be asked again. Override it for a single
run with the `PYKAXE_TOOLS_DIR` environment variable.

Type `/` to see available tools, narrow the list by typing part of a name, and
press Enter to select. If a tool declares arguments, pykaxe prompts for each
one in turn — showing its choices/default/help when it declares them —
before running it.

| Key      | Action               |
| -------- | -------------------- |
| `/`      | List / filter tools   |
| `esc`    | Interrupt running tool |
| `ctrl+y` | Copy output to clipboard |
| `ctrl+s` | Re-scan tools directory |
| `ctrl+c` | Quit                  |

## Getting an AI to write a tool

```bash
pykaxe prompt --copy
```

copies a short prompt to your clipboard that explains the tool contract
below. Paste it into ChatGPT or Claude.ai once, then ask for tools in plain
language:

> Generate a pykaxe script to convert Celsius to Fahrenheit.

Save what it gives you as a `.py` file and run:

```bash
pykaxe add path/to/the-script.py
```

which checks it against the contract and copies it into your tools folder —
it shows up next time you type `/`.

If you're using a coding agent with filesystem access (e.g. [Claude
Code](https://claude.com/claude-code)), run `pykaxe skill` once to install a
skill that writes tools directly into your tools folder — no `pykaxe add`
step needed. Just ask it directly:

> Create a pykaxe tool that reverses a string.

## Writing a tool by hand

A tool is a Python script placed in your configured tools folder (see
`pykaxe tools-dir`) that exposes this contract:

```python
import argparse
import sys

TOOL_NAME = "my-tool"
TOOL_DESCRIPTION = "One-line description shown in the tool list."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=TOOL_NAME, description=TOOL_DESCRIPTION)
    parser.add_argument("--text", required=True, help="Text to process.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    print(f"you said: {args.text}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Each tool runs as its own subprocess (`python <script> --arg value ...`), so
it must be runnable standalone and communicate purely through stdout/stderr
and its exit code. Drop it straight into your tools folder, or validate it
first with `pykaxe add path/to/script.py`.

## Contributing

1. Fork the repo and create a virtualenv.
2. Install in editable mode with dev dependencies:

   ```bash
   make dev
   ```

3. Add or edit a bundled example tool under `src/pykaxe/examples/`, or make
   changes to the app in `src/pykaxe/app.py`.
4. Run the tests and linter:

   ```bash
   make test
   make lint
   ```

5. Open a pull request.

## Building & releasing

This project uses [hatchling](https://hatch.pypa.io/) as its build backend.
The version lives in `src/pykaxe/__init__.py`.

```bash
make build      # bumps the patch version, then builds sdist + wheel into dist/
make publish    # builds, then uploads dist/* to PyPI via twine
```

To bump a minor or major version instead of a patch:

```bash
make bump-minor
make bump-major
```

## License

MIT — see [LICENSE](LICENSE).
