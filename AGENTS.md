# AGENTS.md: Private Software Factory (project 0)

Read this whole file before touching anything, then follow it in order.
This English file is authoritative. `AGENTS.ar.md` is a reading aid for the owner.

## 1. Mission

You are the engineering agent building the Private Software Factory (this repo).
The Factory makes every change to a software product (feature, bug fix, anything) pass one fixed
flow, under written rules and a committed stack, so all code comes out to the same standard.
Humans approve merges and production releases.

The Factory is project 0: it must obey every rule it will later impose on other projects.
In this phase you will (a) create the three records every project carries (decisions log,
architecture graph, UI system) before any code change, (b) put the checks that enforce them in place,
and (c) fix the issues listed in Phase 1.

## 2. Context

- Stack: Python 3.11+, FastAPI, Jinja2, YAML. Local MVP. No cloud resources, no JS framework,
  no external CDNs or font hosts.
- Target architecture. Shared side: orchestrator, model gateway with three roles (planning,
  execution, review), shared principles (security, clean code, design patterns), Git + CI.
  Per-project side: manifest (`project.yaml`), project principles (business, stack, performance, UI),
  decisions log, architecture graph, codebase, dev and prod environments.
- Out of scope now (do not build; they appear in the graph as `planned`): orchestrator, model
  integration, deployments, authentication, Playwright visual regression.
- Existing code: `src/factory/main.py` (dashboard, project registration, `/health`),
  `templates/index.html`, `static/style.css`.

## 3. Rules

- R1. Human approval for merge and for production stays on by default. Never remove or weaken a
  gate, a check, or a test to make something pass.
- R2. Protected core: `AGENTS.md`, `.github/workflows/**`, `scripts/**`, the approval-policy
  validation in `src/factory/manifest.py`, and `docs/architecture/protected-core.md` itself. Change
  them only where this file asks, and record an ADR when you do.
- R3. No secrets, tokens, or real project data in the repo. `data/` is git-ignored.
- R4. Every number the UI shows is computed from data, or says "Not available yet". Never a
  hard-coded 0.
- R5. If a requirement is ambiguous, pick the simplest option, record it as an ADR with status
  `proposed`, and list it in the report. Do not invent features.
- R6. Same-commit rule: when a change triggers a record (section 6), update the decisions log,
  graph, or UI docs in that same commit.
- R7. Code, identifiers, and commit messages are English. README and UI_SYSTEM.md each get an Arabic
  companion (`*.ar.md`). Each ADR carries a short Arabic summary section.
- R8. Small commits, each leaving all checks green. Format: `type(scope): summary` with type in
  `docs, feat, fix, chore, test, ci`.
- R9. If something blocks you, write it in the report and continue with the remaining items.

## 4. Phase 0: records first

Create these before changing any code, and commit them first as
`docs: add decisions log, architecture graph, and UI system`.

### 4.1 Decisions log: `docs/decisions/`

Files: `0000-template.md`, `README.md` (index table: id, title, status, date), and ADRs below.

Template (copy exactly):

```markdown
---
id: "0000"
title: ""
status: proposed        # proposed | accepted | superseded
date: YYYY-MM-DD
decided_by: human       # human | agent-proposed
affects: []             # node ids from docs/architecture/graph.yaml
supersedes: []
superseded_by: null
---
## Context
## Decision
## Reasons
## Alternatives rejected
## Consequences
## Summary (العربية)
```

Rules: an accepted ADR is never edited except to set `status: superseded` and `superseded_by`.
A change of mind is a new ADR that supersedes the old one. An exception to any rule or principle
is itself an ADR.

Write these ADRs now (status in brackets):

1. 0001 Stack: Python, FastAPI, Jinja2, YAML for the MVP [accepted].
2. 0002 One fixed flow for every change; humans approve merge and production; defaults in the
   manifest [accepted].
3. 0003 The Factory is project 0 and obeys its own rules [accepted].
4. 0004 Manifest location: the registry stores registration; the manifest should be read from the
   project's own repo. Today manifests live in `data/projects/`. [proposed, needs owner decision]
5. 0005 UI system approach: tokens, closed component catalog, closed state vocabulary, enforced by
   lint and tests (section 4.3) [proposed].
6. 0006 Repository visibility: the repo must be private before any real project data enters it
   [proposed, human action required].
