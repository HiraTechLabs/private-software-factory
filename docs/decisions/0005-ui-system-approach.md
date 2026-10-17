---
id: "0005"
title: "UI system approach: tokens, closed catalogs, enforced by lint and tests"
status: proposed
date: 2026-10-17
decided_by: agent-proposed
affects: ["ui-system"]
supersedes: []
superseded_by: null
---
## Context
The Factory needs a defensible, consistent UI without a design team or a JS framework:
server-rendered templates must stay visually uniform and screen-reader friendly, including a
future Arabic RTL mode.

## Decision
- All numeric design values (colors, sizes, spacing, radius, layout) become tokens in
  `design/tokens.json`, generated into `static/tokens.css` for light and dark themes.
- The component catalog is closed: the only UI components are Jinja macros listed in
  `docs/ui/UI_SYSTEM.md` built in `templates/components/` + `static/components.css`.
- The state vocabulary is closed: all state labels and light kinds come from
  `src/factory/ui_vocab.py`.
- A lint script and tests enforce all of this so drift fails CI (see AGENTS.md section 4.3).
- The primary button is solid `ink` on `paper`; color never carries meaning alone; the default
  theme follows `prefers-color-scheme`.

Needs owner acceptance as the standing UI contract.

## Reasons
- Closed catalogs make reviews fast: any new style culprit is visible immediately.
- Physical CSS properties would break future Arabic RTL layouts; logical properties keep it ready.
- Tokens over a hosted design system avoid external CDN dependencies (R).

## Alternatives rejected
- Tailwind or a CSS framework: class soup, no tokens, hard to lint for RTL.
- Component library (Web Components): needs a JS build, against the stack decision.

## Consequences
- Adding any component, token, or enum requires updating the docs, the catalog, and the lint.
- Colors are limited to the token palette; gradients and shadows are banned in the chrome.
## Summary (العربية)
نظام واجهة موثّق: قيم تصميم واحدة في tokens.json، قائمة مكونات مغلقة بالماكرو،
مفردات حالات مغلقة بالبايثون، مع أداة تدقيق اختبارات تمنع الانحراف. بانتظار موافقة المالك.
