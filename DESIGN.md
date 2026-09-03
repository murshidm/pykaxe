# DESIGN.md

Layout and visual design reference for the pykaxe TUI. This describes what
is currently implemented in `src/pykaxe/app.py` (the `Pykaxe.CSS` string and
`compose()` tree), so it can be reviewed and used as the source of truth
when changing the look of the app. If you edit `Pykaxe.CSS` or `compose()`,
update this file in the same change.

Most layout/style lives in the `CSS` class variable on `Pykaxe` (and on
`FilePickerScreen`/`StatsBar`) in `app.py` — there is no external `.tcss`
file — but as of this round the app also registers a real Textual `Theme`
(`PYKAXE_THEME`, see "Theming" below) so built-in widgets it adopts
(`Footer`, `Digits`) pick up matching colors automatically.

## Design philosophy

- **A real app-owned theme, not a borrowed terminal background.** Earlier
  rounds of this design kept `BG = "ansi_default"` deliberately, so the app
  blended into whatever terminal theme the user already had. This round
  reverses that on purpose, at the user's explicit request for more visual
  "character" — matching the look of Textual's own demo app
  (`python -m textual`, `textual/demo/home.py`): a real, consistent dark
  background (`BG`) and an elevated surface (`PANEL`) the app owns
  outright. If a future change wants to go back to terminal-transparency,
  that's a deliberate reversal of *this* note, not an oversight to "fix."
- **Palette adapted from Textual's own "dracula" theme**
  (`textual/theme.py`, `BUILTIN_THEMES["dracula"]`), not picked freehand —
  `BG`, `PANEL`, `PRIMARY`, and `BORDER` all trace back to that theme's
  `background`/`panel`/`primary`/(current-line) values. `ACCENT` (amber,
  tool identity) and `SUCCESS`/`ERROR`/`WARNING` are pykaxe's own, kept
  from earlier rounds rather than replaced, since they already carry
  established, tested meaning.
- **Borders are still a primary structural device.** `round` borders dim to
  a near-invisible tone at rest and brighten only when focused/active —
  unchanged from earlier rounds, just recolored to sit against the new
  background instead of `ansi_default`.
- **Two accent colors for content, plus one for brand.** Amber (`ACCENT`)
  always means "this identifies a tool." Green (`SUCCESS`) always means
  "this is output the running subprocess produced, or a successful
  completion." `PRIMARY` (violet) is new this round and means neither of
  those — it's pykaxe's own brand/heading color (the welcome title, the
  `Digits` stat), kept strictly separate so it never gets mistaken for tool
  identity or a success signal.
- **Outcomes have their own vocabulary, separate from tool identity.**
  `ERROR` (red) and `WARNING` (amber-yellow) exist specifically so a failed
  action, an invalid input, or a caution never has to borrow `MUTED` (which
  would make it look like neutral status) or `ACCENT` (which would make it
  look like a tool name). See "Output semantics" below.
- **Chrome disappears when idle, or when not relevant to the current
  state.** The suggestions dropdown and scrollbars default to `display:
  none` / transparent and only appear when they have something to show.
  `#badge` and `StatsBar` are *mutually exclusive* — exactly one "what
  state is the app in" row is visible at a time (idle → `StatsBar`, tool
  loaded/running → `#badge`), not both, and never neither once a tool
  exists to talk about.
- **Tints over blocks for "this row is selected/active."** Confirmed
  against Textual's own installed source (`textual/design.py`): its
  built-in themes highlight an unfocused list cursor with the primary
  color at `with_alpha(0.3)` — a translucent tint — not a solid fill.
  `#suggestions`'s highlighted row follows the same restraint via
  `ACCENT_TINT`.

## Theming: a registered Textual `Theme`

`PYKAXE_THEME` (a `textual.theme.Theme`) is registered in
`Pykaxe.__init__()` and applied via `self.theme = "pykaxe"`. Its fields
mirror the plain Python color constants exactly (`primary=PRIMARY`,
`background=BG`, `panel=PANEL`, `surface=PANEL`, `accent=ACCENT`,
`success=SUCCESS`, `warning=WARNING`, `error=ERROR`, `foreground=FG`).

This exists for one reason: built-in widgets pykaxe adopts without writing
their CSS from scratch — `Footer`, `Digits` — reference Textual's own `$primary`
/ `$foreground` / `$footer-key-foreground` etc. variables internally. Without
a matching registered theme they'd render in Textual's *default* palette
(blue-based `textual-dark`), clashing with everything pykaxe draws itself.
Registering the theme once means `Footer`'s key labels come out amber
(`$footer-key-foreground` defaults to `$accent`, which is set to `ACCENT`)
with a `PANEL` background — verified in `run_test()`, not just assumed —
without a single line of custom Footer CSS.

