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
- **Tints over blocks for "this row is selected/active."** Confirmed
  against Textual's own installed source (`textual/design.py`,
  `theme.py`): its built-in themes highlight an unfocused list cursor with
  the primary color at `with_alpha(0.3)` — a translucent tint — not a
  solid fill. Every "you're here" indicator in this app (`#suggestions`
  highlight, `#badge`) follows the same restraint via `ACCENT_TINT`/
  `ACCENT_WASH` rather than an opaque colored block. See "Color palette"
  below.

## Color palette

Defined as module-level constants in `app.py` (lines 30–37) and interpolated
into the CSS via f-string — there is no theming system, changing a look
means editing these constants directly.

| Constant | Value | Meaning | Used in |
| --- | --- | --- | --- |
| `FG` | `#f2f2f2` | primary/focused | body text, focused input/log border, welcome title (via `_write_heading`) |
| `MUTED` | `#8a8a8a` | secondary/inactive/neutral status | help text, prompts, hint lines, unfocused hover states, neutral info messages |
| `BORDER` | `#3a3a3a` | resting structure | unfocused borders on RichLog/Input/suggestions |
| `BG` | `ansi_default` | all backgrounds | Screen, RichLog, Input, buttons, suggestions, file picker |
| `ACCENT` | `#f2c94c` (amber) | tool identity | `/toolname` in welcome list & suggestions, badge tool name, tool banner title (via `_write_heading`) |
| `SUCCESS` | `#7ee787` (green) | live subprocess output / successful outcome | every line streamed from a running tool's stdout, `✓ <tool> finished`, `✓ copied — N lines` |
| `ERROR` | `#e5534b` (red) | failed action / invalid input | `× no such tool`, `× <field> is required`, `× <tool> failed — exit N`, `× <tool> killed — ...` |
| `WARNING` | `#e5c07b` (amber-yellow) | caution, not a failure | `! a tool is already running — press esc to stop it first` |

There is no dark/light theme switch — this is one fixed palette.

### Alpha tokens: `ACCENT_TINT` / `ACCENT_WASH`

Textual CSS has no `color 30%` shorthand — alpha has to be baked into an
`rgba()`/hex-with-alpha value up front (confirmed against Textual's `<color>`
CSS type reference). `_alpha(hex, alpha)` does that conversion; two derived
tokens sit next to the base palette:

| Constant | Value | Meaning | Used in |
| --- | --- | --- | --- |
| `ACCENT_TINT` | `ACCENT` @ 30% alpha | "this row is the current selection" | `#suggestions` highlighted option — mirrors Textual's own `block-cursor-blurred-background` (`primary.with_alpha(0.3)`) |
| `ACCENT_WASH` | `ACCENT` @ 12% alpha | "this row is a tool's live status" | `#badge` background |

Both are still `ACCENT` at heart — this doesn't add a new color to the
palette, just a restrained way of applying the existing one to a whole row
instead of only to text.

### Headings: `Rule`, not a plain text line

`_write_heading(title, copy_text)` marks each new top-level context — the
welcome banner, or a freshly loaded tool's banner — with a `rich.rule.Rule`
(`style=BORDER`, `align="left"`) instead of a plain markup string. The rule
line itself stays quiet/structural (`BORDER`, same as every other resting
border in the app); the `title` — a `rich.text.Text` built with
`.append(text, style=...)` rather than markup — carries the actual color
(bold `FG` for "pykaxe", bold `ACCENT` for a tool name). Used sparingly, at
genuine context transitions only, so it reads as a signal rather than
wallpaper.

`RichLog.write()` accepts any Rich renderable, not only markup strings —
`_write_heading` is the one place in the app that uses that directly
instead of going through `write_line_to`. Because a `Rule`'s decorative
dashes have no meaningful plain-text form, `shell.lines` (the buffer
`ctrl+y` copies from) gets a separate, plain `copy_text` argument instead —
e.g. `"pykaxe v0.1.10"` or `"word-count — Count the number of words in
text."` — so copying output right after a heading doesn't paste a wall of
dashes or lose the title's content.

Building the title via `Text.append()` rather than a markup f-string is
also a small security improvement, not just idiomatic: `Text.append()`
never parses its argument as markup, so a tool name or description
containing `[` can't be interpreted as a style tag — no `escape_markup()`
call needed at these two sites (contrast with `tool_name()`/`user_input()`
elsewhere, which must escape because they build markup strings).

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
│ #badge            "toolname · active"         │  ← 1 row, hidden unless a tool is loaded
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
  reads `<tool> · active` or `<tool> · • running`.
