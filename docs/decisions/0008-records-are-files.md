---
id: "0008"
title: "Records are files in Git, not a database"
status: proposed
date: 2026-10-17
decided_by: agent-proposed
affects: ["decisions-log", "graph", "ui-system", "manifest", "registry"]
supersedes: []
superseded_by: null
---
## Context
The decisions log, architecture graph, UI system, and manifests could live in a database that an
API writes to, or as plain files reviewed in Git.

## Decision
All Factory records (decisions, graph, UI system) and project manifests are plain text files in
Git. They are read and written by the app in the same commits as the code they describe, and
reviewed in pull requests like any other change.

## Reasons
- Git gives history, reviewable diffs, and branch-and-review workflow for free.
- Humans can read Markdown and YAML without a UI.
- Agent tooling (lint, scripts) gets deterministic paths and simple I/O.

## Alternatives rejected
- SQLite or a document store: invisible to diff, un-reviewable in PRs, extra backup surface.
- Wikis or hosted tools: they drift out of sync with the code and lack commit-level traceability.

## Consequences
- Concurrent edits merge by hand like code; no locking service is provided.
- Large projects later with hundreds of ADRs will need index pages and search, which is fine.
## Summary (العربية)
كل السجلات (القرارات، عمارة النظام، نظام الواجهة، مخطط المشروع) ملفات نصية في Git، لُج
الاستعراض والسجل والدمج لا قاعدة بيانات.