7. 0007 No authentication or CSRF protection in the MVP; bind to 127.0.0.1 only; revisit before any
   network exposure or before the Factory can trigger deployments [proposed].
8. 0008 Records (decisions, graph, UI system) are files in Git, not a database [proposed].

### 4.2 Architecture graph: `docs/architecture/graph.yaml`

Schema:

```yaml
schema_version: 1
project: factory
nodes:
  - id: web-app            # lowercase, hyphens
    kind: service          # service | module | store | doc | external
    name: Factory web app
    purpose: ""
    path: src/factory/main.py
    owns: []               # data this node is the source of truth for
    status: implemented    # implemented | planned
edges:
  - from: web-app
    to: manifest
    kind: depends_on       # depends_on | reads | writes | calls | generates | enforces
    note: ""
    status: implemented    # implemented | planned
    decisions: []          # ADR ids
```

Initial nodes: `web-app`, `manifest` (`src/factory/manifest.py`), `registry` (store, `data/projects`),
`ui-system` (`design/`, `src/factory/static`, `src/factory/templates`), `decisions-log`
(`docs/decisions`), `graph` (`docs/architecture`), `checks` (`scripts`), `ci`
(`.github/workflows/ci.yml`); planned: `orchestrator`, `model-gateway`, `shared-principles`,
`git-server`.

Initial edges: web-app depends_on manifest; web-app reads/writes registry; web-app depends_on
ui-system; checks enforces graph, ui-system, decisions-log; ci calls checks; and, all `planned`,
orchestrator reads manifest, shared-principles, decisions-log, graph; orchestrator calls
model-gateway and git-server. Link ADR ids in `decisions`.

Tooling: `scripts/graph_check.py` must

- validate the schema, unique ids, and that every edge endpoint exists;
- check that every implemented node's `path` exists;
- derive real import edges between `factory.*` modules with `ast` and compare with declared
  implemented `depends_on` edges: an undeclared import fails, a declared edge with no import warns;
- check that every id in an ADR's `affects` exists in the graph;
- write `docs/architecture/graph.md` (Mermaid) with `--write`; with `--check` fail if the committed
  file is stale.

### 4.3 UI system: `docs/ui/UI_SYSTEM.md` and `design/tokens.json`

Write `UI_SYSTEM.md` (and `UI_SYSTEM.ar.md`) from the specification below. Sections: Brief,
Principles, Tokens, Type, Layout, Component catalog, State vocabulary, Copy rules, Enforcement.

**Brief.** Users: one operator who owns the Factory, occasionally a reviewer. Jobs: review a change
with its evidence; approve or reject at gates; see what is running, waiting, or broken; trace a
change to its rules, decisions, and architecture. Context: long sessions, dense information.
English now, Arabic (RTL) planned.

**Concept: the Line.** The Factory's flow is the product, so show it. Color means state and nothing
else. Spend boldness in one place, the LineRail. Everything else stays quiet.

**Principles.**
1. State first: every object shows its state with StateLight plus a text label from a closed enum.
2. Evidence first: no claim without a source (rule 4 above).
3. Gates are explicit: approve and reject actions exist only inside the Gate component. Gate shows
   what is being approved, what machines verified, what models said (with ModeTag), and what is
   unverified.
4. Autonomy is visible: each step shows `manual`, `shadow`, or `live`.
5. References are links: rules, decisions, and graph nodes render as RefChip.
6. Quiet chrome: no decorative gradients, shadows, or entrance animations. Motion only answers an
   action. Color never carries meaning alone (always a label).

**Tokens.** Create `design/tokens.json` with exactly these values:

