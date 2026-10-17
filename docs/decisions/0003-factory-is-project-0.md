---
id: "0003"
title: "The Factory is project 0 and obeys its own rules"
status: accepted
date: 2026-10-17
decided_by: human
affects: ["web-app", "orchestrator"]
supersedes: []
superseded_by: null
---
## Context
A factory that imposes checks on other products must prove those checks pass on itself, or the
checks mean nothing.

## Decision
The Factory treats itself as project 0. It carries the same records (manifest-like rules in
AGENTS.md, decisions log, architecture graph, UI system), passes the same checks, and uses the
community stack from 0001 for itself first.

## Reasons
- Self-hosting exposes the pain in the pipeline before any project depends on it.
- The dashboards CI all gates the Factory itself, so the tooling is exercised on every commit.

## Alternatives rejected
- A separate "tools" project without tests: the tooling would rot and real projects would inherit it.

## Consequences
- Changes to checks or records require the Factory's own CI to pass before merge.
## Summary (العربية)
المصنع نفسه هو المشروع صفر: يخضع لنفس القواعد والسجلات والفحوص التي سيفرضها لاحقاً على أي مشروع آخر.
