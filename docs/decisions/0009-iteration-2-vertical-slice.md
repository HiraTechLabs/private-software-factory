---
id: "0009"
title: "Iteration 2: vertical slice first; supersedes the iteration-1 agent file; graph_check changes"
status: accepted
date: 2026-10-18
decided_by: human
affects: ["web-app", "ui-system", "checks", "orchestrator", "flow"]
supersedes: []
superseded_by: null
---
## Context
The iteration-1 audit found governance scaffolding with only one working product feature
(registering a project). The owner approved the "make it real" plan: a full working vertical
slice before any widening, no dead controls, and plain vocabulary.

## Decision
1. The solver file for this iteration is the delivered `AGENTS.md` ("Make it real"), which
   replaces the iteration-1 agent file (recorded here rather than editing the accepted ADR 0003).
2. Build the thinnest complete path (request → plan → build → checks → review → merge approval
   → dev → production approval → live) before polishing any single part; no dead controls
   anywhere in the UI.
3. `scripts/graph_check.py` (protected core) changes as asked: `mermaid()` replaced with the
   appendix A renderer (valid Mermaid, dashed planned edges, prefix `n_`, `group` subgraphs);
   optional `group`, `evidence`, and `target_path` fields allowed; an implemented node of kind
   `service`, `module`, or `store` under `src/` or `data/` must list evidence test ids that
   exist under `tests/` and every planned node must carry `target_path`.

## Reasons
- A trustworthy narrow pipeline beats a broad mock that lies; the flow must be real before clever.
- Disabled buttons and sample data trained the owner to distrust the app; R10 and R12 fix that.
- Evidence in the graph keeps "implemented" honest: a node without a passing test is not done.

## Alternatives rejected
- Polish the iteration-1 UI catalog and wire features behind it: it would repeat the audit's
  core failure (buttons that do not work).
- Loosen graph_check instead of extending it: reduces trust when trust is the goal.

## Consequences
- The `/ui` component catalog, its test, and its lint rules are deleted (work moves to the real
  pages and `docs/ui/mockup.html`); ADR 0005 is superseded by 0010.
- Every new engine module must land with evidence test ids in the same commit (same-commit rule).
## Summary (العربية)
التكرار الثاني «اجعله حقيقياً»: شريحة واحدة كاملة تعمل من الطلب حتى Live قبل أي توسيع، ولا
أزرار ميتة، ومفردات بسيطة. استُبدل ملف التعليمات السابق، وطُوّر فاحص الرسم ليطلب إثبات
اختباري لكل عقدة معمّلة ومساراً لكل عقدة مخططة.
