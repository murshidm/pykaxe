<div align="center">

<img src="https://raw.githubusercontent.com/murshidm/pykaxe/main/assets/logo.svg" alt="pykaxe" width="50">

# pykaxe

**Ask an AI for a tool. Get a TUI that runs it.**

These days it's easy to ask an AI to generate a Python script for almost
anything — but they end up scattered everywhere, and running one still means
wrestling with terminal commands. `pykaxe` brings them all together in one
place: pick one from a simple menu, fill in what it asks for, and watch it
run. No terminal commands to remember, even if you've never used one before.

[![CI](https://github.com/murshidm/pykaxe/actions/workflows/ci.yml/badge.svg)](https://github.com/murshidm/pykaxe/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/pykaxe?color=3B6EA5)](https://pypi.org/project/pykaxe/)
[![License: MIT](https://img.shields.io/badge/License-MIT-3B6EA5.svg)](LICENSE)

[Quick Start](#quick-start) · [Install](#install) · [Usage](#usage) · [Writing a tool by hand](#writing-a-tool-by-hand) · [Contributing](#contributing)

</div>

You don't write the tools yourself — you ask an AI chatbot for them in plain
English and drop what it gives you into a folder.

## Quick Start

Three things. Your AI walks you through the setup one step at a time — you're
still the one clicking, it just tells you what to click next.

### 1. Get it running

Paste this into ChatGPT, Claude, or Gemini:

> I want to install and run pykaxe on my computer. Read
> https://github.com/murshidm/pykaxe/blob/main/SETUP.md and follow its
> instructions for guiding me: ask first whether I'm on Mac or Windows, then
> give me one step at a time, waiting for me to confirm each one worked
> before moving to the next. If you can't open that link, tell me plainly
> instead of guessing at steps.

Then just follow along. It ends with pykaxe running and you knowing where your
tools folder is.

*If it says it can't open links, open [SETUP.md](SETUP.md) yourself, copy the
whole page, and paste it into the chat instead — or just
[follow it yourself](SETUP.md).*

### 2. Teach the chatbot what pykaxe is

Open [this page](https://raw.githubusercontent.com/murshidm/pykaxe/main/src/pykaxe/assets/PROMPT.md),
select all of it (`Cmd/Ctrl + A`), copy it, and **paste it as the first
message of a new chat**.

Do this once per chat, before asking for anything. Skip it and you'll get
ordinary Python back, because the word "pykaxe" means nothing to a chatbot
otherwise. To set it up permanently instead, see
[Teach your AI once](#teach-your-ai-once).

### 3. Ask for a tool

In that same chat:

> Write a pykaxe tool that reverses a string.

Save the code it gives you into your tools folder as a file ending in `.py`.
There's a knack to this in Notepad and TextEdit —
[the details are here](SETUP.md#saving-a-tool-into-that-folder), or just ask
the same chatbot to talk you through saving it.

Then open pykaxe (or, if it's already open, press `Ctrl+S` so it notices the
new file), type `/`, pick your tool, and press Enter.

That's the loop — repeat 2 and 3 for every tool you want.

## Teach your AI once

Optional — skip this if pasting the prompt each time (step 2) is working fine
for you. Most chat apps can remember it permanently instead, so "write me a
pykaxe tool that…" just works in any conversation without pasting anything
first:

- **ChatGPT** — build a [Custom GPT](https://chatgpt.com/gpts/editor) with the
  prompt as its instructions, or paste it into Settings → Personalization →
  **Custom Instructions** to apply it everywhere.
- **Claude.ai** — create a [Project](https://claude.ai/projects) and paste the
  prompt into its **Project Knowledge**.
- **Gemini** — create a [Gem](https://gemini.google.com/gems) with the prompt
  as its instructions.
- **Anything else** — look for custom instructions, a system prompt, or a
  project/space feature, and put the prompt there.

**Using an AI coding agent?** Claude Code, Cursor, Copilot and Codex CLI write
files for you, so they skip steps 2 and 3 entirely. Run `pykaxe skill` once to
teach the agent the contract permanently, then just ask:

> Create a pykaxe tool that reverses a string.

## Install

Most people should use the launcher — see [SETUP.md](SETUP.md). If you're
comfortable in a terminal:

```bash
pipx run pykaxe        # run the latest release, nothing installed permanently
pipx install pykaxe    # install it, isolated and independently upgradeable
pip install pykaxe     # install it the plain way
```

`pipx run pykaxe` is exactly what the launcher does under the hood. Both pipx
options need [pipx](https://pipx.pypa.io/) first:

```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
```

## Usage

Run `pykaxe` — or `pipx run pykaxe` if you didn't install it permanently.

On first run it silently creates `~/Documents/pykaxe/scripts` for your tools,
seeds it with a few example tools, and remembers your choice in
`~/Documents/pykaxe/config.json`. Override it for a single run with the
`PYKAXE_TOOLS_DIR` environment variable.

Type `/` to see available tools, narrow the list by typing part of a name, and
press Enter to select. Tools are listed by their `TOOL_NAME`, not their
filename. If a tool declares arguments, pykaxe prompts for each one in turn —
showing its choices/default/help when it declares them — before running it.

| Key      | Action               |
| -------- | -------------------- |
| `/`      | List / filter tools   |
| `esc`    | Interrupt running tool |
| `ctrl+y` | Copy output to clipboard |
| `ctrl+s` | Re-scan tools directory |
| `ctrl+c` | Quit                  |

| Command | What it does |
| ------- | ------------ |
| `pykaxe prompt --copy` | Copy the step 2 prompt straight to your clipboard |
| `pykaxe add script.py` | Check a script against the contract and copy it into your tools folder |
| `pykaxe skill` | Install the pykaxe skill for a coding agent |
| `pykaxe tools-dir` | Print where your tools folder is |

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

Working on pykaxe itself, not just using it? See
[CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT — see [LICENSE](LICENSE).
