# Private Software Factory

One fixed flow for every change, on a committed stack, with humans approving merges and
production. This repository is project 0: it obeys its own rules (see `AGENTS.md`).

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

Then open the dashboard at `http://127.0.0.1:8000/` and the UI catalog at `/ui`.

## Checks

All of these must pass locally and in CI:

```sh
ruff check .
ruff format --check .
pytest
python scripts/graph_check.py --check
python scripts/ui_lint.py
python scripts/build_tokens.py --check
```

## Repo layout

```text
AGENTS.md            the binding rules for this repo (read first)
docs/decisions/      decisions log (ADRs)
docs/architecture/   graph.yaml + generated Mermaid graph.md
docs/ui/             UI_SYSTEM.md (+ .ar.md), fonts-todo.md
design/              design/tokens.json (source of truth for styling)
scripts/             checks: graph_check, ui_lint, build_tokens
src/factory/         app code: main.py, manifest.py, ui_vocab.py, templates, static
data/projects/       registered projects (git-ignored)
.github/workflows/   CI
```

Governance lives in `AGENTS.md`, which is authoritative for this repo.
