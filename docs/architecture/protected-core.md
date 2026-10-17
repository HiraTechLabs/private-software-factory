# Protected core

These paths carry the binding rules of the Factory. They change only when `AGENTS.md` asks for a
change, and every such change requires an ADR (rule R2):

- `AGENTS.md`
- `.github/workflows/**`
- `scripts/**`
- the approval-policy validation in `src/factory/manifest.py`
- this file (`docs/architecture/protected-core.md`)

What each one protects:

- `AGENTS.md` — the rules themselves (R1-R9, phases, definition of done).
- `.github/workflows/**` — the set of checks that must stay green; gates cannot be removed to
  make a change pass (R1).
- `scripts/**` — the enforcement scripts (`graph_check.py`, `ui_lint.py`, `build_tokens.py`).
- `src/factory/manifest.py` (approval-policy validation) — human approval for merge and
  production defaults to `True` (ADRs 0002, 0007); weakening that validation is forbidden.
- `docs/architecture/protected-core.md` — this list.

Human to-do: add a `CODEOWNERS` file requiring the owner's review (listed in AGENTS.md item 8);
until it exists, rely on the PR review habit.
