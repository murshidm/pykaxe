# pykaxe

A terminal UI for discovering and running small Python CLI tools.

`pykaxe` scans a tools directory you choose for standalone Python scripts,
lets you search for them and launch them from a single prompt, and streams
their output live — with sandboxing (memory/CPU/runtime limits, output caps)
so a runaway tool can't take the terminal down with it.

You don't write the tools yourself — you ask an AI chatbot for them in plain
English and drop what it gives you into a folder.

## Quick Start

Three things. An AI does the rest, including the setup.

### 1. Get it running

Paste this into ChatGPT, Claude, or Gemini:

> I want to install and run pykaxe on my computer. The setup instructions are
> at https://github.com/murshidm/pykaxe/blob/main/SETUP.md — please read that
> page and walk me through it one step at a time, waiting for me to confirm
> each step. Ask me first whether I'm on Mac or Windows.

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

Then open pykaxe, type `/`, pick your tool, and press Enter.

That's the loop — repeat 2 and 3 for every tool you want.

## Teach your AI once

Step 2 has you paste the prompt at the start of each new chat. Most chat apps
can remember it permanently instead, so "write me a pykaxe tool that…" just
works in any conversation:

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
The version lives in `src/pykaxe/__init__.py`. For local test builds vs.
cutting an actual release (bump → tag → CI publishes to PyPI), see
[RELEASING.md](RELEASING.md).

## License

MIT — see [LICENSE](LICENSE).
