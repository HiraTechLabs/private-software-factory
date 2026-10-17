# UI system

Related decision: ADR 0005 (status: proposed). This document is the binding UI contract; changes
to tokens, components, or enums are UI system changes and require an ADR plus an update to this
file, the catalog page (`/ui`), `tests/test_ui_catalog.py`, and `tests/test_tokens_contrast.py`.
ملخص بالعربية: `UI_SYSTEM.ar.md`.

## Brief

- **Users.** One operator who owns the Factory, occasionally a reviewer.
- **Jobs.** Review a change with its evidence; approve or reject at gates; see what is running,
  waiting, or broken; trace a change to its rules, decisions, and architecture.
- **Context.** Long sessions, dense information. The UI is a workbench, not a marketing page.
- **Languages.** English now. Arabic (RTL) is planned; all layout properties are logical
  (`inline`/`block`) and all themes are tokenized so an RTL flag later is a data change.

## Concept: the Line

The Factory's flow is the product, so the flow is shown as a Line: `intake > plan > build >
checks > review > merge > dev > prod`. Color means state and nothing else. Boldness is spent in
one place only — the LineRail. Everything else is quiet: paper, ink, hairlines.

## Principles

1. **State first.** Every object shows its state with a StateLight plus a text label drawn from
   the closed enums in `src/factory/ui_vocab.py`.
2. **Evidence first.** No claim without a source. Every number is computed from data, or the UI
   says "Not available yet"; never a hard-coded 0.
3. **Gates are explicit.** Approve and reject actions exist only inside the Gate component. The
   Gate shows what is being approved, what machines verified, what models said (with ModeTag),
   and what is unverified.
4. **Autonomy is visible.** Each step shows `manual`, `shadow`, or `live` via ModeTag.
5. **References are links.** Rules, decisions, and graph nodes render as RefChip links, not prose.
6. **Quiet chrome.** No decorative gradients, shadows, or entrance animations. Motion only
   answers an action. Color never carries meaning alone — it always sits beside a text label.

## Tokens

Source of truth: `design/tokens.json`, generated into `static/tokens.css` by
`scripts/build_tokens.py`. CSS never uses literal hex, rgb, or hsl values; it uses
`var(--c-*)`, `var(--size-*)`, `var(--space-*)`, `var(--radius-*)`, and `var(--layout-*)`.
The primary button is solid `ink` on `paper`. There is no brand accent color.
The default theme follows `prefers-color-scheme`; light values are the default in media queries
that target light, dark values the override.

## Type

- Sans for prose and labels, mono for identifiers: task ids, rule ids, commit hashes, paths,
  logs, diffs.
- Font stack (no font host; see `docs/ui/fonts-todo.md`):
  sans `IBM Plex Sans, IBM Plex Sans Arabic, system-ui, sans-serif`,
  mono `IBM Plex Mono, ui-monospace, monospace`.
- Sentence case everywhere. No all-caps, no letter-spacing on labels.
- Line length under 72ch (`--layout-measure`).

## Layout

Left rail lists only pages that exist (now: Projects; UI catalog). The shell: rail on the
inline-start edge, PageHeader on top of the content column.

```text
Shell                                   Change page (planned, build the shell only)
+--------+------------------------+     +-----------------------------------------------+
| Rail   | PageHeader             |     | LineRail: intake>plan>build>checks>review>... |
|        +------------------------+     +----------------------------+------------------+
|        | content                |     | Evidence: spec, diff,      | Gate (sticky)    |
+--------+------------------------+     | checks, review report      | approve / reject |
                                        +----------------------------+------------------+
```

## Component catalog (closed)

The catalog is closed. Each component is a Jinja macro in `templates/components/` with styles in
`static/components.css`, and is rendered live (in every state, every light kind, every mode) on
the `/ui` catalog page:

| Component | Purpose |
|---|---|
| StateLight | Small state dot in a light kind, always with a text label |
| ModeTag | Tag for `manual`, `shadow`, `live`; dashed outline in shadow mode |
| LineRail | The flow as a line of steps with states |
| Gate | Approve/reject surface with evidence, verification, and unverified lists |
| EvidenceRow | One row of evidence linking artifact + summary |
| RefChip | Chip link to a rule, ADR, or graph node |
| DataTable | Dense, sortable-by-convention data table |
| FilterBar | Row of filters above a data table |
| DiffView | Two-column diff rendering (planned usage; built now) |
| LogView | Scrollable mono log view |
| Button | Solid `ink` primary and quiet secondary |
| Field | Labeled input with help and error text |
| EmptyState | Empty list message inviting the next action |
| ErrorState | What failed, where, and how to recover |
| PageHeader | Page title, description, and primary action slot |

## State vocabulary (closed)

Defined once in `src/factory/ui_vocab.py`; templates never hard-code state strings or badges.

- **Light kinds:** `idle, run, hold, stop, shadow, done`.
- **Task states and their light:** draft idle, planned idle, implementing run, checking run,
  in_review run, awaiting_approval hold, merged done, deployed_dev done, awaiting_prod hold,
  live done, blocked hold, failed stop, cancelled idle.
- **Modes:** `manual, shadow, live`. `shadow` renders with a dashed outline in the shadow color.
- **Registry readiness (used now):** `registered` (light: done), `invalid` (light: stop).

## Copy rules

- Name things by what the user does, not how the system works.
- Buttons say what happens: "Create project", never "Submit". The same action keeps the same
  word in toasts.
- Errors say what went wrong and how to fix it, with no apology.
- Empty states invite the next action.

## Enforcement

- `scripts/build_tokens.py` (re)generates `static/tokens.css`; `--check` fails if stale (CI).
- `scripts/ui_lint.py` fails on literal colors, raw px sizing (outside the allowed exceptions),
  uppercase transforms, letter-spacing, physical CSS properties, and any state label in
  templates that does not come from `ui_vocab.py`.
- `tests/test_tokens_contrast.py` requires WCAG contrast: 4.5:1 for `ink, steel` and the four
  `*-text` colors against `surface` and `paper` in both themes; 3:1 for the six light colors
  against `surface` in both themes.
- `tests/test_ui_catalog.py` renders `/ui` and asserts every component, light kind, task state,
  and mode appears, so adding an enum value forces a catalog update.