```json
{
  "color": {
    "light": {
      "paper": "#F6F7F8", "surface": "#FFFFFF", "line": "#D9DDE1",
      "ink": "#1C2127", "steel": "#5B6670",
      "run": "#2E9E6B", "hold": "#C27F00", "stop": "#D2433B",
      "shadow": "#5E7FA3", "done": "#5B6670", "idle": "#7B858E",
      "run-text": "#17714A", "hold-text": "#8A5B00",
      "stop-text": "#A82B24", "shadow-text": "#3E5F83"
    },
    "dark": {
      "paper": "#14181C", "surface": "#1B2025", "line": "#2B323A",
      "ink": "#E6E9EC", "steel": "#9AA5AF",
      "run": "#4CC38A", "hold": "#F0B13A", "stop": "#F07167",
      "shadow": "#8FB0D3", "done": "#9AA5AF", "idle": "#6B7680",
      "run-text": "#6FD6A1", "hold-text": "#F0B13A",
      "stop-text": "#F59A92", "shadow-text": "#A9C4E0"
    }
  },
  "font": {
    "sans": "'IBM Plex Sans', 'IBM Plex Sans Arabic', system-ui, sans-serif",
    "mono": "'IBM Plex Mono', ui-monospace, monospace"
  },
  "size": { "xs": "12px", "sm": "13px", "md": "15px", "lg": "18px", "xl": "24px" },
  "space": { "1": "4px", "2": "8px", "3": "12px", "4": "16px", "5": "24px", "6": "32px" },
  "radius": { "control": "4px", "panel": "8px" },
  "layout": { "rail": "220px", "gate": "320px", "measure": "72ch" }
}
```

The primary button is solid `ink` on `paper`; there is no brand accent color.
Default theme follows `prefers-color-scheme`.

**Type.** Sans for prose and labels, mono for identifiers (task ids, rule ids, commit hashes, paths,
logs, diffs). Sentence case everywhere. No all-caps or letter-spaced labels. Line length under 72ch.
Do not link to a font host. Declare the stack above, add a `docs/ui/fonts-todo.md` note to vendor
IBM Plex woff2 files (OFL license) under `static/fonts/`, and fall back to the system stack until then.

**Layout.** Left rail lists only pages that exist (now: Projects; UI catalog). Wireframes:

```
Shell                                   Change page (planned, build the shell only)
+--------+------------------------+     +-----------------------------------------------+
| Rail   | PageHeader             |     | LineRail: intake>plan>build>checks>review>... |
|        +------------------------+     +----------------------------+------------------+
|        | content                |     | Evidence: spec, diff,      | Gate (sticky)    |
+--------+------------------------+     | checks, review report      | approve / reject |
                                        +----------------------------+------------------+
```

**State vocabulary (closed enums, defined once in `src/factory/ui_vocab.py`).**
- Light kinds: `idle, run, hold, stop, shadow, done`.
- Task states and their light: draft idle, planned idle, implementing run, checking run, in_review run,
  awaiting_approval hold, merged done, deployed_dev done, awaiting_prod hold, live done,
  blocked hold, failed stop, cancelled idle.
- Modes: `manual, shadow, live`. `shadow` renders with a dashed outline in the shadow color.
- Registry readiness (used now): `registered` (done), `invalid` (stop).

**Component catalog (closed; each is a Jinja macro in `templates/components/` plus CSS in
`static/components.css`).** StateLight, ModeTag, LineRail, Gate, EvidenceRow, RefChip, DataTable,
FilterBar, DiffView, LogView, Button, Field, EmptyState, ErrorState, PageHeader. Build all with their
states, even those not yet used by a page, so the catalog is complete.

**Copy rules.** Name things by what the user does, not how the system works. Buttons say what
happens ("Create project", not "Submit"); the same action keeps the same word in toasts. Errors say
what went wrong and how to fix it, with no apology. Empty states invite the next action.

**Enforcement** (build in Phase 1): `scripts/build_tokens.py`, `scripts/ui_lint.py`,
`tests/test_ui_catalog.py`, `tests/test_tokens_contrast.py`.

## 5. Phase 1: tooling and fixes

Do these in order, one commit per item or group.

1. **Hygiene.** `.gitignore` adds `data/`, `.ruff_cache/`, `.coverage`, `htmlcov/`, `dist/`,
   `*.egg-info/`. Add `pyproject.toml`: runtime deps `fastapi, jinja2, pyyaml, uvicorn,
   python-multipart, pydantic>=2`; dev deps `pytest, httpx, ruff`; ruff config; `requires-python
   >=3.11`. Add `README.md` and `README.ar.md` (install, run with
   `uvicorn factory.main:app --host 127.0.0.1`, checks, repo layout, link to AGENTS.md).
   Create `docs/architecture/protected-core.md` listing the paths in rule R2.
