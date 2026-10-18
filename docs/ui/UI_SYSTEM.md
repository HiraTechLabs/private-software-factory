# UI system

The Factory's interface is calm and plain. It is built from design tokens, a small set of
plain-named components, and a closed status vocabulary. This file is the record of that system;
`docs/ui/mockup.html` is the visual reference. See ADR 0010.

## Look

- Light paper page, deep teal accent for buttons and links, dark teal left rail, rounded panels,
  comfortable 17 px text, generous spacing.
- Status colors: **needs you** amber, **working** blue, **done** green, **failed** red,
  **not started** grey. A status always shows a text label as well as a color.
- Boldness is spent in two places only: the amber "needs you" rows on Today, and the Pipeline on a
  Request page. Everything else stays quiet.
- Dark theme follows the operating system setting (`prefers-color-scheme`).
- Type: the system font stack, with an Arabic-capable fallback. Monospace only for ids, paths, and
  code. Sentence case; no all-caps labels.
- Only logical CSS properties (`margin-inline-start`, not `margin-left`), so Arabic right-to-left
  stays possible later.

## Tokens

`design/tokens.json` is the source of truth; `scripts/build_tokens.py` generates
`src/factory/static/tokens.css`. Colors: `ink`, `ink-soft`, `paper`, `card`, `line`, `accent`,
`accent-ink`, `need`, `need-bg`, `work`, `done`, `fail`, `fail-bg`, `idle` (plus rail and a few
surface helpers). Sizes: control radius 8 px, panel radius 12 px, rail 232 px, base font 17 px.
`tests/test_tokens_contrast.py` proves the text colors meet 4.5:1 and the status colors meet 3:1 on
`card` in both themes.

## Vocabulary

- **Status** — where something is now (a colored dot plus a text label). Kinds: `idle`, `work`,
  `need`, `done`, `fail`.
- **Pipeline** — the nine steps of the flow on a Request page.
- **Your decision** — the sticky box on a Request page with the approve, send-back, and cancel
  actions.
- **Provider words** — "You paste", "Local model", "Demo model".

Labels are defined once in `src/factory/ui_vocab.py`; templates read them from there, never as
literals.

## Components

Plain names, defined as Jinja macros in `src/factory/templates/components.html` and styled with the
tokens: Status, Page header, Pipeline, Diff view, Log view, Empty state, Error state. Add a
component only when a page uses it.

## Rules kept by `scripts/ui_lint.py`

No `disabled` attributes and no hash-only links (no dead controls). No placeholder phrases and no
filler text. No banned iteration-1 terms. No literal colors outside `tokens.css`. No physical CSS
properties.
