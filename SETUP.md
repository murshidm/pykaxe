# Setting up pykaxe

Detailed setup, for when you'd rather read it yourself than be walked through
it — see the [Quick Start](README.md#quick-start) for the AI-guided version.

> **If you are an AI assistant helping someone with this:** ask whether they're
> on Mac or Windows first, then give them only the steps for that system, one
> at a time, waiting for them to confirm before moving on. They are likely a
> beginner — don't assume they know what a terminal is, and don't give them
> steps for the other operating system.

## 1. Install Python

pykaxe is a Python program, so the computer needs Python first.

Go to [python.org/downloads](https://www.python.org/downloads/), click the big
yellow **Download Python** button, and open the file it downloads (it'll be in
the **Downloads** folder).

- **Windows:** on the first installer screen, **tick the box at the bottom
  that says "Add python.exe to PATH"**, then click **Install Now**. That box
  is easy to miss and pykaxe won't start without it.
- **Mac:** click **Continue** / **Agree** / **Install**. It may ask for your
  Mac password.

Nothing new appears on the desktop afterwards and there's no app to open.
That's normal — Python is something other programs use, not a program you open.

## 2. Download the launcher

The launcher is a small file that starts pykaxe for you, so you never have to
type commands.

- **Mac:** [pykaxe.command](https://github.com/murshidm/pykaxe/blob/main/launchers/pykaxe.command)
- **Windows:** [pykaxe.bat](https://github.com/murshidm/pykaxe/blob/main/launchers/pykaxe.bat)

Clicking the link shows the file's contents on a web page — it doesn't
download it. To download it, click the **download icon (⬇)** near the
top-right of that page. It saves to **Downloads**; drag it to the **Desktop**.

**Windows:** the browser may warn that this kind of file "can harm your
computer" and hide it behind a **⋯** or **Keep** button. Choose **Keep**.

**Mac, one time only:** macOS strips the "allowed to run" flag from anything
downloaded from the web, so double-clicking would just say *permission
denied*. To fix it permanently:

1. Press `Cmd + Space`, type `Terminal`, press Enter.
2. Type `chmod +x ` — including the trailing space — but **don't press Enter**.
3. Drag `pykaxe.command` from the Desktop into that window. It fills in the
   file's location for you.
4. Press Enter. No output means it worked. Close the window.

## 3. Double-click the launcher

**Mac, first time only:** macOS may say the file is "from an unidentified
developer" and refuse to open it. Right-click the file instead, choose
**Open**, then click **Open** in the box that appears. You only confirm once.

A plain text window opens by itself and pykaxe starts. **The first run can
take a minute or two** with nothing visibly happening while it downloads
pykaxe — that's normal, don't close it.

On first run it silently creates a tools folder for you — no prompt, nothing
to confirm — and seeds it with a few example tools. See
[Find your tools folder](#4-find-your-tools-folder) for where that is.

**Check it works** — a few example tools ship with pykaxe:

1. Type `/` — a list of tools appears.
2. Arrow down to `word-count`, press Enter.
3. It asks for the text to count. Type a sentence, press Enter.

You should see the word count printed back.

To close pykaxe, press `Ctrl + C` — the **Control** key, not Command, even on
a Mac.

## 4. Find your tools folder

This is the one and only place your tools live:

- **Mac:** open Finder, press `Cmd + Shift + G`, paste
  `~/Documents/pykaxe/scripts`, press Enter. Drag the folder into Finder's
  sidebar so it's one click away next time.
- **Windows:** open File Explorer, click the address bar, paste
  `%USERPROFILE%\Documents\pykaxe\scripts`, press Enter. Right-click the
  folder and choose **Pin to Quick access**.

To confirm from a terminal instead, run `pykaxe tools-dir` — it prints the
exact path. To use a different folder, set the `PYKAXE_TOOLS_DIR` environment
variable before launching pykaxe (see `README.md#usage`); the choice made on
first run is otherwise remembered in `~/Documents/pykaxe/config.json`.

## Saving a tool into that folder

When an AI gives you code, it has to be saved as a plain text file ending in
`.py`. Both built-in text editors need one setting changed first:

- **Mac (TextEdit):** choose **Format → Make Plain Text** *before* pasting —
  otherwise it saves a formatted document pykaxe can't read. Then **File →
  Save**, press `Cmd + Shift + G` in the save box, paste
  `~/Documents/pykaxe/scripts`, name it e.g. `reverse.py`. If asked about the
  extension, choose **Use .py**.
- **Windows (Notepad):** paste the code, then **File → Save as**. Paste
  `%USERPROFILE%\Documents\pykaxe\scripts` into the address bar. Change
  **Save as type** to **All Files** — otherwise Windows silently saves it as
  `reverse.py.txt` and pykaxe won't see it. Name it `reverse.py`.

## If something didn't work

A few fixes need the terminal. To open it: **Mac** — `Cmd + Space`, type
`Terminal`, Enter. **Windows** — **Start**, type `Command Prompt`, click it.
Type the command, press Enter.

**Mac: "permission denied" when double-clicking the launcher**

The download stripped the file's permission to run — do the four
drag-and-drop steps at the end of [step 2](#2-download-the-launcher).

**Mac: "cannot be opened because it is from an unidentified developer"**

Right-click the launcher → **Open** → **Open** again. Once only.

**"pykaxe needs Python", or double-clicking does nothing**

```bash
python3 --version    # Mac
python --version     # Windows
```

A version number like `Python 3.12.0` means Python is fine. An error means
step 1 didn't take — reinstall from
[python.org](https://www.python.org/downloads/), ticking **"Add python.exe to
PATH"** on Windows. (On Windows, if `python` fails, try `py --version`.)

**"pykaxe needs pipx"**

```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
```

On Windows write `python` instead of `python3`. Then **close the terminal and
open a fresh one** — the change doesn't apply to already-open windows — and
double-click the launcher again.

**The window opens but nothing happens for a long time**

The first run downloads pykaxe with no progress bar. Give it a couple of
minutes.

**A tool you saved doesn't appear when you type `/`**

- The file must be directly in the tools folder — pykaxe doesn't look in
  subfolders.
- It must really end in `.py` — see [saving a tool](#saving-a-tool-into-that-folder)
  for the Notepad/TextEdit settings that trip this up.
- If pykaxe was already open when you saved, press `Ctrl + S` to re-scan.

**A tool is listed under a different name than the file**

Expected — pykaxe lists tools by the `TOOL_NAME` line in the code, not the
filename. `reverse.py` may show up as `reverse-string`.
