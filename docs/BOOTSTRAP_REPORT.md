# Bootstrap report

Date: 2026-10-17. Scope: Phase 0 (records) + Phase 1 (tooling and fixes) of AGENTS.md.

## What was done

**Phase 0 — records first**
- `docs/decisions/`: template, README index, and ADRs 0001-0008 (0001-0003 accepted as
  directed; 0004-0008 `proposed`). Each ADR carries an Arabic summary and `affects` values
  checked against the graph.
- `docs/architecture/graph.yaml` with the 12 initial nodes (8 implemented, 4 planned) and all
  initial edges, plus `scripts/graph_check.py`: schema/unique-id/endpoint validation, path
  existence for implemented nodes, AST-derived `factory.*` import edges vs declared
  `depends_on` edges (undeclared import fails; declared-but-unimported edge warns), ADR
  `affects` validation, and Mermaid `graph.md` generation with `--write` / stale `--check`.
- `docs/ui/UI_SYSTEM.md` + `UI_SYSTEM.ar.md`, `design/tokens.json` with exactly the specified
  values, and `docs/ui/fonts-todo.md`.

**Phase 1 — tooling and fixes**
1. Hygiene: `.gitignore` (data/, caches, build output), `pyproject.toml`
   (`fastapi, jinja2, pyyaml, uvicorn, python-multipart, pydantic>=2` + dev extras
   `pytest, httpx, ruff`, ruff config, `requires-python >=3.11`), `README.md` + `README.ar.md`,
   `docs/architecture/protected-core.md` (R2 paths).
2. `src/factory/manifest.py` (pydantic v2): `schema_version: Literal[1]`, id pattern
   `^[a-z0-9]+(-[a-z0-9]+)*$`, all specified fields, and the approval-policy validator: with
   either flag `False`, `waiver_adr` must name an existing accepted ADR in `docs/decisions/`,
   else the manifest is invalid. (Protected core; unchanged behavior otherwise.)
3. `load_projects()` returns a record per project directory with either `manifest` or an
   `error` plus the directory; invalid YAML and invalid manifests render as an ErrorState with
   the file path and the message and are never dropped.
4. Registration: optional `id` field; ASCII slugging from the name when absent; explicit
   "lowercase letters, numbers, and hyphens" error when the slug is empty (e.g. Arabic names);
   `FileExistsError` → duplicate error; `project.yaml` written atomically (temp file +
   `os.replace`); resolved-path containment check inside `data/projects`.
5. Truthful dashboard: stats computed from data (projects registered = valid manifests only,
   config errors, AI roles enabled = sum across manifests); "Pending reviews" card removed;
   hard-coded `REGISTERED` pill and "Configuration created" removed; readiness rendered with
   StateLight (`registered` → done, `invalid` → stop) and labels from `ui_vocab.py`;
   principles render "Not set" when null.
6. UI system implementation: `scripts/build_tokens.py` generates `static/tokens.css` (light +
   `prefers-color-scheme` dark) with `--check`; `static/components.css` and `static/style.css`
   rebuilt on tokens only; 15 component macros in `templates/components/`; route `/ui` renders
   the live catalog (every component, every light kind, every task state, every mode, readiness
   states); `scripts/ui_lint.py` fails on literal colors outside tokens.css, raw px (except
   0/1px and media queries), uppercase transforms, letter-spacing, physical CSS properties,
   and any state label/enum-class literal in templates not coming from `ui_vocab.py`;
   `tests/test_tokens_contrast.py` (4.5:1 text colors vs paper+surface, 3:1 light colors vs
   surface, both themes) and `tests/test_ui_catalog.py` (catalog completeness assertions).
7. Tests: `tests/test_app.py` — valid create, duplicate (+error visible), invalid name,
   Arabic name with explicit ID, Arabic name without ID (+error), invalid YAML → ErrorState,
   approval flag `False` without waiver invalid (and visible as error state), `../x` ID
   rejected, stats computed, `/health`, `/ui`.
8. CI: `.github/workflows/ci.yml` runs `ruff check`, `ruff format --check`, `pytest`,
   `graph_check --check`, `ui_lint`, `build_tokens --check`. `CODEOWNERS` deliberately not
   created (human to-do).

## Check outputs (local run, 2026-10-17)

```text
ruff check .                    → All checks passed!
ruff format --check .           → 28 files already formatted
pytest                          → 25 passed, 1 warning in 1.34s
python scripts/graph_check.py --check → graph_check: ok
python scripts/ui_lint.py       → ui_lint: ok
python scripts/build_tokens.py --check → build_tokens: ok
app start (uvicorn, 127.0.0.1)  → / 200, /ui 200, /health 200 (smoke tested, then stopped)
```

The pytest warning is a deprecation notice from Starlette's bundled `TestClient` (httpx vs
httpx2), not from this repo's code.

## Contrast adjustments

None. Every specified token pair already met the required ratios (lowest: light `hold` on
surface at 3.32; highest required margin was the 4.5 text pairs, all ≥ 5.47).

## Assumptions made (deviations, not rule exceptions)

- `ci.yml` was committed with the Phase 0 docs commit instead of item 8: the graph marks the
  `ci` node as implemented, and its path must exist for `graph_check.py` to stay green from
  the first commit onward. No CI checks ran remotely in between (nothing was pushed).
- In graph.yaml the `manifest` node/edge was committed `planned` and flipped to `implemented`
  in the commit that added the module, so `graph_check.py` is green at every commit. ADRs were
  not needed because the graph's shape did not change (status only).
- Phase 1 items 3, 4, 5 share one commit: loading, registration, and the truthful dashboard
  rewritten templates together (splitting them would leave a template rendering dead fields).
- `scripts/graph_check.py` creates a missing store directory (`data/projects`) rather than
  failing it, because the store is git-ignored data; only code/doc node paths must pre-exist.
- A project directory with no `project.yaml` (yet) is not listed as an error record; only
  unreadable or invalid manifests become ErrorStates (the spec names those two).
- Gate is presentational: approve/reject buttons render disabled because no orchestrator or
  gate flow exists yet (both are `planned` in the graph).

## ADRs awaiting owner acceptance

- 0004 manifest location (data/ today vs project repo later) — needs an owner decision.
- 0005 UI system approach (tokens, closed catalogs) — standing contract to accept.
- 0006 repo must be private before real data — human action.
- 0007 no auth/CSRF, 127.0.0.1 only — revisit before any exposure.
- 0008 records are files, not a database.

## Human to-dos

1. Make the GitHub repository private (ADR 0006) before any real project data appears in
   issues, PRs, or commits.
2. Add `CODEOWNERS` requiring owner review (CI item 8 leaves it as a to-do on purpose).
3. Vendor IBM Plex woff2 files (OFL) under `static/fonts/` and add `@font-face` rules — see
   `docs/ui/fonts-todo.md`. Until then the stacks fall back to system fonts.

## Deferred

- Real gate orchestration, reviews, and change pages (the Change page shell exists only as a
  wireframe in `UI_SYSTEM.md`); Playwright visual regression; Arabic RTL switching;
  fonts vendoring (human to-do above).
