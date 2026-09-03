# DESIGN.md

Layout and visual design reference for the pykaxe TUI. This describes what
is currently implemented in `src/pykaxe/app.py` (the `Pykaxe.CSS` string and
`compose()` tree), so it can be reviewed and used as the source of truth
when changing the look of the app. If you edit `Pykaxe.CSS` or `compose()`,
update this file in the same change.

All layout/style lives in one place: the `CSS` class variable on `Pykaxe`
(and on `FilePickerScreen`) in `app.py`. There is no external `.tcss` file.

## Design philosophy

- **Borrow the terminal, don't repaint it.** Every background is
  `ansi_default` (`BG`), not a hex color — the app has no background color
  of its own and blends into whatever terminal theme the user already has.
- **Borders are the only structural device.** No filled panels, no drop
  shadows, no boxes-within-boxes. Sections are separated by `round` borders
  that dim to a near-invisible dark grey at rest and brighten only when
  focused/active.
- **Two accent colors, used consistently, nothing else.** Amber (`ACCENT`)
  always means "this identifies a tool." Green (`SUCCESS`) always means
  "this is output the running subprocess produced, or a successful
  completion," as opposed to pykaxe's own chrome (`MUTED`/`FG`). No other
  color is used for tool/result identity.
- **Outcomes have their own vocabulary, separate from tool identity.**
  `ERROR` (red) and `WARNING` (amber-yellow) exist specifically so a failed
  action, an invalid input, or a caution never has to borrow `MUTED` (which
  would make it look like neutral status) or `ACCENT` (which would make it
  look like a tool name). See "Output semantics" below.
- **Chrome disappears when idle.** The badge, the suggestions dropdown, and
  scrollbars all default to `display: none` / transparent and only appear
  when they have something to show. Nothing sits on screen "just in case."

## Color palette

Defined as module-level constants in `app.py` (lines 30–37) and interpolated
into the CSS via f-string — there is no theming system, changing a look
means editing these constants directly.

| Constant | Value | Meaning | Used in |
| --- | --- | --- | --- |
| `FG` | `#f2f2f2` | primary/focused | body text, focused input/log border, badge text-on-amber is `#1a1a1a` instead |
| `MUTED` | `#8a8a8a` | secondary/inactive/neutral status | help text, prompts, hint lines, unfocused hover states, neutral info messages |
| `BORDER` | `#3a3a3a` | resting structure | unfocused borders on RichLog/Input/suggestions |
| `BG` | `ansi_default` | all backgrounds | Screen, RichLog, Input, buttons, suggestions, file picker |
| `ACCENT` | `#f2c94c` (amber) | tool identity | `/toolname` in welcome list & suggestions, the badge background, tool banner |
| `SUCCESS` | `#7ee787` (green) | live subprocess output / successful outcome | every line streamed from a running tool's stdout, `✓ <tool> finished`, `✓ copied — N lines` |
| `ERROR` | `#e5534b` (red) | failed action / invalid input | `× no such tool`, `× <field> is required`, `× <tool> failed — exit N`, `× <tool> killed — ...` |
| `WARNING` | `#e5c07b` (amber-yellow) | caution, not a failure | `! a tool is already running — press esc to stop it first` |

There is no dark/light theme switch — this is one fixed palette.

### Output semantics — semantic helpers, not scattered markup

`app.py` defines six small helper functions right after `footer_label()` —
`info()`, `success()`, `warning()`, `error()`, `cancelled()`, `tool_name()` —
each wrapping a string in the right color plus, where relevant, a semantic
symbol prefix (`✓` success, `!` warning, `×` error). Every feedback line
pykaxe prints goes through one of these instead of an inline `f"[{COLOR}]...[/]"`
literal, so what a message *means* is decided once, in one place, rather
than re-decided per call site. `cancelled()` deliberately reuses `MUTED`
(not `ERROR`) — a deliberate user-initiated stop (Esc) is not a failure and
should not read as one.

A clean tool exit (`returncode == 0`) now prints `✓ <tool> finished` in
`SUCCESS` — previously a successful run left the log silent after its last
streamed output line, so there was no way to tell "still running" from
"done" by looking at the log alone. A non-zero exit or a resource-limit
kill prints the `ERROR` equivalent instead.

