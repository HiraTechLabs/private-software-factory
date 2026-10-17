---
id: "0001"
title: "MVP stack: Python, FastAPI, Jinja2, YAML"
status: accepted
date: 2026-10-17
decided_by: human
affects: ["web-app", "manifest", "ui-system"]
supersedes: []
superseded_by: null
---
## Context
The Factory needs a working local MVP with no cloud resources, no JS framework, and no external
CDNs or font hosts. The stack must be committed so that every later change sticks to it.

## Decision
The MVP stack is Python 3.11+, FastAPI, Jinja2, and YAML (with PyYAML). Static assets are served
by FastAPI from `src/factory/static`. No JavaScript framework.

## Reasons
- FastAPI projects are small, typed, and testable with `TestClient`.
- Jinja2 templates keep the UI server-rendered and inspectable by lint scripts.
- YAML fits handwritten manifests and the architecture graph.
- It runs fully local on a laptop, which is the MVP requirement.

## Alternatives rejected
- Django + templates: heavier than the MVP needs, more conventions than value here.
- A JS SPA: violates "no JS framework" and adds a build step the agent cannot defend.
- SQLite or a document database: records are files first (see 0008), no database needed.

## Consequences
- All tooling (lint, tests, token build) is Python and runs from `pyproject.toml`.
- Adding any dependency later is a change to the stack and needs a new ADR.
## Summary (العربية)
اعتماد حزمة العمل الأساسية للنسخة الأولى المحلية: بايثون 3.11+ مع FastAPI و Jinja2 و YAML،
بدون إطار جافاسكربت وبدون خدمات سحابية.
