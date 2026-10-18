# Private Software Factory --- Implementation Brief for the Coding Model

## Mission

Implement the next working version of **HiraTechLabs / Private Software
Factory** in the existing repository:

`https://github.com/Hira-TechLabs/private-software-factory`

The latest reviewed commit (`2b5ea605fc3330afa7899ea2be127c2e4e5a26c6`,
"First pillar") added instructions, architecture/decision documents,
graph validation changes, and a visual mockup. It did **not** wire the
mockup into the running application. The runtime still uses the older
Projects dashboard and UI catalog.

Your task is to implement the product in the actual application---not
merely update documentation, add another mockup, or describe what should
be built.

## Primary outcome

A user must be able to open the running application, create or select a
project, submit a change request, and follow a real, truthful workflow
through planning, implementation/build, checks, review, and approval. Do
not pretend that stages have run when they have not.

Build **one complete vertical slice** before expanding the feature set.

## Repository rules

1.  Inspect the current branch, working tree, repository instructions
    (`AGENTS.md` and nested `AGENTS.md`), architecture graph, decisions,
    and tests before editing.
2.  Inspect the existing stack and conventions. The application is
    Python/FastAPI with server-rendered Jinja templates. Keep the
    current architecture unless a concrete blocker requires a change.
3.  Work on a dedicated branch using the repository's naming convention.
    Do not commit directly to `main` unless the repository workflow
    explicitly requires it.
4.  Preserve unrelated user changes. Never reset, overwrite, or delete
    user work.
5.  Implement in the real runtime files under `src/factory/`. Editing
    `docs/ui/mockup.html` alone is not implementation.
6.  Keep documentation and the architecture graph synchronized with
    actual behavior. Do not mark a planned component implemented merely
    because a document or placeholder exists.
7.  Use clear, plain interface language. Avoid internal architecture
    jargon in user-facing screens.
8.  Avoid new frameworks, databases, services, or major dependencies
    unless demonstrably necessary. Follow existing project decisions
    unless they block the required vertical slice; explain any
    deviation.
9.  Never claim a test, command, model call, Git operation, or
    deployment succeeded unless it was actually run and the result
    observed.

## UI requirements

Use `docs/ui/mockup.html` as a **visual reference**, not as production
implementation.

-   Bring the real application UI toward the mockup's calmer, more
    usable layout and visual hierarchy.
-   Replace the old dashboard as appropriate; do not leave the new UI
    hidden in a standalone HTML file.
-   Retire the demo `/ui` catalog from the primary user workflow if that
    matches the accepted project decisions. Update navigation and tests
    consistently.
-   Make the UI usable at ordinary desktop widths and reasonably
    responsive at narrower widths.
-   Reuse existing design tokens and component styles where appropriate;
    avoid duplicating styling systems.
-   Distinguish real data from examples. Never show hard-coded sample
    logs, check results, review gates, or project statuses as live.
-   Every visible interactive control must work or be clearly disabled
    with a useful explanation. No dead buttons, fake links, or forms
    that silently do nothing.
-   Include useful empty, success, and error states where relevant.

## Required vertical slice

Implement the smallest complete, honest workflow that fits the existing
architecture:

1.  **Projects** --- list registered projects and create/select a
    project.
2.  **Requests** --- create a change request for a project. Persist its
    title/description, project, creation time, and current state.
3.  **Plan** --- produce and persist a plan. If no model provider is
    configured, provide a clearly labeled deterministic/manual fallback
    rather than pretending AI generated it.
4.  **Build/implementation** --- run a real, bounded implementation step
    or provide an explicit manual step. If automatic code changes are
    not safely supported, mark the stage as blocked/manual and explain
    why. Never execute model-generated shell commands without validation
    and explicit safety boundaries.
5.  **Checks** --- run genuinely available project checks and record the
    command, result, exit code, and timestamp. If checks cannot run,
    show the exact reason and truthful status.
6.  **Review** --- show the actual plan, change summary, and check
    evidence. Do not invent diffs or evidence.