### Completion feedback: who already explained the kill

`_run_and_pump`'s completion tail (the code above) has to decide what, if
anything, to say once a process exits — but three other places can *also*
kill the process first and print their own explanation: `_watchdog` (runtime
limit — prints `ERROR`), `action_quit` (app closing — prints `info`), and
`action_interrupt` (user pressed Esc — prints `cancelled`). To avoid a
second, redundant completion line stacking under whichever of those already
fired, `Shell.kill_announced` is a one-shot flag: each of those three sites
sets it to `True` right before killing, the tail checks it and stays silent
if set, then resets it to `False` for the next run.

This replaced an earlier version that special-cased `returncode in (-9,
-15)` to mean "already handled, say nothing" — which was wrong for any
*external* kill (an OOM kill, a segfault, something outside pykaxe sending
the signal): those also produce a `-9`/`-15` returncode but nothing had
actually printed an explanation, so the tool would die silently. The flag
only suppresses the tail when a pykaxe code path is actually the one that
decided to kill the process, so an unexplained termination now correctly
falls through to `× <tool> failed — exit -9`.

## Layout sections (top to bottom)

```
┌──────────────────────────────────────────────┐
│ #badge            "pykaxe active > toolname"  │  ← 1 row, hidden unless a tool is loaded
├──────────────────────────────────────────────┤
│                                                │
│ RichLog           scrolling output/log        │  ← fills all remaining vertical space
│                                                │
├──────────────────────────────────────────────┤
│ #suggestions       (tool picker popup)         │  ← hidden unless typing "/..."
│ Input              "Type / to load a tool..."  │  ← always visible, single entry point
│ StatusBar          [esc] [ctrl+y] [ctrl+s] [ctrl+c]│ ← 1 row, docked bottom
└──────────────────────────────────────────────┘
```

`#bottom` (a `Vertical`) wraps suggestions + Input + StatusBar and is
`dock: bottom; height: auto` — it's pinned to the bottom edge and only as
tall as its (variable) contents. `RichLog` has no explicit height, so it
absorbs whatever space is left above `#bottom`.

### 1. Badge (`#badge`) — the "header"

There is no `Header` widget; this `Static` at the very top is the closest
thing to one, and it is off by default.

- **Hidden state:** `display: none`, zero height — most of the time this
  row doesn't exist at all.
- **Shown state:** appears the instant a tool is loaded (`update_badge()`),
  reads `pykaxe active > <tool>` or `pykaxe running > <tool>`.
- **Style:** solid amber (`ACCENT`) background, dark text (`#1a1a1a`, hardcoded
  — the one color not drawn from the shared palette, chosen for contrast
  against amber rather than reusing `FG`), bold, left-aligned, 1 row tall,
  `0 1` padding.
- **Purpose:** the only persistent visual indicator of "which tool is
  active/running" — useful since the RichLog scrolls the tool's own banner
  out of view.

### 2. Content section (`RichLog`)

The main output pane — every printed line (welcome text, tool banners,
prompts, streamed subprocess output, error/status lines) goes here via
`write_line()` / `write_line_to()`.