Widgets pykaxe fully owns (`RichLog` content, `#badge`, `StatsBar`,
`#suggestions`, the file picker) keep using the plain Python constants
directly in an f-string `CSS`/`DEFAULT_CSS`, exactly as before — the theme
only needs to cover the surface built-in widgets already reference. Rich
markup strings (everything written into `RichLog`) *cannot* reference
Textual's `$variable` syntax at all — that's DOM CSS only — so those call
sites will always need the literal hex constants regardless of theming.

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
| `BORDER` | `#44475a` | resting structure | unfocused borders on RichLog/Input/suggestions, `Rule` heading lines |
| `BG` | `#282a36` | base app background | Screen, RichLog, Input, `#bottom` |
| `PANEL` | `#313442` | elevated surface | `#badge`, `StatsBar`, `#suggestions`, file picker modal |
| `PRIMARY` | `#bd93f9` (violet) | app/brand identity, headings | welcome title (`_write_heading`), `StatsBar`'s `Digits` |
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
(An earlier version of this round also had `ACCENT_WASH`, a lighter tint
for `#badge` — removed when the badge moved to a solid `PANEL` background
instead; see "Badge" below for why.)

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
so it reads as a signal rather than wallpaper.

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
│ #badge / StatsBar   (mutually exclusive)      │  ← 1-4 rows, exactly one visible
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

### 1. Badge (`#badge`) / StatsBar — the "header," state-dependent

There is no `Header` widget. Two `Static`/`Widget` rows share the same top
slot, toggled together (never both, never neither) in `update_badge()`:

**`StatsBar` — idle state (no tool loaded).** Modeled directly on
Textual's own demo app (`StarCount` in `textual/demo/home.py`), which docks
a `Digits`-based stat row above its home screen and nowhere else:

- 4 rows tall, `PANEL` background, one stat: **Tools** — the discovered
  tool count, as a `Digits` widget colored `PRIMARY`. Updated in
  `on_mount()` and again in `action_scan_tools()`.
- Deliberately *one* stat, not two. Version already has a place — the
  welcome heading's `MUTED` subtitle — so repeating it here in a much
  louder `Digits` treatment right next to it would read as a mistake
  rather than intentional emphasis. If a second real, dynamic stat becomes
  meaningful later, this is where it goes; don't add a stat for the sake
  of matching the reference layout.

**`#badge` — a tool is loaded/running.**

- Reads `<tool> · active` or `<tool> · • running`.
- `PANEL` background (elevated surface, same as `StatsBar` — both are
  "status row" contexts and share the same elevation language), 1 row
  tall, `0 1` padding, no forced text-style. Text color carries the
  state: tool name via `tool_name()` (bold `ACCENT`), state word `MUTED`
  for "active" or `SUCCESS` with a `•` for "running" — reusing `SUCCESS`
  deliberately, since green already means "this tool is live" for streamed
  stdout elsewhere; this is the same meaning applied to a status word, not
  a new one.
  - History: this was originally a solid `ACCENT` block with hardcoded
    dark inverted text (read as a heavy, dated "banner"), then briefly a
    translucent `ACCENT_WASH` tint (see the alpha-token note above), before
    settling on the current `PANEL` solid fill — closer to how Textual's
    own `StarCount` uses `background: $boost` (a neutral elevation, not a
    colored wash) for what is structurally the same kind of "persistent
    status row."
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

- **Background:** `BG`.
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
- **Background:** `PANEL` — an elevated popup surface, distinct from the
  `BG` content plane behind it (previously this matched `BG` exactly, back
  when the whole app shared one transparent-to-terminal background; now
  that the app owns real tonal layers, the dropdown gets to look
  genuinely "on top" rather than blending in).
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

`yield Footer(show_command_palette=False)` — as of this round, no longer a
hand-rolled `StatusBar`/`Button` row. Textual's real `Footer` reads
key/description straight from `Pykaxe.BINDINGS`, so there's exactly one
place each shortcut's key and label are written; the earlier
`footer_label()`/`KEY_DISPLAY` scaffolding this replaced existed
specifically to work around not having this.

- **Height:** `1` (`Footer`'s own `DEFAULT_CSS` — unconditional, not
  `auto`), same footprint as the `StatusBar` it replaced. No layout
  dimension changed.
- **Which bindings show:** every `Binding` with `show=True` (the default)
  appears; `ctrl+o`/`browse_file` is explicitly `show=False` since it's
  contextual (only relevant while collecting a `Path` argument), not a
  standing shortcut — same curation the old `StatusBar.FOOTER_ACTIONS`
  did, now expressed on the `Binding` itself instead of a separate list.
- **Key display:** `Binding("escape", ..., key_display="esc", ...)` — the
  one allowed display-only override, using Textual's own supported
  `Binding` parameter instead of the app's own `KEY_DISPLAY` dict this
  replaced.
