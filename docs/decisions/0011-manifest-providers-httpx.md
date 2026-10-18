---
id: "0011"
title: "Manifest additions, providers, httpx"
status: proposed
date: 2026-10-18
decided_by: agent-proposed
affects: ["manifest", "model-gateway", "git-ops", "project-repo", "shared-principles", "project-principles", "check-runner", "deployer"]
supersedes: []
superseded_by: null
---
## Context
The fixed flow needs a real project repository, per-project checks and deploy commands,
provider configuration per role, and principle files that live outside the repo.

## Decision
1. Manifest additions (all optional with defaults; `schema_version` stays 1):
   `repo_path` (use an existing folder instead of a created repo when set), `default_branch`
   ("main"), `checks` (list of `{name, command}`), `environments.<dev|prod>.command`
   (`configured` becomes derived: true iff the command is non-empty), `protected_paths`,
   `limits` (max_files 30, max_file_kb 200, max_attempts 2), and `records` (decisions and
   graph paths inside the project repo).
2. `ai_roles.<role>` keeps `enabled` and `model` and adds `provider`
   (`manual | ollama | demo`, default `manual`). `enabled: false` forces `manual` behavior
   regardless; today's "all disabled" therefore becomes "all manual", which works.
3. Global settings live in `data/factory.yaml` (ollama_url default `http://127.0.0.1:11434`,
   read timeout 900 s per call, never stream).
4. New runtime dependency `httpx` for the Ollama provider (tested with `httpx.MockTransport`).
5. Data layout per project: `principles/` (six starter files), `repo/` (created by the Factory
   with an initial commit containing starter `docs/decisions/` and `docs/architecture/graph.yaml`,
   unless `repo_path` is set), plus the existing change folders.
6. The approval-policy validator (protected core) is unchanged.

## Reasons
- Commands in the manifest are the only executable source (R14); roles need one gateway
  interface with swappable providers; Ollama is the realistic local model path.

## Alternatives rejected
- Provider selection per request instead of per role: more moving parts, no benefit yet.
- Storing principles in the project repo: they are policy, and they must survive repo resets.

## Consequences
- Tests cover each provider and the manifest additions; the Models page Test button exercises
  the real provider.
## Summary (العربية)
توسعة المخطط: مسار المستودع، الفرع الافتراضي، أوامر الفحوص والنشر، المسارات المحمية، والحدود.
لكل دور مزوّد: «يدوي» (تلصق الإجابة) أو Ollama محلي أو تجريبي مبرمج، مع إضافة httpx
لامتحان خادم النماذج المحلي، وملفات مبادئ للمالك داخل data/ ويترقي رقمها عند كل حفظ.
