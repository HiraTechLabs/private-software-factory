---
id: "0004"
title: "Manifest location: project repo preferred; data/ today"
status: proposed
date: 2026-10-17
decided_by: human
affects: ["manifest", "registry"]
supersedes: []
superseded_by: null
---
## Context
The manifest describes a product's stack, environments, AI roles, and approval policy. It must
live somewhere readable by the Factory. Today projects do not have their own repositories yet, so
the registry writes `project.yaml` under `data/projects/<id>/` in this repo.

## Decision
Target: each project's manifest is read from the project's own repository. Today, until projects
have repos, manifests are read from `data/projects/` (which stays git-ignored per rule R3).
Needs an owner decision before onboarding real projects.

## Reasons
- Reading from the repo makes the manifest versioned with the code it governs.
- `data/` keeps this repo free of real project data during the MVP.

## Alternatives rejected
- Storing manifests in a database: contradicts 0008 (records are files).
- Keeping manifests in this repo after migration: split sources of truth.

## Consequences
- `load_projects()` reads `data/projects/` for now; the switch later is one loader change.
- Any real project data appearing under `data/` while the repo is public would violate 0006.
## Summary (العربية)
الهدف: قراءة ملف المخطط من مستودع المشروع نفسه، ولهذا سيعتمد المصنع في المرحلة الأولى على
`data/projects/` مؤقتاً. القرار النهائي يحتاج موافقة مالك المشروع.
