---
id: "0013"
title: "Run state is files"
status: proposed
date: 2026-10-18
decided_by: agent-proposed
affects: ["change-store", "orchestrator", "audit-log", "approvals", "flow"]
supersedes: []
superseded_by: null
---
## Context
Changes run in the background and the app can restart mid-run; state must survive restarts
and stay auditable without a database (ADR 0008).

## Decision
1. Each change is a folder under `data/projects/<id>/changes/<cid>/` with `change.yaml`
   (state, step, attempt, decisions, note) plus every artifact of each step (request, plan,
   prompt, answer, diff, checks log/json, review, deploy logs). All writes are atomic
   (temp file then `os.replace`).
2. The orchestrator is the only writer of change state besides `approvals`, and both must
   pass through `flow.py`'s legal transitions; runs execute in a background thread, one at a
   time per change, saving state after every step.
3. On app start any change in `planning, implementing, checking, in_review` becomes
   `interrupted` with the reason "The Factory restarted while this step was running"; the
   Request page then offers "Try this step again".
4. `audit.jsonl` per project is append-only and records every transition with actor and time.
5. The owner can cancel a request (no longer rendered as working) and "Try this step again"
   after any failure or interruption.

## Reasons
- Files are inspectable and diffable; restart recovery without them would strand requests in
  fake "working" states.

## Alternatives rejected
- In-memory global state (lost on reload, lies to the owner).
- A database for changes: contradicts ADR 0008 for this data too.

## Consequences
- Tests cover restart recovery, wrong-state approvals, and the merge-conflict and dirty-repo
  `blocked` paths.
## Summary (العربية)
حالة أي طلب ملفات في مجلده: change.yaml وكل مخلفات الخطوات والسجل المراجعي append-only.
المنسّق وحده (مع الاعتمادات) يغيّر الحالة عبر انتقالات legal، والمقاطع الناتجة عن إعادة
التشغيل تصبح «interrupted» مع زر إعادة المحاولة.
