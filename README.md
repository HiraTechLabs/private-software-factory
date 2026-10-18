# Private Software Factory

**What is this?** The Factory is an app that takes every change to a software product — a feature
or a bug fix — through one fixed path: request, plan, build, checks, review, and then two clicks
from you (approve the merge, approve production). You open it in your browser, create a project,
send a request, and watch it travel to "Live". Nothing reaches your `main` branch or production
without a human click. This repository is project 0: it obeys its own rules (see `AGENTS.md`).

CI runs the same checks on GitHub after every push so a broken push is visible. It checks the
Factory's own code; it is not the same thing as the Checks step that runs on each project's
requests.

## Install

Requires Python 3.11+.

```sh
pip install -e ".[dev]"
```

## Run

Bind to 127.0.0.1 only; the MVP has no authentication (ADR 0007):

```sh
uvicorn factory.main:app --host 127.0.0.1
```

Then open `http://127.0.0.1:8000/`. On **Today**, press **Create demo project**, then send a
request and follow it to Live. See `docs/GUIDE.md` for the full walkthrough in plain words.

## Checks

One command runs everything (lint, format, tests, graph, UI, tokens, features, smoke):

```sh
python scripts/check_all.py
```

## Repo layout

```text
AGENTS.md            the binding rules for this repo (read first)
docs/                GUIDE.md, FEATURES.md, decisions/ (ADRs), architecture/ (graph), ui/
design/              design/tokens.json (source of truth for styling)
scripts/             checks: check_all, graph_check, ui_lint, build_tokens, features_check, smoke
src/factory/         app code: main.py, flow.py, orchestrator.py, models/, templates, static
data/                projects, changes, principles, settings (git-ignored)
.github/workflows/   CI
```

Governance lives in `AGENTS.md`, which is authoritative for this repo.
