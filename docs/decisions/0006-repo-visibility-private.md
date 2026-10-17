---
id: "0006"
title: "Repo must be private before real project data enters it"
status: proposed
date: 2026-10-17
decided_by: human
affects: ["registry"]
supersedes: []
superseded_by: null
---
## Context
Rule R3 forbids real project data in the repo, but `data/` is only a local directory. Real project
data could still appear in issue text, CI logs, or a fork once the repo is shared.

## Decision
The owner must set the repository visibility to private on the remote before any real project
data is committed against it. Human action required; the agent cannot and must not touch remote
settings.

## Reasons
- The registry, decisions, and Future manifests include business context that leaks value.
- Private is cheap now and public is irreversible after a leak.

## Alternatives rejected
- Relying on `data/` being git-ignored: ignores GitHub issues, PRs, and CI logs.
- Moving data to a private repository later: the data is already public by then.

## Consequences
- The state is a blocker for the multi-project phase (0004); until then, only test data in `data/`.
## Summary (العربية)
يجب أن يصبح المستودع خاصاً قبل إدخال أي بيانات مشروعة، إجراء يدوي على المالك، ويتوقف التوزيع
أعلى للتقييم العملي.
