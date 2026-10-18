---
id: "0012"
title: "Execution output is file blocks; model output is data"
status: proposed
date: 2026-10-18
decided_by: agent-proposed
affects: ["model-gateway", "patch-applier", "context-builder", "orchestrator"]
supersedes: []
superseded_by: null
---
## Context
Small local models are unreliable at producing diffs but can reproduce a full file reliably.
The Factory must stay safe while accepting model-written files.

## Decision
1. The execution role answers only in the file-block format:

   <<<FILE path/relative/to/repo>>>
   full new content of the file
   <<<END>>>

   Full file contents, not diffs. Prompts say this explicitly and a failed format triggers one
   retry with a format reminder before the step fails.
2. Validation before writing (each violation fails the step with a visible reason and keeps the
   raw answer in `build-answer.txt`): absolute path, `..` in path, `.git/` target, a path
   matching the manifest `protected_paths`, resolution outside the worktree after symlink
   resolution, file count over `limits.max_files`, single file over `limits.max_file_kb`,
   or no file blocks at all.
3. Model output is data, never a command (R14): only commands written by the owner in the
   manifest are executed. The context builder records every principle file (path + content
   hash) and ADR id used so the owner can see exactly what the model was told.

## Reasons
- Full files are the most robust format for small models; strict path validation closes the
  prompt-injection escape hatch; transparency of prompts keeps the human in control.

## Alternatives rejected
- Free-form diff parsing: brittle with local models.
- Sandboxed command execution of model output: contradicts R14 and invents risk.

## Consequences
- The patch applier, not the model, performs all filesystem writes; tests cover every
  rejection reason above.
## Summary (العربية)
مخرجات منفّذ البناء بصيغة ثابتة: كتل «FILE/END» بمحتوى كامل للملفات وليس فروقاً. كل مسار
يُفحص (مطلق، أو «..»، أو git، أو محمي، أو خارج الشجرة، أو حجم/عدد أكبر من الحدود) قبل الكتابة،
ومخرجات النماذج بيانات لا أوامر — الأوامر من المخطط فقط.
