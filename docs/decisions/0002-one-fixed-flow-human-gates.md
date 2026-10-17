---
id: "0002"
title: "One fixed flow; humans approve merge and production"
status: accepted
date: 2026-10-17
decided_by: human
affects: ["manifest", "web-app", "checks", "orchestrator"]
supersedes: []
superseded_by: null
---
## Context
Every change to a product must pass one flow, and the approval policy must not change silently
per project or per agent run.

## Decision
There is one fixed flow (intake, plan, build, checks, review, merge, deploy dev, release prod).
Humans approve merges and production releases. The defaults live in the manifest schema
(`human_approval_required_for_merge`, `human_approval_required_for_production`), both defaulting
to `True`. Disabling either flag requires a written waiver naming an accepted ADR; the manifest is
invalid without it. The agent never removes or weakens a gate, check, or test to make something pass.

## Reasons
- The defaults being on keeps the human gate in place even for untouched manifests.
- A waiver must point to a real accepted decision, so any exception is traceable.
- Put anywhere else, the policy could drift per project; the schema keeps it uniform.

## Alternatives rejected
- Per-project opt-in to approval: the first mistake would ship an unapproved change.
- Policy only in prose (docs): prose can be ignored; schema validation cannot.

## Consequences
- Manifest validation reads the decisions log to verify waivers (ADR 0008 keeps the log in Git).
- The catalog of "how to run a change" is fixed; changing the flow itself is a new ADR.
## Summary (العربية)
مسار واحد ثابت لكل تغيير، واعتماد البشر إلزامي لكل عملية دمج أو إطلاق للإنتاج. المنعطفان
مفعلان افتراضياً في المخطط، وأي استثناء يحتاج إعفاءً يشير إلى قرار مقبول، وإلا فالمخطط غير صالح.
