# DESIGN.md

Layout and visual design reference for the pykaxe TUI. This describes what
is currently implemented in `src/pykaxe/app.py` (the `Pykaxe.CSS` string and
`compose()` tree), so it can be reviewed and used as the source of truth
when changing the look of the app. If you edit `Pykaxe.CSS` or `compose()`,
update this file in the same change.

Most layout/style lives in the `CSS` class variable on `Pykaxe` (and on
`FilePickerScreen`) in `app.py` — there is no external `.tcss` file — but
the app also registers a real Textual `Theme` (`PYKAXE_THEME`, see
"Theming" below) so the one built-in widget it adopts (`Footer`) picks up
matching colors automatically.

## Design philosophy

- **Borrow the terminal, don't repaint it.** `BG = "ansi_default"` — the
  app has no background color of its own; every background blends into
  whatever terminal theme the user already has. An earlier draft of this
  round tried a real app-owned dark background plus a separate elevated
  `PANEL` tone (matching Textual's own demo app's look); that was reverted
  at the user's explicit request for exactly one background, transparent
  where possible, so borders and `Rule` dividers — the app's actual
  structural language — read clearly against *any* terminal, and don't
  have to compete with filled color blocks.
- **Borders are a primary structural device.** `round` borders dim to a
  near-invisible neutral grey at rest and brighten only when
  focused/active. `BORDER` is a plain, hue-neutral grey specifically so it
  reads clearly regardless of what background color is actually behind it
  (a terminal can be anything from pure black to solarized to a pastel
  theme) — it doesn't try to color-match a fixed background, because there
  isn't one.
- **Two accent colors for content, plus one for brand.** Amber (`ACCENT`)
  always means "this identifies a tool." Green (`SUCCESS`) always means
  "this is output the running subprocess produced, or a successful
  completion." `PRIMARY` (violet) is pykaxe's own brand/heading color (the
  welcome title), kept strictly separate so it never gets mistaken for
  tool identity or a success signal. `PRIMARY`/`ACCENT`/`SUCCESS`/`ERROR`/
  `WARNING` are foreground/text colors, not backgrounds — terminal
  transparency never applied to them, and dropping the app-owned
  background didn't touch any of them.
- **Outcomes have their own vocabulary, separate from tool identity.**
  `ERROR` (red) and `WARNING` (amber-yellow) exist specifically so a failed
  action, an invalid input, or a caution never has to borrow `MUTED` (which
  would make it look like neutral status) or `ACCENT` (which would make it
  look like a tool name). See "Output semantics" below.
- **Chrome disappears when idle, or when not relevant to the current
  state.** `#badge`, the suggestions dropdown, and scrollbars all default
  to `display: none` / transparent and only appear when they have
  something to show. There is no persistent "header" chrome shown while
  idle — an earlier draft tried a `Digits`-based tool-count stat bar there
  (see CHANGELOG); removed at the user's request as unnecessary.
- **Tints over blocks for "this row is selected/active."** Confirmed
  against Textual's own installed source (`textual/design.py`): its
  built-in themes highlight an unfocused list cursor with the primary
  color at `with_alpha(0.3)` — a translucent tint — not a solid fill.
  `#suggestions`'s highlighted row follows the same restraint via
  `ACCENT_TINT`. `#badge` follows the same "no filled block" principle,
  just taken further: flat colored text on the same background as
  everything else, not even a tint — see "Badge" below for why.

## Theming: a registered Textual `Theme`

`PYKAXE_THEME` (a `textual.theme.Theme`) is registered in
`Pykaxe.__init__()` and applied via `self.theme = "pykaxe"`. Its fields
mirror the plain Python color constants (`primary=PRIMARY`,
`accent=ACCENT`, `foreground=FG`, `success=SUCCESS`, `warning=WARNING`,
`error=ERROR`), and `background`/`surface`/`panel` are all set to `BG`
(`"ansi_default"`) — one background concept everywhere, confirmed via
`run_test()` that Textual accepts `"ansi_default"` as a `Theme` background
value without error (it's handled as a special ANSI-passthrough marker,
not literal black).