- **Style:** `ACCENT_WASH` (a translucent 12%-alpha tint, not a solid
  fill — see "Alpha tokens" above) background, left-aligned, 1 row tall,
  `0 1` padding, no forced text-style. Text color does the work instead of
  a block: tool name is `tool_name()` (bold `ACCENT`), the state word is
  `MUTED` for "active" or `SUCCESS` with a `•` for "running" — reusing
  `SUCCESS` deliberately, since green already means "this tool is live" for
  streamed stdout elsewhere in the app; this isn't a new meaning for the
  color, the same one applied to a status word instead of output text.
  Previously this was a solid `ACCENT` block with hardcoded dark text and
  forced bold — replaced because it read as a heavy, dated "inverted
  banner" rather than a status line, and because a solid full-saturation
  block for something shown on *every* tool load turned out to compete
  with the actual outcome colors (`ERROR`/`WARNING`/`SUCCESS`) for
  attention instead of staying in the background like other chrome.
  - **A `height: 1` widget has no room for a border.** An earlier version
    of this change added `border-bottom: solid {BORDER}` for a subtle
    separator from the `RichLog` below — that silently collapsed the
    badge's own content area to zero height (`Size(height=0)`, confirmed
    via `run_test()`), since the single available row went entirely to the
    border edge instead of the text. If a divider is wanted here again,
    the badge's `height` has to grow to accommodate it; don't add a border
    edge to a `height: 1` widget expecting the text to still fit.
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
  tool_name/user_input/prompt` helpers — see "Output semantics" above):
  - `FG` via `user_input()` → the user's own submitted text, echoed back —
    a third voice distinct from pykaxe's `MUTED` chrome and a tool's
    `SUCCESS` stdout. `user_input()` also `escape_markup()`s the value,
    which matters beyond styling: without it, a submitted value containing
    `[` would be parsed as Rich markup instead of shown literally.
  - `FG` via `prompt()` (with a `›` lead-in) → the argument prompt itself
    ("enter text:") — the thing that requires action next, one level above
    the `MUTED` help line that may follow it. Previously both used `info()`
    and were visually identical. `prompt_next_arg()` also escapes the
    prompt text before styling it — a default value that happens to look
    like markup (e.g. `enter interval [2.0]:`, from the shipped
    `sci-fi-quote-loop` example) would otherwise have its brackets silently
    eaten and any word matching a real Rich style name (`[bold]`, `[red]`,
    etc.) actually applied as styling.
  - `MUTED` via `info()`/`cancelled()` → pykaxe's own neutral chrome: hints,
    "cancelled — \<tool\>"
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
  - A `Rule` via `_write_heading()` (not markup — a Rich renderable
    written directly) → the `pykaxe vX` welcome title and each tool's
    banner. See "Headings" above.
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
- **Highlight:** the focused/hovered option gets `background: {ACCENT_TINT}`
  — a translucent 30%-alpha wash of the tool-identity color, not a solid
  fill. Previously this was `{BORDER}` (a flat, near-invisible dark grey)
  — low-contrast enough that the "you're here" signal was easy to miss,
  and, being an unrelated neutral color, disconnected from what's actually
  being selected (a tool). `ACCENT_TINT` ties the highlight to the same
  amber that already means "tool" everywhere else, at an alpha chosen to
  mirror Textual's own default-theme convention for an unfocused list
  cursor (`block-cursor-blurred-background`, confirmed in
  `textual/design.py`) rather than inventing a new intensity. Only
  `color`/`background`/`text-style` apply to this component class — no
  `border`, confirmed against `OptionList.DEFAULT_CSS` in Textual's own
  source.
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
  - **Single source of truth:** `StatusBar` is constructed with
    `Pykaxe.BINDINGS` (`StatusBar(self.BINDINGS)`) and builds each button's
    key + label by reading the matching `Binding.key`/`Binding.description`
    at compose time — `StatusBar.FOOTER_ACTIONS` only picks *which* four
    bindings appear and in what order (`ctrl+o`/browse is deliberately
    excluded here — it's contextual, not a standing shortcut). `KEY_DISPLAY`
    is the one allowed display-only override (`"escape"` → `"esc"`); a
    binding's key or description can't drift out of sync with the footer
    since there's nothing left to retype by hand.
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
| #suggestions option | bg `BG` | highlighted: bg `ACCENT_TINT` (30% alpha), `text-style: none` | same as highlighted |
| #badge | hidden | bg `ACCENT_WASH` (12% alpha), color-coded text, shown | — |
| File picker border | white always | white always | — |

## Where to change things

- **Recolor anything:** edit the constants at the top of `app.py` (`FG`,
  `MUTED`, `BORDER`, `BG`, `ACCENT`, `SUCCESS`, `ERROR`, `WARNING`,
  `ACCENT_TINT`, `ACCENT_WASH`) — every rule below references these,
  nothing is hardcoded elsewhere except the file picker's unconditional
  `FG` border. `ACCENT_TINT`/`ACCENT_WASH` are derived from `ACCENT` via
  `_alpha()`, not independent colors — changing `ACCENT` moves both
  automatically.
- **Add a heading:** use `self._write_heading(title, copy_text)` with a
  `Text` built via `.append()` — don't hand-roll another plain markup
  title line for a new top-level context. Reserve it for genuine context
  transitions (see "Headings" above); using it for routine messages would
  turn a signal into wallpaper.
- **Change what a message means (info/success/warning/error/cancelled):**
  don't reach for a raw `f"[{COLOR}]...[/]"` string — use the matching
  helper (`info()`, `prompt()`, `success()`, `warning()`, `error()`,
  `cancelled()`, `tool_name()`, `user_input()`) defined next to
  `footer_label()` near the top of `app.py`. That's the single place the
  outcome vocabulary is defined; call sites should never re-decide it.
- **Change a keyboard shortcut's key or footer text:** edit the matching
  `Binding` in `Pykaxe.BINDINGS` — `StatusBar` reads both from there, so
  there's nothing else to update. To change *which* bindings the footer
  shows or their order, edit `StatusBar.FOOTER_ACTIONS`.
- **Add/remove a section:** edit `Pykaxe.compose()` (widget tree) and add a
  matching block to `Pykaxe.CSS`.
- **Change what a section shows/when:** the *content* of each widget
  (badge text, placeholder text, suggestion rows, log lines) is driven from
  Python methods (`update_badge`, `update_input_placeholder`,
  `on_input_changed`, `write_line*`), not CSS — check there too if the
  visible *behavior* (not just color) needs to change.