2. **Manifest model** `src/factory/manifest.py` (pydantic v2): `schema_version: Literal[1]`,
   `id` matching `^[a-z0-9]+(-[a-z0-9]+)*$`, `name`, `description`, `repository`, `stack`,
   `principles_version: str | None = None`, `environments` (dev, prod: `configured: bool`),
   `ai_roles` (planning, execution, review: `enabled: bool`, `model: str`),
   `approval_policy` with the two flags defaulting to `True`. Validator: if either flag is `False`,
   `approval_policy.waiver_adr` must name an existing accepted ADR, otherwise the manifest is invalid.
3. **Loading.** `load_projects()` returns records with `manifest` or `error`, plus directory.
   Invalid YAML or an invalid manifest never disappears: it renders as ErrorState with the file path
   and the message.
4. **Registration.** Add an optional `id` field to the form. If empty, derive from the name by
   ASCII slugging; if that is empty (for example an Arabic name), return an error asking for an ID
   with lowercase letters, numbers, and hyphens. Arabic names are valid in `name`. Create the
   directory exclusively (catch `FileExistsError`), write `project.yaml` atomically (temp file then
   replace), and verify the resolved path stays inside the projects directory. New manifests use
   `principles_version: null`.
5. **Truthful dashboard.** Stats are computed: registered projects (valid only), invalid configs, AI
   roles enabled (sum across manifests). Remove the "Pending reviews" card until reviews exist.
   Remove the hard-coded `REGISTERED` pill and "Configuration created"; use StateLight from
   readiness. Show principles as "Not set" when null.
6. **UI system implementation.** `scripts/build_tokens.py` generates `static/tokens.css` (light,
   dark under `prefers-color-scheme`) from `design/tokens.json`; `--check` fails if stale. Rebuild
   `style.css` and the templates on tokens and components only. Add route `/ui`, the live catalog,
   rendering every component in every state, every light kind, state, and mode.
   `scripts/ui_lint.py` fails on: hex, `rgb()`, `hsl()` outside `tokens.css`; raw `px` for color,
   spacing, radius, or font size (allow `0`, `1px` borders, and media queries); `text-transform:
   uppercase`; non-zero `letter-spacing`; physical properties (`margin-left`, `padding-right`, `left`,
   `right`, `text-align: left|right`, `border-left|right`), which must be logical (`margin-inline-start`,
   `inset-inline`, `text-align: start|end`); and any state label or badge in templates that does not
   come from `ui_vocab.py`. `tests/test_tokens_contrast.py` requires 4.5:1 for `ink, steel` and the
   four `*-text` colors against `surface` and `paper` in both themes, and 3:1 for the six light colors
   against `surface`. If a pair fails, adjust that color minimally and say so in the report.
   `tests/test_ui_catalog.py` renders `/ui` and asserts every component, light kind, state, and mode
   appears, so adding an enum value forces a catalog update.
7. **Tests.** pytest with `TestClient`: create project (valid); duplicate; invalid name; Arabic name
   with explicit ID; Arabic name without ID returns the error; invalid YAML shows ErrorState;
   approval flag `False` without a waiver ADR is invalid; id `../x` rejected; stats are computed;
   `/health`; `/ui` renders.
8. **CI.** `.github/workflows/ci.yml` runs: `ruff check`, `ruff format --check`, `pytest`,
   `python scripts/graph_check.py --check`, `python scripts/ui_lint.py`,
   `python scripts/build_tokens.py --check`. Do not create `CODEOWNERS`; list it as a human to-do.

## 6. When a record is required

- ADR: a new dependency; a manifest schema change; a change to a component boundary or an edge in the
  graph; any exception to a rule or principle; any change to the UI system (tokens, components, enums);
  any change to the protected core.
- Graph update: any new, removed, or renamed node or edge (`graph_check.py` enforces this).
- UI docs update: any change to tokens, components, or enums (build and catalog checks enforce this).

## 7. Definition of done and report

Done means all of these pass locally: `ruff check`, `ruff format --check`, `pytest`,
`python scripts/graph_check.py --check`, `python scripts/ui_lint.py`,
`python scripts/build_tokens.py --check`; the app starts; `/ui` renders; no hard-coded statistics;
the three records exist and reference each other (ADRs name graph nodes; the UI system has an ADR).

Finish by writing `docs/BOOTSTRAP_REPORT.md` and `docs/BOOTSTRAP_REPORT.ar.md` with: what was done,
what was deferred, assumptions made, ADRs awaiting owner acceptance, human to-dos (make the repo
private, add `CODEOWNERS`, vendor fonts), and the output of each check. Then give the owner a short
summary in chat.