This exists for one reason: `Footer`, the one built-in widget pykaxe
adopts without writing its CSS from scratch, references Textual's own
`$primary` / `$foreground` / `$footer-key-foreground` etc. variables
internally. Without a matching registered theme it would render in
Textual's *default* palette (blue-based `textual-dark`), clashing with
everything pykaxe draws itself. Registering the theme once means
`Footer`'s key labels come out amber (`$footer-key-foreground` defaults to
`$accent`, which is set to `ACCENT`) — verified in `run_test()`, not just
assumed — without a single line of custom Footer CSS.

Widgets pykaxe fully owns (`RichLog` content, `#badge`, `#suggestions`, the
file picker) keep using the plain Python constants directly in an
f-string `CSS`, exactly as before — the theme only needs to cover the
surface `Footer` already references. Rich markup strings (everything
written into `RichLog`) *cannot* reference Textual's `$variable` syntax at
all — that's DOM CSS only — so those call sites will always need the
literal hex constants regardless of theming.

`ENABLE_COMMAND_PALETTE = False` on `Pykaxe`: Textual's generic command
palette (theme switching, its own screenshot action, etc.) isn't part of
pykaxe's designed/tested feature set, so it's turned off rather than left
as an unreviewed surface behind an undocumented `ctrl+p`. `Footer` is also
constructed with `show_command_palette=False` for the same reason.

## Color palette

Defined as module-level constants near the top of `app.py`.

| Constant | Value | Meaning | Used in |
| --- | --- | --- | --- |
| `FG` | `#f2f2f2` | primary/focused | body text, focused input border |
| `MUTED` | `#8a8a8a` | secondary/inactive/neutral status | help text, prompts, hint lines, neutral info messages |
| `BORDER` | `#3a3a3a` | resting structure | unfocused borders on RichLog/Input/suggestions, `Rule` heading lines |
| `BG` | `ansi_default` | the one background, everywhere | Screen, RichLog, Input, `#bottom`, `#badge`, `#suggestions`, file picker |
| `PRIMARY` | `#bd93f9` (violet) | app/brand identity, headings | welcome title (`_write_heading`) |
| `ACCENT` | `#f2c94c` (amber) | tool identity | `/toolname` in welcome list & suggestions, badge tool name, tool banner title |
| `SUCCESS` | `#7ee787` (green) | live subprocess output / successful outcome | every line streamed from a running tool's stdout, `✓ <tool> finished`, `✓ copied — N lines`, badge "• running" |
| `ERROR` | `#e5534b` (red) | failed action / invalid input | `× no such tool`, `× <field> is required`, `× <tool> failed — exit N`, `× <tool> killed — ...` |
| `WARNING` | `#e5c07b` (amber-yellow) | caution, not a failure | `! a tool is already running — press esc to stop it first` |

There is no dark/light theme switch — one fixed palette, mirrored into
`PYKAXE_THEME` as described above.

### Alpha token: `ACCENT_TINT`

Textual CSS has no `color 30%` shorthand — alpha has to be baked into an
`rgba()`/hex-with-alpha value up front (confirmed against Textual's
`<color>` CSS type reference). `_alpha(hex, alpha)` does that conversion.

| Constant | Value | Meaning | Used in |
| --- | --- | --- | --- |
| `ACCENT_TINT` | `ACCENT` @ 30% alpha | "this row is the current selection" | `#suggestions` highlighted option — mirrors Textual's own `block-cursor-blurred-background` (`primary.with_alpha(0.3)`) |

Still `ACCENT` at heart — this doesn't add a new color, just a restrained
way of applying the existing one to a whole row instead of only to text.
Alpha-blending is composited against whatever's actually behind it at
paint time, so this still works correctly now that the background it's
blended over is `ansi_default` rather than a fixed hex.

### Headings: `Rule`, not a plain text line

