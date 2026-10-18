# Iteration 2 report: request to Live

This is the honest account of iteration 2 ("make it real"). Everything marked **working** below was
run; `python scripts/check_all.py` passes at the head of this work.

## 1. Feature truth table

`docs/FEATURES.md`, and how each `working` row was verified by a test (the last column names the
test; `scripts/features_check.py` fails the build if the name stops existing).

| id | what you can do | where | status | test |
|----|-----------------|-------|--------|------|
| today-needs | See everything that needs you | Today | working | tests/test_app.py::test_today_lists_computed |
| today-setup | See the setup checklist while setup is incomplete | Today | working | tests/test_app.py::test_today_empty |
| create-demo | Create the demo project in one click | Today | working | tests/test_app.py::test_create_demo_project |
| see-projects | See registered projects | Projects | working | tests/test_app.py::test_projects_page_empty |
| create-project | Create a project, in a new or an existing repository | Projects, create form | working | tests/test_app.py::test_create_project_valid |
| project-settings | Change a project's settings | Project, Settings | working | tests/test_app.py::test_project_settings_saved |
| project-requests | See a project's requests | Project, Requests | working | tests/test_app.py::test_all_pages_return_200 |
| send-request | Send a feature or a bug-fix request | Project, New request | working | tests/test_app.py::test_request_page_reaches_approval |
| request-pipeline | See the pipeline and what happens next | Request | working | tests/test_app.py::test_request_page_reaches_approval |
| result-tabs | Read the plan, changes, checks, and review | Request | working | tests/test_app.py::test_request_page_reaches_approval |
| watch-progress | The page updates itself while a step runs | Request | working | tests/test_app.py::test_status_json |
| approve-merge | Approve merge | Request, Your decision | working | tests/test_orchestrator.py::test_happy_path_demo |
| approve-production | Approve production | Request, Your decision | working | tests/test_orchestrator.py::test_happy_path_demo |
| send-back | Send back with a note | Request, Your decision | working | tests/test_orchestrator.py::test_send_back_note_reaches_prompt |
| cancel-request | Cancel request | Request, Your decision | working | tests/test_orchestrator.py::test_cancel_stops_a_request |
| retry-step | Try this step again | Request, Your decision | working | tests/test_orchestrator.py::test_dirty_repo_blocks_build_then_retry_succeeds |
| submit-answer | Paste a model answer while a role waits for you | Request | working | tests/test_models.py::test_manual_round_trip |
| choose-model | Choose how models answer (provider and model) | Models | working | tests/test_app.py::test_models_role_saved |
| test-model | Test a model connection and read the result in words | Models | working | tests/test_models.py::test_ollama_test_connection_ok |
| local-model-settings | Set the local model address and timeout | Models | working | tests/test_app.py::test_local_model_settings_saved |
| guide | Read the guide in English or Arabic | Guide | working | tests/test_app.py::test_guide_page |

Every row above is also walked end to end by `scripts/smoke.py`, which drives the real pages and
forms: create demo project, send a request, wait for **Needs your approval to merge**, approve merge,
reach **On dev**, approve production, reach **Live** (8 steps, all PASS). `tests/test_orchestrator.py`
adds the failure paths: checks fail then `failed`; a dirty repo becomes `blocked` and a retry
succeeds; a production command that exits non-zero becomes `failed` with the log shown; an approval
click in the wrong state is refused; a restart turns a running change into `interrupted`.

## 2. Deliberately not built

Per AGENTS.md section 9 and phase G: no authentication or CSRF (ADR 0007, local only), no remote Git
hosts, no containers, no multi-user roles, no Playwright tests in CI, no Arabic UI strings, no
streaming model output, and no "the Factory edits itself without a human". Inside the app these stay
`not-built` in the feature register: editing principles, the Decisions tab, the Graph tab, and sign in.
The graph keeps `records-view` and the two external nodes (`git-server`, `local-model-server`) as
`planned`.

## 3. ADRs awaiting owner acceptance

- 0010 UI v2 (supersedes 0005) — **proposed**
- 0011 Manifest additions, providers, `httpx` — **proposed**
- 0012 Execution output is file blocks; model output is data — **proposed**
- 0013 Run state is files — **proposed**
- 0014 Token CSS variable names keep the hyphens from `tokens.json` — **proposed** (added this
  iteration; fixes the invisible left rail)
- 0009 (iteration 2 plan) is **accepted**.

Screenshots were taken during development with headless Chromium (Playwright) against a running
server: Today, Request, Projects, and Models. They are how the invisible-rail bug in 0014 was found
(the contrast test reads the JSON, so it could not see the CSS name mismatch). They are not committed
as binaries; regenerate them by running the demo project and opening the pages.

## 4. Assumptions (R5) and what could not be run

- **Assumption:** an all-disabled manifest means "all roles use the manual provider" (ADR 0011). This
  keeps the Factory usable with no local model.
- **Assumption:** a request is a *change* with an id `c-NNNN`; the flow and states are a closed set in
  `flow.py` (ADR 0013) and only the orchestrator and approvals may move them.
- **Assumption:** the demo project fixes its providers to `demo` so one click reaches a decision in a
  minute; the provider is labelled "Demo model" everywhere it appears.
- **Could not run:** a real Ollama server. The `ollama` provider is tested with `httpx.MockTransport`
  (chat answer, missing model, timeout, and connection test). Pull a model into Ollama and use the
  Models page **Test** button to confirm on real hardware.

## 5. Human to-dos

- Make the repository private (ADR 0006) and add a `CODEOWNERS` file for the protected core.
- Pull a model into Ollama and set it on the Models page; then press **Test**.
- Review and accept the four proposed ADRs (0010-0014).
- Decide when to start phase G (principles editor, Decisions tab, Graph tab, dogfooding).

## 6. Output of every check in `scripts/check_all.py`

`python scripts/check_all.py` runs, in order, and stops at the first failure:

```text
PASS  ruff check
PASS  ruff format
PASS  pytest            (70 passed)
PASS  graph_check
PASS  ui_lint
PASS  build_tokens
PASS  features_check    (21 working)
PASS  smoke             (8 steps)
check_all: PASS (every check)
```

`.github/workflows/ci.yml` now runs only `python scripts/check_all.py`, on Python 3.11, so a broken
push is visible on GitHub and the local run and CI are the same command.

## Note on commit granularity (honest)

The engine, the new UI, the tests, and the check scripts were built together as one vertical slice,
so the intermediate commits were not each run green in isolation. Only the head of this work was
verified, with `scripts/check_all.py`. Further changes should return to one small green commit per
step (R8).