- **Background:** `ansi_default` (transparent to terminal).
- **Border:** `round {BORDER}` always — this widget does not brighten on
  focus (it's rarely focused directly; the Input is), so its border stays
  the dim resting grey permanently.
- **Scrollbar:** fully transparent at rest (`scrollbar-background/-color:
  transparent`), becomes `{MUTED}` on hover and `{FG}` while actively
  scrolling — a scrollbar that's invisible until you reach for it.
- **Text color semantics inside this pane** (not CSS, but content markup
  applied per-line in Python via the `info/success/warning/error/cancelled/
  tool_name` helpers — see "Output semantics" above):
  - default/unstyled → terminal foreground (raw user input echoed back)
  - `MUTED` via `info()`/`cancelled()` → pykaxe's own neutral chrome:
    prompts, hints, "cancelled — \<tool\>"
  - `ACCENT` via `tool_name()` → tool names (welcome list, suggestions,
    banners)
  - `SUCCESS` (green) via `success()` → lines streamed live from a running
    tool's stdout, plus `✓ <tool> finished` / `✓ copied — N lines` — the
    color that distinguishes "the subprocess said this, or this succeeded"
    from "pykaxe said this"
  - `ERROR` (red) via `error()` → invalid input, failed actions, non-zero
    exits, kills — always prefixed `×`
  - `WARNING` (amber-yellow) via `warning()` → a caution that isn't a
    failure (e.g. a tool already running) — always prefixed `!`
  - `FG` → the one-off `pykaxe v0.1.x` title line
- **Scrollback cap:** `max_lines=MAX_OUTPUT_LINES` (2000) — old lines are
  dropped, not paginated.

### 3. Tool picker popup (`#suggestions`)

This is the thing that appears when you type `/`. It is an `OptionList`
sitting directly above the `Input`, inside `#bottom`.

- **Trigger:** `on_input_changed` — visible input starts with `/` and the
  app isn't mid argument-collection. Cleared/hidden on submit, on escape,
  or when the query no longer starts with `/`.
- **Hidden state:** `display: none, height: auto` — takes no space until
  populated.
- **Shown state:** up to 8 fuzzy-matched tool names, each rendered as
  `[ACCENT]toolname[/]: description` — same amber-for-name convention as the
  welcome screen and badge, `{MUTED}` for the description.
- **Sizing:** `max-height: 6` — caps to 6 visible rows regardless of match
  count; scrolls internally rather than growing to push the Input off
  screen.
- **Background:** `ansi_default`, same as everything else — it is not a
  separate "popup surface," it reads as part of the same panel, just an
  extra strip above the Input.
- **Highlight:** the focused/hovered option gets `background: {BORDER}` —
  intentionally low-contrast/neutral (dark grey), not an accent color, so
  the amber tool-name text stays the visual anchor rather than the
  selection box.
- **Scrollbar:** same ghost-until-hover treatment as RichLog.
- **Selecting an option** (click or Enter) calls `load_tool()` directly —
  this is the same code path as typing `/name` and hitting Enter in the
  Input; the popup is a discovery aid, not a separate flow.

### 4. Input

The single text-entry widget; every user action funnels through it (see
`app.py`'s three-mode dispatch in `on_input_submitted`).

- **Border:** `round {BORDER}` at rest → `round {FG}` on `:focus`. This
  is the *only* widget whose border actually changes state in response to
  focus — it's meant to read as "the thing you're typing into right now."
- **Placeholder text is dynamic, not static** (`update_input_placeholder`):
  it always describes what typing + Enter will currently do —
  `"Type / to load a tool..."`, `"enter <arg-name> (ctrl+o to browse)..."`,
  or `"<tool> is running — press esc to stop..."`. The placeholder is
  effectively part of the design system: it's the app's only per-state
  instructional text.

### 5. Status bar (`StatusBar`, the "footer")

A `Horizontal` of 4 flat buttons, docked at the very bottom row.

- **Height:** exactly 1 row.
- **Buttons:** `[esc] interrupt`, `[ctrl+y] copy`, `[ctrl+s] scan`,
  `[ctrl+c] quit` — each built by `footer_label()` as
  `[FG]<key>[/] [MUTED]<label>[/]`, i.e. the keybinding is bright, the
  action name is dim. This is the one place `FG` is used for something
  other than "focused."
  - Note: `esc` is drawn from the same `Binding` list but its label text is
    "Interrupt" in `BINDINGS` — the footer button hardcodes "interrupt"
    itself rather than reading the binding description.
- **Button style:** `background: {BG}`, `border: solid {BORDER}` (not
  `round`, unlike every other bordered element — buttons are the one
  rectangular/solid-border exception), `margin-right: 2` between them,
  `min-width: 0` so each sizes to its label instead of stretching.
- **Hover:** border brightens to `{FG}`, background stays `{BG}` (no
  fill-on-hover).
- **`text-style: none` is forced** on default/hover/focus states — this
  suppresses Textual's default bold-on-focus so the footer stays visually
  quiet even when a button has keyboard focus.

## File browser modal (`FilePickerScreen`)

Pushed with `ctrl+o` while the Input is prompting for a `Path`-typed
argument. This is the one place the design deliberately departs from the
rest of the app's "border only brightens on focus" rule — **the modal's
border is always bright white**, never dim, because the whole point of a
modal is to read as unambiguously active/on-top regardless of focus state
within it.

```
┌─ #picker (80% × 80%, centered) ──────────────┐
│ #picker-title   "/path — esc to cancel, ..."  │  ← 1 row, MUTED text
├───────────────────────────────────────────────┤
│                                                │
│         DirectoryTree (file browser)          │
│                                                │
└────────────────────────────────────────────────┘
```

- **Screen-level:** `align: center middle` — the panel floats centered over
  the dimmed-by-Textual-default backdrop, rather than filling the screen.
- **Panel (`#picker`):** `width: 80%; height: 80%`, `background: {BG}`
  (same transparent-to-terminal background as everything else — the
  differentiation from the main screen is the border, not a fill color),
  `border: round {FG}` — **unconditional** white, unlike every other
  bordered widget in the app which is conditional on `:focus`. This is the
  "different color" the file browser has: it's not a different palette, it's
  the *same* `FG` used elsewhere for focus, but applied statically here
  because the modal has no unfocused state worth showing.
- **Title bar (`#picker-title`):** 1 row, `{MUTED}` text on `{BG}`, shows
  the current directory and the two available keys (`esc` cancel,
  `backspace` up a directory). Updates live as you navigate.
- **`DirectoryTree`:** stock Textual widget, only re-themed with
  `background: {BG}` to match — no custom row/selection colors are set, so
  its selection highlight is whatever Textual's default theme provides
  (this is the one widget in the app not fully re-skinned).
- **No escape binding on the screen itself** — `Pykaxe`'s own `escape`
  binding is `priority=True` and wins before the pushed screen ever sees
  the key, so cancel is handled centrally in `Pykaxe.action_interrupt()`
  (`self.screen.dismiss(None)`), not on `FilePickerScreen`.

## Interactive states summary

| Element | Rest | Focus/Active | Hover |
| --- | --- | --- | --- |
| Input | border `BORDER` | border `FG` | — |
| RichLog | border `BORDER` | (no change — not typically focused) | — |
| Buttons | border `BORDER`, bg `BG` | border unchanged, `text-style: none` forced | border `FG` |
| Scrollbars (RichLog/#suggestions) | transparent | — | thumb `MUTED`, track transparent |
| Scrollbars (actively scrolling) | — | thumb `FG` | — |
| #suggestions option | bg `BG` | highlighted: bg `BORDER`, `text-style: none` | same as highlighted |
| #badge | hidden | amber bg, dark text, shown | — |
| File picker border | white always | white always | — |

## Where to change things

- **Recolor anything:** edit the constants at the top of `app.py` (`FG`,
  `MUTED`, `BORDER`, `BG`, `ACCENT`, `SUCCESS`, `ERROR`, `WARNING`) — every
  rule below references these, nothing is hardcoded elsewhere except the
  badge's `#1a1a1a` text and the file picker's unconditional `FG` border.
- **Change what a message means (info/success/warning/error/cancelled):**
  don't reach for a raw `f"[{COLOR}]...[/]"` string — use the matching
  helper (`info()`, `success()`, `warning()`, `error()`, `cancelled()`,
  `tool_name()`) defined next to `footer_label()` near the top of `app.py`.
  That's the single place the outcome vocabulary is defined; call sites
  should never re-decide it.
- **Add/remove a section:** edit `Pykaxe.compose()` (widget tree) and add a
  matching block to `Pykaxe.CSS`.
- **Change what a section shows/when:** the *content* of each widget
  (badge text, placeholder text, suggestion rows, log lines) is driven from
  Python methods (`update_badge`, `update_input_placeholder`,
  `on_input_changed`, `write_line*`), not CSS — check there too if the
  visible *behavior* (not just color) needs to change.