`_write_heading(title, copy_text)` marks each new top-level context — the
welcome banner, or a freshly loaded tool's banner — with a `rich.rule.Rule`
(`style=BORDER`, `align="left"`) instead of a plain markup string. The rule
line itself stays quiet/structural (`BORDER`); the `title` — a
`rich.text.Text` built with `.append(text, style=...)` rather than markup —
carries the actual color: bold `PRIMARY` for "pykaxe" (brand identity),
bold `ACCENT` for a tool name (tool identity — deliberately a different
color from the app's own brand, so a tool banner never reads as "part of
pykaxe's own chrome"). Used sparingly, at genuine context transitions only,
so it reads as a signal rather than wallpaper. This is the *only* heading
mechanism in the app — see "Badge" below for why `#badge` was deliberately
kept from becoming a second, competing one.

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

`app.py` defines helper functions — `info()`, `prompt()`, `success()`,
`warning()`, `error()`, `cancelled()`, `tool_name()`, `user_input()` — each
wrapping a string in the right color plus, where relevant, a semantic
symbol prefix (`✓` success, `!` warning, `×` error, `›` prompt). Every
feedback line pykaxe prints goes through one of these instead of an inline
`f"[{COLOR}]...[/]"` literal, so what a message *means* is decided once, in
one place, rather than re-decided per call site. `cancelled()` deliberately
reuses `MUTED` (not `ERROR`) — a deliberate user-initiated stop (Esc) is
not a failure and should not read as one.

A clean tool exit (`returncode == 0`) prints `✓ <tool> finished` in
`SUCCESS` — a successful run leaving the log silent after its last
streamed output line would give no way to tell "still running" from
"done." A non-zero exit or a resource-limit kill prints the `ERROR`
equivalent instead.

### Completion feedback: who already explained the kill

`_run_and_pump`'s completion tail has to decide what, if anything, to say
once a process exits — but three other places can *also* kill the process
first and print their own explanation: `_watchdog` (runtime limit — prints
`ERROR`), `action_quit` (app closing — prints `info`), and
`action_interrupt` (user pressed Esc — prints `cancelled`). To avoid a
second, redundant completion line stacking under whichever of those
already fired, `Shell.kill_announced` is a one-shot flag: each of those
three sites sets it to `True` right before killing, the tail checks it and
stays silent if set, then resets it to `False` for the next run. This is
also what correctly surfaces a *genuinely* unexplained kill (an OOM kill,
a segfault — no pykaxe code path did it) as `× <tool> failed — exit -9`
instead of going silent: the flag only suppresses the tail when a pykaxe
kill site actually set it.

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
│ Footer             [ctrl+c] Quit  [ctrl+y] Copy ... │ ← 1 row, docked bottom
└──────────────────────────────────────────────┘
```

`#bottom` (a `Vertical`) wraps suggestions + Input and is `dock: bottom;
height: auto` — pinned to the bottom edge, only as tall as its (variable)
contents. `Footer` docks itself independently (it has its own `dock:
bottom` in its `DEFAULT_CSS`), so it isn't nested inside `#bottom`.
`RichLog` has no explicit height, so it absorbs whatever space is left.
There is no persistent widget shown while idle — the top slot is simply
empty (`display: none`) until a tool is loaded.

### 1. Badge (`#badge`) — the "header," when a tool is loaded

There is no `Header` widget; this `Static` at the very top is the closest
thing to one, and it is off by default.

- **Hidden state:** `display: none`, zero height — most of the time this
  row doesn't exist at all.
- **Shown state:** appears the instant a tool is loaded (`update_badge()`),
  reads `<tool> · active` or `<tool> · • running`.
- **Style:** flat text on `BG` — no filled block, no border, no distinct
  background at all. Text color carries the state: tool name via
  `tool_name()` (bold `ACCENT`), state word `MUTED` for "active" or
  `SUCCESS` with a `•` for "running" — reusing `SUCCESS` deliberately,
  since green already means "this tool is live" for streamed stdout
  elsewhere; this is the same meaning applied to a status word, not a new
  one.
  - **Why not a filled block or an elevated panel:** earlier drafts tried
    a solid `ACCENT` block with hardcoded dark inverted text, then a
    translucent tint, then a solid elevated `PANEL` fill — all read as a
    second, competing "heading," visually fighting the `Rule`-based
    heading that also appears (in `RichLog`) the moment a tool loads.
    Consistency won: there's exactly one heading *mechanism* in this app
    (`_write_heading`'s `Rule`), and `#badge` is a plain status line, not
    a rival banner. Removing its background also directly serves "one
    background color, borders stand out" — a distinct badge background
    was itself one of the "many colors" being consolidated away.
  - **A `height: 1` widget has no room for a border.** An earlier draft
    added `border-bottom: solid {BORDER}` for a subtle separator from
    `RichLog` below — that silently collapsed the badge's own content area
    to zero height (`Size(height=0)`, confirmed via `run_test()`), since
    the single available row went entirely to the border edge instead of
    the text. If a divider is wanted here again, the badge's `height` has
    to grow to accommodate it.
- **Purpose:** the only persistent visual indicator of "which tool is
  active/running" — useful since the RichLog scrolls the tool's own banner
  out of view.

### 2. Content section (`RichLog`)

The main output pane — every printed line (welcome text, tool banners,
prompts, streamed subprocess output, error/status lines) goes here via
`write_line()` / `write_line_to()` / `_write_heading()`.

- **Background:** `BG` (`ansi_default`).
- **Border:** `round {BORDER}` always — this widget does not brighten on
  focus (it's rarely focused directly; the Input is), so its border stays
  the dim resting tone permanently.
- **Scrollbar:** fully transparent at rest (`scrollbar-background/-color:
  transparent`), becomes `{MUTED}` on hover and `{FG}` while actively
  scrolling — a scrollbar that's invisible until you reach for it.
- **Text color semantics inside this pane** (not CSS, but content markup
  applied per-line in Python via the `info/prompt/success/warning/error/
  cancelled/tool_name/user_input` helpers, or a `Rule` via
  `_write_heading()` — see "Output semantics"/"Headings" above):
  - `FG` via `user_input()` → the user's own submitted text, echoed back —
    a third voice distinct from pykaxe's `MUTED` chrome and a tool's
    `SUCCESS` stdout. Also `escape_markup()`s the value: without it, a
    submitted value containing `[` would be parsed as Rich markup instead
    of shown literally.
  - `FG` via `prompt()` (with a `›` lead-in) → the argument prompt itself
    ("enter text:") — one level above the `MUTED` help line that may
    follow it. Also escapes the prompt text before styling: a default
    value that happens to look like markup (e.g. `enter interval [2.0]:`,
    from the shipped `sci-fi-quote-loop` example) would otherwise have its
    brackets silently eaten, or a default matching a real Rich style name
    (`[bold]`, `[red]`) actually applied as styling.
  - `MUTED` via `info()`/`cancelled()` → pykaxe's own neutral chrome:
    hints, "cancelled — \<tool\>"
  - `ACCENT` via `tool_name()` → tool names (welcome list, suggestions,
    badge)
  - `SUCCESS` (green) via `success()` → lines streamed live from a running
    tool's stdout, plus `✓ <tool> finished` / `✓ copied — N lines`
  - `ERROR` (red) via `error()` → invalid input, failed actions, non-zero
    exits, kills — always prefixed `×`
  - `WARNING` (amber-yellow) via `warning()` → a caution that isn't a
    failure (e.g. a tool already running) — always prefixed `!`
  - A `Rule` via `_write_heading()` → the `pykaxe vX` welcome title
    (`PRIMARY`) and each tool's banner (`ACCENT`)
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
- **Shown state:** up to 8 fuzzy-matched tool names, each rendered via
  `tool_name()` (bold `ACCENT`) plus `{MUTED}` description.
- **Sizing:** `max-height: 6` — caps to 6 visible rows regardless of match
  count; scrolls internally rather than growing to push the Input off
  screen.
- **Background:** `BG`, same as everything else — it is not a separate
  "popup surface," it reads as part of the same panel, just an extra strip
  above the Input.
- **Highlight:** the focused/hovered option gets `background:
  {ACCENT_TINT}` — a translucent 30%-alpha wash of the tool-identity
  color, not a solid fill. Previously this was a flat `{BORDER}` grey —
  low-contrast enough that the "you're here" signal was easy to miss, and
  disconnected from what's actually being selected (a tool). `ACCENT_TINT`
  ties the highlight to the same amber that already means "tool"
  everywhere else, at an alpha chosen to mirror Textual's own
  default-theme convention for an unfocused list cursor
  (`block-cursor-blurred-background`, confirmed in `textual/design.py`).
  Only `color`/`background`/`text-style` apply to this component class —
  no `border`, confirmed against `OptionList.DEFAULT_CSS` in Textual's own
  installed source.
- **Scrollbar:** same ghost-until-hover treatment as RichLog.
- **Selecting an option** (click or Enter) calls `load_tool()` directly —
  this is the same code path as typing `/name` and hitting Enter in the
  Input; the popup is a discovery aid, not a separate flow.

### 4. Input

The single text-entry widget; every user action funnels through it (see
`app.py`'s three-mode dispatch in `on_input_submitted`).

- **Background:** `BG`.
- **Border:** `round {BORDER}` at rest → `round {FG}` on `:focus`. This
  is the *only* widget whose border actually changes state in response to
  focus — it's meant to read as "the thing you're typing into right now."
- **Placeholder text is dynamic, not static** (`update_input_placeholder`):
  it always describes what typing + Enter will currently do —
  `"Type / to load a tool..."`, `"enter <arg-name> (ctrl+o to browse)..."`,
  or `"<tool> is running — press esc to stop..."`. The placeholder is
  effectively part of the design system: it's the app's only per-state
  instructional text.

### 5. Footer (Textual's built-in `Footer` widget)

`yield Footer(show_command_palette=False)` — not a hand-rolled
`StatusBar`/`Button` row. Textual's real `Footer` reads key/description
straight from `Pykaxe.BINDINGS`, so there's exactly one place each
shortcut's key and label are written.

- **Height:** `1` (`Footer`'s own `DEFAULT_CSS` — unconditional, not
  `auto`).
- **Which bindings show:** every `Binding` with `show=True` (the default)
  appears; `ctrl+o`/`browse_file` is explicitly `show=False` since it's
  contextual (only relevant while collecting a `Path` argument), not a
  standing shortcut.
- **Key display:** `Binding("escape", ..., key_display="esc", ...)` — the
  one allowed display-only override.
- **Colors:** entirely from `PYKAXE_THEME` (see "Theming" above) — key
  labels render bold `ACCENT`, description text `FG`. No Footer-specific
  CSS is written in `Pykaxe.CSS`; changing the theme's `accent`/
  `foreground` moves the footer automatically.
- **Tooltips:** every `Binding` has a `tooltip=`.
- **Click behavior:** `FooterKey.on_mouse_down` calls
  `self.app.simulate_key(...)`, running the real keyboard-action pipeline.
  The existing generic `Pykaxe.on_click` still refocuses the `Input`
  afterward — verified via `run_test()` that a simulated footer click both
  fires the action and returns focus.

## File browser modal (`FilePickerScreen`)

Pushed with `ctrl+o` while the Input is prompting for a `Path`-typed
argument. This is the one place the design deliberately departs from the
rest of the app's "border only brightens on focus" rule — **the modal's
border is always bright `FG`**, never dim, because the whole point of a
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
  (same background as everything else — the differentiation from the main
  screen is the border, not a fill color), `border: round {FG}` —
  **unconditional** bright, unlike every other bordered widget in the app,
  which is conditional on `:focus`, because the modal has no unfocused
  state worth showing.
- **Title bar (`#picker-title`):** 1 row, `{MUTED}` text on `{BG}`, shows
  the current directory and the two available keys (`esc` cancel,
  `backspace` up a directory). Updates live as you navigate.
- **`DirectoryTree`:** stock Textual widget, only re-themed with
  `background: {BG}` to match — no custom row/selection colors are set, so
  its selection highlight is whatever the registered `PYKAXE_THEME`
  provides (this is the one widget in the app not fully re-skinned by
  hand — it inherits from the theme like Footer does).
- **No escape binding on the screen itself** — `Pykaxe`'s own `escape`
  binding is `priority=True` and wins before the pushed screen ever sees
  the key, so cancel is handled centrally in `Pykaxe.action_interrupt()`
  (`self.screen.dismiss(None)`), not on `FilePickerScreen`.

## Interactive states summary

| Element | Rest | Focus/Active | Hover |
| --- | --- | --- | --- |
| Input | border `BORDER` | border `FG` | — |
| RichLog | border `BORDER` | (no change — not typically focused) | — |
| Footer keys | key `ACCENT` bold, label `FG` | (Textual default) | `$block-hover-background` (Textual default) |
| Scrollbars (RichLog/#suggestions) | transparent | — | thumb `MUTED`, track transparent |
| Scrollbars (actively scrolling) | — | thumb `FG` | — |
| #suggestions option | bg `BG` | highlighted: bg `ACCENT_TINT` (30% alpha), `text-style: none` | same as highlighted |
| #badge | hidden | flat text on `BG`, color-coded, shown | — |
| File picker border | `FG` always | `FG` always | — |

## Where to change things

- **Recolor anything:** edit the constants at the top of `app.py` (`FG`,
  `MUTED`, `BORDER`, `BG`, `PRIMARY`, `ACCENT`, `SUCCESS`, `ERROR`,
  `WARNING`, `ACCENT_TINT`) — every rule below references these. If the
  color also needs to reach `Footer` (the one built-in widget adopted),
  update the matching field on `PYKAXE_THEME` too — the Python constant
  alone only affects pykaxe's own hand-written CSS/markup, not Textual's
  `$variable`-driven internals.
- **Add a heading:** use `self._write_heading(title, copy_text)` with a
  `Text` built via `.append()` — don't hand-roll another plain markup
  title line for a new top-level context, and don't introduce a second
  competing heading widget (see "Badge" above for why that was reverted).
  Reserve it for genuine context transitions; using it for routine
  messages would turn a signal into wallpaper.
- **Change what a message means (info/success/warning/error/cancelled):**
  don't reach for a raw `f"[{COLOR}]...[/]"` string — use the matching
  helper (`info()`, `prompt()`, `success()`, `warning()`, `error()`,
  `cancelled()`, `tool_name()`, `user_input()`) defined near the top of
  `app.py`. That's the single place the outcome vocabulary is defined;
  call sites should never re-decide it.
- **Change a keyboard shortcut's key, tooltip, or whether it shows in the
  footer:** edit the matching `Binding` in `Pykaxe.BINDINGS` directly
  (`key`, `description`, `show`, `key_display`, `tooltip`) — `Footer`
  reads all of it live, nothing else to update.
- **Add/remove a section:** edit `Pykaxe.compose()` (widget tree) and add a
  matching block to `Pykaxe.CSS` (or the widget's own `DEFAULT_CSS`, the
  pattern `FilePickerScreen` uses). Before adding a persistent
  header/status widget, check whether it's answering a question the user
  already has another way to answer (placeholder text, the badge, streamed
  output) — a `Digits`-based tool-count stat bar was tried and removed
  this round for exactly that reason.
- **Change what a section shows/when:** the *content* of each widget
  (badge text, placeholder text, suggestion rows, log lines) is driven
  from Python methods (`update_badge`, `update_input_placeholder`,
  `on_input_changed`, `write_line*`), not CSS — check there too if the
  visible *behavior* (not just color) needs to change.