7.  **Approval gates** --- require explicit human approval before
    consequential Git merge or deployment. If merge/deploy is not
    implemented, mark it unavailable; do not simulate success.
8.  **History** --- persist request state and events/evidence so the
    user can reload or return later without losing the record.

### Scope discipline

A narrow, real end-to-end path is better than many empty pages.
Prioritize one complete request lifecycle over implementing every
planned subsystem. Do not build a broad orchestrator, model gateway,
patch applier, deployment platform, or elaborate plugin system unless
necessary for this vertical slice and safely testable.

## State and truthfulness

-   Define explicit request/stage states, such as `draft`, `planned`,
    `running`, `passed`, `failed`, `blocked`, `awaiting_approval`, and
    `approved`, adapting names to repository conventions.
-   Validate transitions. A request must not jump to `Live` because a
    generic button was clicked.
-   Persist state and meaningful events using the simplest durable
    mechanism consistent with existing decisions. Inspect first; do not
    introduce an unrelated storage layer or second database.
-   Distinguish "not started," "running," "passed," "failed," and "not
    available."
-   If a feature is unconfigured or unsupported, say so in the UI and
    give the user the next actionable step.

## Safety boundaries

-   Treat model output as untrusted data, never trusted commands or
    policy.
-   Do not execute arbitrary shell commands, arbitrary repository paths,
    or model-supplied scripts.
-   Validate project paths and ensure filesystem operations remain
    inside the configured workspace.
-   Keep secrets out of logs and rendered pages.
-   Make Git operations opt-in and explicit. Never push, merge, or
    deploy automatically.
-   Require human approval before merge/deployment.
-   If safe implementation is beyond this iteration, mark it blocked/not
    implemented instead of creating a fake success path.

## Tests and acceptance criteria

Add or update automated tests for actual behavior. At minimum, verify:

-   The app starts and its health endpoint works.
-   Home/projects renders and reflects real registered projects.
-   Project creation validates input and persists a project.
-   A request can be created for a project and remains available after
    reload.
-   Invalid request/stage transitions are rejected.
-   The plan fallback is clearly identified and not mislabeled as AI
    output.
-   Checks record real outcomes and failures are displayed honestly.
-   Approval cannot bypass required preceding stages.
-   Missing configuration/errors are visible and do not crash the app.
-   Navigation has no dead destinations or nonfunctional controls.
-   Tests do not depend on the old `/ui` demo catalog unless
    intentionally retained as development-only.

Run the test suite and lint/type/static checks that the repository
actually defines. Fix regressions introduced by your changes and report
exact commands/results.

## Implementation sequence

1.  Inspect instructions, code, tests, graph, and decisions.
2.  Write a short plan based on the actual code; identify the smallest
    viable data model and lifecycle.
3.  Implement the real UI and vertical slice in the runtime app.
4.  Add persistence, validation, safe execution boundaries, and truthful
    status/evidence.
5.  Add/update tests.
6.  Run checks and fix failures.
7.  Update `docs/architecture/graph.md`, `docs/architecture/graph.yaml`,
    and decision statuses only to reflect what is genuinely implemented.
8.  Update user-facing documentation with run instructions and a short
    usage path.
9.  Review the final diff for accidental changes, fake live data, dead
    controls, unsafe execution, and undocumented behavior.

## Definition of done

The task is **not complete** if it only adds: - another HTML mockup; -
documentation or architecture diagrams; - buttons that only change the
page visually; - hard-coded demo requests/results presented as live; - a
workflow without real persistence, checks, or approval rules; - tests
that only assert that pages render.

The task is complete when the running application supports a real,
tested vertical slice; its interface is materially improved; displayed
statuses and evidence are truthful; and limitations are clearly
identified.

## Final response required from the coding model

When finished, report:

1.  What actually works now in user-facing terms.
2.  The exact workflow the user can try.
3.  Files changed and the purpose of the main changes.
4.  Tests/checks run, with exact outcomes.
5.  Features still blocked, manual, unconfigured, or not implemented.
6.  Required environment variables or setup steps.
7.  Branch and commit created, if any.

Do not claim the entire project is finished if only the vertical slice
is complete.