- **Colors:** entirely from `PYKAXE_THEME` (see "Theming" above) — key
  labels render bold `ACCENT` on `PANEL`, description text `FG`. No
  Footer-specific CSS is written in `Pykaxe.CSS`; changing the theme's
  `accent`/`panel`/`foreground` moves the footer automatically.
- **Tooltips:** every `Binding` has a `tooltip=` — free with `Footer`,
  something the old `StatusBar` had no equivalent for.
- **Click behavior:** `FooterKey.on_mouse_down` calls
  `self.app.simulate_key(...)`, running the real keyboard-action pipeline
  (more correct than the old `on_button_pressed` dispatch it replaced,
  which has been removed). The existing generic `Pykaxe.on_click` still
  refocuses the `Input` afterward — verified via `run_test()` that a
  simulated footer click both fires the action and returns focus.

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
- **Panel (`#picker`):** `width: 80%; height: 80%`, `background: {PANEL}`
  (an elevated surface — previously `BG`, back when the whole app shared
  one background; now the modal gets to look genuinely "above" the main
  screen the same way `#suggestions` does), `border: round {FG}` —
  **unconditional** bright, unlike every other bordered widget in the app,
  which is conditional on `:focus`, because the modal has no unfocused
  state worth showing.
- **Title bar (`#picker-title`):** 1 row, `{MUTED}` text on `{PANEL}`,
  shows the current directory and the two available keys (`esc` cancel,
  `backspace` up a directory). Updates live as you navigate.
- **`DirectoryTree`:** stock Textual widget, only re-themed with
  `background: {PANEL}` to match — no custom row/selection colors are
  set, so its selection highlight is whatever the registered `PYKAXE_THEME`
  provides (this is the one widget in the app not fully re-skinned by
  hand — it inherits from the theme like Footer/Digits do).
- **No escape binding on the screen itself** — `Pykaxe`'s own `escape`
  binding is `priority=True` and wins before the pushed screen ever sees
  the key, so cancel is handled centrally in `Pykaxe.action_interrupt()`
  (`self.screen.dismiss(None)`), not on `FilePickerScreen`.

## Interactive states summary

| Element | Rest | Focus/Active | Hover |
| --- | --- | --- | --- |
| Input | border `BORDER` | border `FG` | — |
| RichLog | border `BORDER` | (no change — not typically focused) | — |
| Footer keys | bg `PANEL`, key `ACCENT` bold, label `FG` | (Textual default) | `$block-hover-background` (Textual default) |
| Scrollbars (RichLog/#suggestions) | transparent | — | thumb `MUTED`, track transparent |
| Scrollbars (actively scrolling) | — | thumb `FG` | — |
| #suggestions option | bg `PANEL` | highlighted: bg `ACCENT_TINT` (30% alpha), `text-style: none` | same as highlighted |
| #badge (tool loaded) | hidden | bg `PANEL`, color-coded text, shown | — |
| StatsBar (idle) | shown | bg `PANEL`, `Digits` in `PRIMARY` | — |
| File picker border | `FG` always | `FG` always | — |

## Where to change things

- **Recolor anything:** edit the constants at the top of `app.py` (`FG`,
  `MUTED`, `BORDER`, `BG`, `PANEL`, `PRIMARY`, `ACCENT`, `SUCCESS`,
  `ERROR`, `WARNING`, `ACCENT_TINT`) — every rule below references these.
  If the color also needs to reach a *built-in* widget (Footer, Digits,
  DirectoryTree), update the matching field on `PYKAXE_THEME` too — the
  Python constant alone only affects pykaxe's own hand-written CSS/markup,
  not Textual's `$variable`-driven internals.
- **Add a heading:** use `self._write_heading(title, copy_text)` with a
  `Text` built via `.append()` — don't hand-roll another plain markup
  title line for a new top-level context. Reserve it for genuine context
  transitions; using it for routine messages would turn a signal into
  wallpaper.
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
- **Add a new stat to StatsBar:** only if it's genuinely dynamic and
  meaningful (like tool count) — see the "deliberately one stat" note in
  "Layout sections" above before adding a second `Digits`.
- **Add/remove a section:** edit `Pykaxe.compose()` (widget tree) and add a
  matching block to `Pykaxe.CSS` (or the widget's own `DEFAULT_CSS`, the
  pattern `StatsBar`/`FilePickerScreen` use).
- **Change what a section shows/when:** the *content* of each widget
  (badge/StatsBar text, placeholder text, suggestion rows, log lines) is
  driven from Python methods (`update_badge`, `update_input_placeholder`,
  `on_input_changed`, `write_line*`), not CSS — check there too if the
  visible *behavior* (not just color) needs to change.
