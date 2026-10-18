---
id: "0014"
title: "Token CSS variable names keep the hyphens from tokens.json"
status: proposed
date: 2026-10-18
decided_by: agent-proposed
affects: ["ui-system"]
supersedes: []
superseded_by: null
---
## Context
`design/tokens.json` names multi-word colors with hyphens (`ink-soft`, `accent-ink`,
`need-bg`, `rail-ink`, `rail-link`, `rail-active`). The generator (`scripts/build_tokens.py`)
replaced every hyphen with an underscore, so it emitted `--c-ink_soft`, `--c-rail_ink`, and
so on. The stylesheet and templates use the hyphenated names (`--c-ink-soft`, `--c-rail-ink`),
which resolved to nothing: the left rail rendered its text in the inherited dark ink on the
dark rail, so Today, Projects, Models, and Guide were invisible.

## Decision
`build_tokens.py` writes each color variable with its key unchanged, so
`--c-ink-soft`, `--c-accent-ink`, `--c-need-bg`, `--c-rail-ink`, `--c-rail-link`, and
`--c-rail-active` exist. `design/tokens.json` and `static/tokens.css` stay the single source
and its generated form; `tests/test_tokens_contrast.py` already reads the JSON keys.

## Reasons
- Hyphenated custom properties are the CSS convention and match the keys the designer writes.
- The mismatch was invisible to the contrast test (it reads the JSON), so only a real render
  caught it; the screenshots in `docs/ITERATION_2_REPORT.md` are the proof.

## Alternatives rejected
- Rename the keys to underscores: it pushes the generator's quirk into the design file.
- Rename the stylesheet back to underscores: it keeps two spellings for the same idea.

## Consequences
- `scripts/build_tokens.py` (protected core) changes in one place; `--check` stays meaningful.
- Any future token key with a hyphen generates a hyphenated variable and matches the CSS.
## Summary (العربية)
كان مُولِّد الرموز يستبدل الشُرَط السفلية في أسماء الألوان، فصارت المتغيرات مثل `--c-rail_ink`
بينما التنسيق يستخدم `--c-rail-ink`، فظهر الشريط الجانبي بلا نص. الأسماء الآن تبقى كما في
ملف الرموز، وهذا ما أصلح اختفاء قائمة التنقل.
