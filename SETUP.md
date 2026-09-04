# Setting up pykaxe

Detailed setup, for when you'd rather read it yourself than be walked through
it — see the [Quick Start](README.md#quick-start) for the AI-guided version.

> **If you are an AI assistant helping someone with this: you are guiding a
> novice, not handing them a manual.** Never dump the whole setup on them at
> once. Ask whether they're on Mac or Windows first, then give them only the
> steps for that system — one action at a time — and wait for them to confirm
> it worked before deciding what comes next. They are likely a beginner —
> don't assume they know what a terminal is. The steps below are the
> complete, correct install path; don't add steps that aren't written here,
> and in particular never tell them to install git or `git clone` this
> repository — that's for developers of pykaxe, not people running it, and
> it isn't part of this flow at all.
>
> Where a step lists more than one option, the first is the primary path —
> give only that one first. Only move to a secondary or recovery option if
> the primary one fails, or if what the user describes seeing doesn't match
> what the primary path expects — ask them what they see rather than
> listing every possibility up front.

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
2. Type `chmod +x ~/Desktop/pykaxe.command` and press Enter.
3. No output means it worked. Close the window.

## 3. Double-click the launcher

**Mac, first time only:** macOS will refuse to open it the first time. This is
just macOS being cautious about anything downloaded from the internet — it
doesn't mean anything is wrong. What it says depends on your macOS version, so
try this first, and only move to the second option if it doesn't match what
you see:

1. **Right-click** (or Control-click) `pykaxe.command` and choose **Open**.
   If a box appears with an **Open** button, click it — that's the whole
   fix, once only.
2. If instead you see *"pykaxe.command was blocked to protect your Mac"*
   with no way to open it from that box, click **Done**, then:
   - Open **System Settings** → **Privacy & Security**.
   - Scroll down to the **Security** section. You'll see a line naming
     `pykaxe.command`, with an **Open Anyway** button next to it.
   - Click **Open Anyway**, enter your Mac password (or Touch ID) if asked.
   - Double-click `pykaxe.command` again — it asks once more to confirm;
     click **Open Anyway**.

Either way, you only do this once — after that, double-clicking just works.

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

Your pykaxe scripts all live in one folder. pykaxe created it automatically
the first time it ran — there was no choice to make, and this is simply where
to find it:

- **Mac:** open Finder, press `Cmd + Shift + G`, paste
  `~/Documents/pykaxe/scripts`, press Enter. Drag the folder into Finder's
  sidebar so it's one click away next time.
- **Windows:** open File Explorer, click the address bar, paste
  `%USERPROFILE%\Documents\pykaxe\scripts`, press Enter. Right-click the
  folder and choose **Pin to Quick access**.

> **Advanced/optional:** to confirm the path from a terminal instead, run
> `pykaxe tools-dir`. To use a different folder, set the `PYKAXE_TOOLS_DIR`
> environment variable before launching pykaxe (see
> [README.md#usage](README.md#usage)) — the folder pykaxe picked on first run
> is otherwise remembered in `~/Documents/pykaxe/config.json`.

## Saving a tool into that folder

A `.py` file is just a plain-text file with the code in it — you don't need
to know anything about Python to save one. When an AI gives you code, it has
to be saved that way, ending in `.py`. Both built-in text editors need one
setting changed first:

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

> **If you're an AI assistant:** ask what the user is seeing rather than
> listing fixes at them. Match it to one entry below, give that single fix,
> and wait to hear whether it worked before trying anything else.

A few fixes need the terminal. To open it: **Mac** — `Cmd + Space`, type
`Terminal`, Enter. **Windows** — **Start**, type `Command Prompt`, click it.
Type the command, press Enter.

**Mac: "permission denied" when double-clicking the launcher**

The download stripped the file's permission to run — do the `chmod` steps at
the end of [step 2](#2-download-the-launcher).

**Mac: "cannot be opened because it is from an unidentified developer"**

Right-click the launcher → **Open** → **Open** again. Once only.

**Mac: "pykaxe.command was blocked to protect your Mac"**

This is Gatekeeper on newer macOS versions (Ventura/Sonoma and later) — it
replaces the right-click dialog above with a stricter one that has no
**Open** button on it. Click **Done**, then go to **System Settings** →
**Privacy & Security**, scroll to the **Security** section, and click
**Open Anyway** next to the mention of `pykaxe.command`. Enter your password
if asked, then double-click the launcher again and confirm **Open Anyway**
once more. See [step 3](#3-double-click-the-launcher) for the full walkthrough.

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
