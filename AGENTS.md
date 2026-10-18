# AGENTS.md: Private Software Factory, iteration 2 ("Make it real")

Read this whole file before touching anything, then follow it in order.
This English file is authoritative. The Arabic block right below is a reading aid for the owner.
This file replaces the iteration-1 `AGENTS.md`. Record that in ADR 0009 (section 7, Phase A).

## الملخص للمالك (العربية)

**ما الذي حدث في النسخة الأولى؟** بُنيت "هياكل الحوكمة" (كتالوج واجهة من 15 مكوّناً، فحوص تنسيق،
اختبارات تباين ألوان) قبل بناء أي منتج يعمل. الشيء الوحيد الذي يعمل فعلاً هو تسجيل مشروع في ملف YAML.
أما الباقي (Gate، الأزرار المعطّلة، الأمثلة داخل `/ui`) فهو شكل بلا وظيفة، ولهذا شعرتَ أن 90% من الخصائص لا تعمل.
والمفردات (StateLight، LineRail، Shadow، Gate) صعبة الفهم، وهذا سبب أنك لم تعد تفهم الواجهة.

**ما الذي سيتغيّر؟**
1. نبني **شريحة كاملة تعمل من البداية للنهاية** أولاً: طلب ← خطة ← بناء ← فحوص ← مراجعة ← موافقتك على الدمج ← بيئة التطوير ← موافقتك على الإنتاج. وكل ما عدا ذلك يؤجَّل حتى يصل أول طلب إلى "Live".
2. **لا يظهر أي زر أو رقم في الواجهة إلا إذا كان يعمل.** وأي ميزة تُسجَّل "تعمل" فقط إذا أثبتها اختبار.
3. **واجهة جديدة بالكامل** مبنية على نموذج مرئي جاهز (`docs/ui/mockup.html`): صفحة "اليوم" تقول لك فوراً ما الذي ينتظر قرارك، وصفحة الطلب فيها خط سير واضح وصندوق قرارك. ألوان جديدة، كلمات بسيطة، وصفحة "الدليل" تشرح كل شيء.
4. مشروع تجريبي يُنشأ بضغطة واحدة لترى كل الخطوات تعمل خلال دقيقة.
5. النماذج لها ثلاثة أوضاع: **يدوي** (الـ Factory يعطيك النص وأنت تلصق الإجابة من أي AI)، **Ollama محلي**، و**تجريبي مبرمج** للاختبار. هكذا يعمل المصنع اليوم حتى بدون نموذج محلي قوي.
6. الـ CI يبقى، لكنه أمر واحد (`python scripts/check_all.py`) يشغّله المطوّر محلياً وتشغّله GitHub بعد كل push.

**كيف تتأكد أن العمل حقيقي؟** عند النهاية يوجد `docs/FEATURES.md` (جدول: كل ميزة ← هل تعمل ← اسم الاختبار)،
والأمر `python scripts/smoke.py` يمر على كل خطوات النظام عبر الواجهة الحقيقية ويطبع نجاح أو فشل لكل خطوة.

---

## 1. Mission

You are the engineering agent for the Private Software Factory (this repo, "project 0").
The Factory makes every change to a software product (feature, bug fix, anything) pass **one fixed
flow**, under written rules and a committed stack, so all code comes out to the same standard.
Humans approve merges and production releases. The long-term aim is that the Factory takes over
programming itself, so the flow must be real and trustworthy before it is clever.

### 1.1 What the iteration-1 audit found (facts from the repo)

- The only working product feature is: register a project (writes `data/projects/<id>/project.yaml`) and list it.
- `/ui` is a catalog filled with invented sample data (fake changes, fake gate, fake logs). It looks like a product and is not.
- Gate approve/reject buttons render disabled. There is no change page, no request form, no orchestrator,
  no model gateway, no git integration, no deploy step. All of them exist only as `planned` in the graph.
- Visible words are internal jargon: StateLight, LineRail, Gate, EvidenceRow, RefChip, ModeTag,
  "Shadowed", modes manual/shadow/live, "Config errors", "AI roles enabled". The owner cannot read the screen.
- CI checks the Factory's own repo (lint, format, tests, graph, tokens). Nothing explains this to the
  owner, so it reads as noise. It is also unrelated to the per-project "checks" step of the flow
  (that step does not exist yet).
- `docs/architecture/graph.md` contains invalid Mermaid for planned edges (`-->|reads|planned| x`), so
  the graph does not render. Fixed in Phase A (appendix A).

### 1.2 The one-sentence goal of this iteration

A person who has never seen the app can open it, create the demo project, submit a request, and watch
it travel through every step to "Live", approving twice, with every button on every page working.

## 2. Rules

- R1. Human approval for merge and for production stays on by default. Never remove or weaken a gate,
  check, or test to make something pass. Approval can only come from a human click in the web app.
- R2. Protected core: `AGENTS.md`, `.github/workflows/**`, `scripts/**`, the approval-policy validation
  in `src/factory/manifest.py`, and `docs/architecture/protected-core.md`. Change them only where this
  file asks, and record an ADR when you do.
- R3. No secrets, tokens, or real project data in the repo. `data/` is git-ignored.
- R4. Every number the UI shows is computed from data, or says "Not available yet". Never a hard-coded 0.
- R5. If a requirement is ambiguous, pick the simplest option, record it as an ADR with status `proposed`,
  and list it in the report. Do not invent features.
- R6. Same-commit rule: when a change triggers a record (section 8), update the decisions log, graph, or
  UI docs in that same commit.
- R7. Code, identifiers, and commit messages are English. README and UI_SYSTEM each keep an Arabic
  companion (`*.ar.md`); add `GUIDE.ar.md`. Each ADR carries a short Arabic summary section.
- R8. Small commits, each leaving all checks green. Format `type(scope): summary`,
  type in `docs, feat, fix, chore, test, ci`.
- R9. If something blocks you, write it in the report and continue with the remaining items.
- **R10. No dead controls.** A control (button, link, form, tab, number) is rendered only if it works
  today and a test proves it. Planned features are never rendered, not even disabled. They live only in
  the graph as `planned`. No `disabled` attributes, no `href="#"`, no "coming soon".
- **R11. Vertical slice first.** Build the thinnest complete path (request to live) before widening any
  one part. Never polish CSS or add components for a page that has no working action yet.
- **R12. Plain words.** The owner reads every label. Use the vocabulary in section 5.3; never the old
  terms. Name things by what the owner does.
- **R13. Honest reporting.** "Done" means you ran it. The final report states what works, what does not,
  and how each claim was verified. Never write "works" for something no test or run exercised.
- **R14. Model output is data, never a command.** Only commands written in the project manifest by the
  owner are ever executed. Model output may only create or change files inside the change worktree,
  after path and size validation (section 4.5).

## 3. Product definition

### 3.1 Concepts (use these words in code comments and UI)

- **Factory**: this application. One Factory hosts many projects.
- **Project**: one software product. Has principles, a code repository, a dev environment, a production
  environment, decisions, and a graph.
- **Request**: something the owner wants changed. Two types: **Feature** and **Bug fix**. Internally a
  request is a *change* with an id like `c-0001`.
- **Flow**: the one fixed path every request takes. It cannot be skipped or reordered.
- **Role**: a model job. **Planning**, **Execution**, **Review**. Roles use *providers*.
- **Provider**: where a role's answers come from. `manual` (the owner pastes the answer), `ollama`
  (local model server), `demo` (scripted, deterministic; for the demo project and tests).
- **Checks**: commands the owner lists in the project settings (tests, lint). Not the Factory's own CI.
- **Approval**: a human click that lets a request merge, or go to production.

### 3.2 The fixed flow

| # | Step | Who does it | Output (saved in the change folder) | Next |
|---|------|-------------|--------------------------------------|------|
| 1 | Request | owner | `request.md` | Plan |
| 2 | Plan | planning role | `plan.md` (what, which files, risks, which records to update, how to test) | Build |
| 3 | Build | execution role | `build-answer.txt`, `diff.patch`, one commit on branch `change/<id>` | Checks |
| 4 | Checks | machine | `checks.json`, `checks.log` | Review, or Build again if failed (up to `max_attempts`) |
| 5 | Review | review role | `review.md` with verdict `approve` or `changes` plus findings (advice only) | Approval to merge |
| 6 | Approve merge | **owner** | decision in `change.yaml` + audit event | Merge |
| 7 | Dev | machine | `deploy-dev.log` (skipped, with a visible reason, if no dev command) | Approval for production |
| 8 | Approve production | **owner** | decision + audit event | Live |
| 9 | Live | machine | `deploy-prod.log` | end |

Owner actions available on a request page, each working: **Approve merge**, **Approve production**,
**Send back with a note** (returns to Build with the note added to the execution context),
**Cancel request**, **Try this step again** (after a failure or restart), and in manual mode
**Submit answer**.

Review verdict is advice. Only the owner's approval merges. A `changes` verdict is shown prominently
above the approve button, but the button still works.

### 3.3 Change states (closed enum, defined once in `ui_vocab.py`; labels and status kinds in 5.3)

Keep the iteration-1 states and add three: `planning`, `waiting_for_you` (the manual provider is waiting for a
pasted answer), and `interrupted` (a run cut off by an app restart). `draft` now means "request received".
Full list: `draft, planning, planned, implementing, checking, in_review, awaiting_approval, merged,
deployed_dev, awaiting_prod, live, waiting_for_you, interrupted, blocked, failed, cancelled`.
Define legal transitions once in `src/factory/flow.py`; nothing else may set a state.

### 3.4 Roles and providers

- `manual`: the Factory builds the full prompt for the role, shows it in a read-only text box with a
  "Copy prompt" button, and a second text box "Paste the answer" with "Submit answer". The change sits in
  `waiting_for_you`. This makes the Factory usable today with any outside AI.
- `ollama`: POST `{ollama_url}/api/chat` with `{"model": ..., "messages": [...], "stream": false}` and read
  `message.content`. Test connection uses `GET {ollama_url}/api/tags` and checks the configured model is
  listed. Verify both against current Ollama docs if network is available. Default `ollama_url` is
  `http://127.0.0.1:11434`, set in `data/factory.yaml`. Local hardware is slow: default read timeout
  900 s per call, configurable; never stream; the UI shows "Working" with elapsed time.
- `demo`: deterministic scripted answers. Plan returns a short plan that quotes the request title. Build
  returns one file block creating `notes/<change-id>.md` containing the request text. Review returns
  verdict `approve` with one finding. It is labeled "Demo model (scripted)" everywhere it appears.
- Manifest `ai_roles.<role>`: keep `enabled` and `model`; add `provider` (`manual | ollama | demo`,
  default `manual`). `enabled: false` means the role runs in `manual` regardless of provider.
  Today's default (all roles disabled) therefore becomes "all roles manual", which works.
- Test the `ollama` provider with `httpx.MockTransport`; no real server is needed in tests.

### 3.5 Data layout (files, ADR 0008; all under git-ignored `data/`)

```text
data/
  factory.yaml                    global settings (ollama_url, timeouts)
  shared/principles/<category>.md shared principles: security, clean-code, design-patterns
  projects/<id>/
    project.yaml                  the manifest
    principles/<category>.md      security, business, architecture, stack, clean-code, performance
    repo/                         the project's git repo (created by the Factory) unless manifest.repo_path is set
    work/<change-id>/             git worktree for branch change/<change-id>
    changes/<change-id>/          change.yaml + all step artifacts listed in 3.2
    audit.jsonl                   append-only events
```

Manifest additions (all optional with defaults; `schema_version` stays `1`; record in an ADR):
`repo_path: str = ""`, `default_branch: str = "main"`, `checks: list[{name, command}] = []`,
`environments.<dev|prod>.command: str = ""` (`configured` becomes derived: true iff `command` is
non-empty), `protected_paths: list[str] = []`, `limits: {max_files: 30, max_file_kb: 200,
max_attempts: 2}`, `records: {decisions: "docs/decisions", graph: "docs/architecture/graph.yaml"}`.
The approval-policy validator is protected core and must stay unchanged.

Principles live in `data/`, owned by the owner, editable in the UI (they are policy, not code), and
carry a counter: each save increments `principles_version` in the manifest.

### 3.6 Per-change execution rules

- Atomic file writes everywhere (temp file then `os.replace`). Reuse and generalize
  `write_manifest_atomic`.
- Runs execute in a background thread, one at a time per change. State is saved after every step.
  On app start, any change in `planning, implementing, checking, in_review` becomes `interrupted` with the
  reason "The Factory restarted while this step was running", and the page offers "Try this step again".
- Build uses `git worktree add data/projects/<id>/work/<cid> -b change/<cid>` from `default_branch`.
  If the main repo has uncommitted changes, the request is `blocked` with a clear message and no work is done.
- Merge (after approval) is `git merge --no-ff change/<cid>` in the main repo, then the worktree and
  branch are removed. A merge conflict leaves the change `blocked` with the git message shown.
- Dev and production deploy run the manifest command with `cwd` = the project repo, a timeout (default
  600 s), output saved to the log. A non-zero exit sets `failed` and shows the log.
- If a step fails, show the artifact that explains why (log, raw model answer), never a bare "failed".

### 3.7 Which rule wins (principles and decisions)

- Shared principles are a floor. Project principles may add rules or tighten shared ones. A project rule
  that loosens a shared rule is ignored unless an accepted ADR in that project's decisions names the exception.
- Between decisions, an accepted ADR that `supersedes` another replaces it; superseded ADRs are left out of the context.
- The context builder labels every rule block with its source file, and writes `context-sources.json` in the
  change folder listing each principle file (path and content hash) and each ADR id it used. The owner can
  always see what the model was told and why.

## 4. Architecture

The target graph is `docs/architecture/graph.yaml`, delivered alongside this file. Replace the repo's
current graph with it (Phase A). Existing node ids are kept so ADRs 0001-0008 stay valid. Planned nodes
use `target_path` (where they will live); when you implement a node, rename `target_path` to `path`,
flip `status` to `implemented`, and flip its edges, in the same commit. `graph_check.py` stays green at every commit.

### 4.1 Module map (new files under `src/factory/`)

| Node | File | Responsibility |
|------|------|----------------|
| flow | `flow.py` | steps, states, legal transitions, who may trigger each. Pure functions, no I/O |
| orchestrator | `orchestrator.py` | background runner; executes steps; saves state; stops at approvals |
| context-builder | `context_builder.py` | assembles each role's prompt (4.4) |
| model-gateway | `models/` (`gateway.py`, `manual.py`, `ollama.py`, `demo.py`) | one `ask(role, prompt) -> Answer` interface |
| patch-applier | `patch_applier.py` | parse file blocks, validate, write in worktree, commit |
| check-runner | `check_runner.py` | run manifest commands with timeout, capture output |
| approvals | `approvals.py` | accept approvals only in awaiting states; write audit event |
| deployer | `deployer.py` | run dev/prod command |
| git-ops | `git_ops.py` | init, worktree, commit, diff, merge via the `git` CLI (`subprocess`, argument lists, never `shell=True`) |
| records-view | `records_view.py` | list ADRs, load the project's graph for pages (Phase G) |
| demo-project | `demo.py` | create the demo repo and project |

New runtime dependency: `httpx` (for Ollama), recorded in an ADR.

### 4.2 How the pieces connect

The web app calls the orchestrator to start or retry, calls approvals for the owner's buttons, and only
*reads* the change store. The orchestrator is the only writer of change state besides approvals, and
both go through `flow.py`. The check runner and deployer run only commands from the manifest.

### 4.3 Dependencies between code modules

`graph_check.py` verifies imports against declared `depends_on` edges. Keep the code layered:
`flow` imports nothing from the Factory; `web-app` may import everything; engine modules never import `web-app`.

### 4.4 Context builder

Prompt for each role = role instructions + project principles (all six files) + shared principles +
index of decisions (id, title, status) + the project's graph (nodes and edges as text) + file tree
(paths only, capped) + the request (+ plan, diff, check output for later roles; + the owner's note
after "Send back"). Cap total size; when truncating, say so inside the prompt. Save every prompt to the
change folder (`prompt-<step>.md`) so the owner can read exactly what the model was told.

Execution role must answer in this format only:

```text
<<<FILE path/relative/to/repo>>>
full new content of the file
<<<END>>>
```

Full file contents, not diffs (more reliable for small local models). Planning and review answers are Markdown.
Review answers begin with a line `VERDICT: approve` or `VERDICT: changes`.

### 4.5 Validation before writing model output

Reject (fail the step with a visible reason and keep the raw answer in `build-answer.txt`) when: a path is
absolute, contains `..`, targets `.git/`, matches `protected_paths`, resolves outside the worktree after
symlink resolution; the file count or any file size exceeds `limits`; the answer has no file blocks.
On a format failure retry once with a format reminder, then fail.

## 5. UI v2: a new look, plain words

The owner rejected the iteration-1 UI (grey, quiet, jargon, nothing worked). Start the UI over.
**Reference design: `docs/ui/mockup.html`, delivered with this file.** Copy it into the repo and open it in a
browser before writing any template. It shows the two key pages (Today and Request) with the palette,
type, spacing, and wording to use. Match its layout and feel; do not reinterpret it into the iteration-1 look.
This section supersedes ADR 0005 (record in ADR 0010).

### 5.1 Design rules

- **Spend boldness in two places only**: the amber "needs you" rows on Today and the Pipeline on the Request page.
  Everything else stays calm.
- **Look**: light page, deep teal accent for buttons and links, dark teal left rail, rounded panels, comfortable
  16-17 px text, generous spacing. Status colors: needs you amber, working blue, done green, failed red, not
  started grey. A status always shows a text label as well as color. Dark theme follows `prefers-color-scheme`.
- **Type**: system font stack (no external fonts, no CDNs), Arabic-capable fallback, monospace only for ids,
  paths, and code. Sentence case, no all-caps labels, lines under 72 characters.
- **Patterns the owner already knows**: Today works like an inbox. The Request page works like a GitHub pull
  request: result tabs on the left, a sticky decision box on the right. Do not invent new patterns.
- Logical CSS properties only (`margin-inline-start`, not `margin-left`), so Arabic RTL stays possible later.
- **Self-review**: after building each page, open it. If a headless browser is available, take screenshots and
  compare with the mockup; fix differences before moving on. If none is available, say so in the report.

### 5.2 Tokens

`design/tokens.json` is rewritten from the mockup's variables. Light values (derive dark values that keep
contrast): `ink #14211F`, `ink-soft #4A5B58`, `paper #F7F8F6`, `card #FFFFFF`, `line #DCE3E0`,
`accent #0F6B5F`, `need #B26A00`, `need-bg #FFF3DC`, `work #1F6FB2`, `done #2E7D4F`, `fail #B3382F`,
`fail-bg #FCE9E7`, `idle #7C8A87`; radius control 8 px, panel 12 px; rail 232 px; base font size 17 px.
Keep `build_tokens.py` generating `static/tokens.css` and keep `tests/test_tokens_contrast.py` (4.5:1 for text
colors on `card` and `paper`, 3:1 for the status colors on `card`, both themes). Remove the old `shadow`,
`run`, `hold`, `stop` tokens and the IBM Plex font requirement (delete `docs/ui/fonts-todo.md`).

### 5.3 Vocabulary (the left column must not appear anywhere in templates, CSS, or docs)

| Old term (banned) | New term |
|---|---|
| StateLight, light | Status |
| LineRail | Pipeline |
| Gate | Decision box ("Your decision") |
| EvidenceRow, RefChip, ModeTag, FilterBar | removed |
| modes manual/shadow/live, "Shadowed" | removed; provider shown as "You paste" / "Local model" / "Demo model" |
| "Config errors" | "Projects with problems" |
| "AI roles enabled" | "Models connected" |
| "Registry readiness" | "Project status" |
| light kinds `run, hold, stop, shadow` | `work, need, fail` (kinds are `idle, work, need, done, fail`) |

Status labels (closed enum in `ui_vocab.py`; kind in brackets): draft "Request received" [idle]; planning
"Planning" [work]; planned "Plan ready" [work]; implementing "Building" [work]; checking "Checking" [work];
in_review "Being reviewed" [work]; awaiting_approval "Needs your approval to merge" [need]; merged "Merged"
[done]; deployed_dev "On dev" [done]; awaiting_prod "Needs your approval for production" [need]; live "Live"
[done]; waiting_for_you "Waiting for your pasted answer" [need]; interrupted "Stopped by a restart" [need];
blocked "Blocked" [need]; failed "Failed" [fail]; cancelled "Cancelled" [idle].

### 5.4 Pages (six; every control on them works; the left rail shows Today, Projects, Models, Guide)

1. **Today** `/`: headline "N things need you" (or "Nothing needs you"), then "Needs your approval", "Waiting for
   you", "Working now", "Failed", all computed from the change store, rows as in the mockup. Setup checklist
   at the top only while setup is incomplete (computed): *Choose how models answer*, *Add a project*, *Send your
   first request*. "Create demo project" shown while no demo exists.
2. **Projects** `/projects`: list with project status, plus the create form (name, optional ID, stack
   description, repository: "Create a new empty repository" or "Use a folder on this computer", checks one
   per line as `name: command`, dev command, production command). Plain-word errors. Creating a project also
   writes starter principle files (short templates for the six categories) under `data/`, and the project
   page shows their folder path so the owner can edit them in any editor.
3. **Project** `/projects/<id>`: **Requests** (list and "New request") and **Settings** (the same fields as the
   create form; save validates through the manifest model).
4. **Request** `/projects/<id>/requests/<cid>`: as in the mockup. Pipeline (9 steps, who does each), "What
   happens next" sentence, result tabs (Plan, Changes, Checks, Review), sticky Decision box, Activity list.
   Page polls `/projects/<id>/requests/<cid>/status.json` every 2 s while a step is working (about 20 lines of
   vanilla JS; the page stays correct without it). In manual mode the current step shows the Copy box (read-only
   prompt + "Copy prompt") and "Paste the answer" + "Submit answer".
5. **Models** `/models`: three rows (Planning, Execution, Review), each with provider and model name and a
   **Test** button that really calls the provider and answers in words. Ollama URL and timeout editable here,
   saved to `data/factory.yaml`.
6. **Guide** `/guide`: renders `docs/GUIDE.md` (Arabic in `docs/GUIDE.ar.md` via a language link). Explains the
   flow, the words, manual mode, what CI is and is not, and where files live.

Delete the iteration-1 `/ui` catalog (route, template, `tests/test_ui_catalog.py`, catalog lint). Its job is
now done by `docs/ui/mockup.html` plus the real pages.

### 5.5 Components (plain names; Jinja macros + CSS on tokens; add one only when a page uses it)

Status, Pipeline, Decision box, Row, Tabs, Diff view, Log view, Button, Field, Empty state, Error state,
Page header, Copy box, Table.

### 5.6 Copy rules

Buttons say what happens ("Approve merge", "Send request", not "Submit"); the same action keeps the same
word everywhere. Errors say what went wrong and how to fix it, no apology. Empty states invite the next action.
Every page has a one-sentence subtitle that says what the page is for.

## 6. Quality: proving it works

- `scripts/check_all.py` (protected core, new): runs, in order, `ruff check .`, `ruff format --check .`, `pytest`,
  `graph_check --check`, `ui_lint`, `build_tokens --check`, `features_check`, and `smoke`. Stops at the first
  failure and prints one line per step. CI and the README both use only this command. Explain in README
  in two sentences: "CI runs the same checks on GitHub after every push so a broken push is visible. It checks the
  Factory's own code; it is not the same thing as the Checks step that runs on each project's requests."
- `scripts/ui_lint.py` (simplified): fail on `disabled` and on `href="#"` in templates; fail on the words
  "coming soon", "TODO", "lorem"; fail on any banned term from 5.3 in `templates/`, `static/`, `docs/ui/`;
  fail on hex or `rgb()` colors outside `tokens.css`; fail on physical CSS properties (`margin-left`, etc.).
  Drop the old catalog, state-label-literal, raw-px, and letter-spacing rules.
- `graph_check.py` additions (R2, ADR 0009): an implemented node of kind `service`, `module`, or `store` whose
  path is under `src/` or `data/` must list `evidence` (test ids `file::function` that exist under `tests/`);
  `target_path` is allowed only on planned nodes and every planned node has one.
- `docs/FEATURES.md` and `scripts/features_check.py`: a table `id | what the owner can do | where | status |
  test`. `status` is `working` or `not-built`. The check fails if a `working` row names a test function that
  does not exist under `tests/`. Add a row per control the owner can reach.
- `scripts/smoke.py`: starts the app in-process with `TestClient`, temp `data/`, `demo` provider; walks
  create demo project, create request, wait for `awaiting_approval`, approve merge, wait for
  `awaiting_prod`, approve production, expect `live`, and prints `PASS/FAIL` per step. Exit code reflects it.
  It must also be runnable by the owner against a real server with `--base-url http://127.0.0.1:8000`.
- Tests to add (names are suggestions): flow transition table (every legal and illegal move); patch
  validation (each rejection reason in 4.5); check runner (pass, fail, timeout); manual provider round trip;
  `ollama` provider with `httpx.MockTransport` including model-missing and timeout; end-to-end happy path;
  checks fail then retry then `failed`; "Send back with a note" reaches the execution prompt; restart recovery
  to `interrupted`; approvals refuse a click in the wrong state; merge conflict becomes `blocked`; dirty repo
  becomes `blocked`; Today page computed lists; every page returns 200 with and without data; banned terms and dead controls.

## 7. Phases

Each phase ends with: all checks green, the app started and the new part exercised by hand or by `smoke.py`,
and a commit. Do them in order. Do not start phase N+1 with phase N unfinished (R11). Anything not named
in phases A to F waits for phase G.

**Phase A: Reset and truth (docs, no feature code).**
1. ADRs, each with Arabic summary and valid `affects`: 0009 "Iteration 2: vertical slice first; supersedes the
   iteration-1 agent file; graph_check changes" [accepted, decided_by human]; 0010 "UI v2: new look, plain
   words, no dead controls; supersedes 0005" [proposed]; 0011 "Manifest additions, providers, `httpx`"
   [proposed]; 0012 "Execution output is file blocks; model output is data" [proposed]; 0013 "Run state is
   files" [proposed].
2. Replace `docs/architecture/graph.yaml` with the delivered file. Replace `mermaid()` in `scripts/graph_check.py`
   with appendix A; allow the optional `group`, `evidence`, `target_path` fields; add the evidence rule from
   section 6; keep every existing check. Run `--write`; commit `graph.md`.
3. Copy `docs/ui/mockup.html` from the delivered file.
4. Write `docs/GUIDE.md` and `docs/GUIDE.ar.md` (owner-facing, plain words, section 5.4 item 6).
5. Create `docs/FEATURES.md` with the current truth: only "Register a project" and "See registered projects"
   are `working`; every other row `not-built`.
6. README (and `README.ar.md`): a "What is this?" paragraph in plain words and the CI sentence from section 6.
Done when: `graph_check` green, Mermaid parses, no application code changed.

**Phase B: Truth and a new look (remove what does not work).**
1. Delete the `/ui` catalog (route, template, test, lint rules); remove `ModeTag`, the `shadow` kind, the disabled Gate, and all fake sample data.
2. New tokens (5.2), new base layout (rail, page header, rows, buttons, status) matching the mockup, plain
   vocabulary (5.3), left rail: Today, Projects. Today and Projects show only real data (the project list,
   the create form). Other rail items are added as their pages land.
3. Simplify `ui_lint` per section 6; update tests.
Done when: all checks green and the app looks like the mockup with only working controls.

**Phase C: Real projects and models.** Extend the manifest (3.5); repository creation (`git init`, initial commit
with starter `docs/decisions/` and `docs/architecture/graph.yaml`) or use an existing folder; starter principle
files; Project page (Requests list shell, Settings); `git_ops.py`; model gateway with `manual`, `ollama`, `demo`;
Models page with Test buttons.
Done when: a project can be created with a repo, settings saved, and each Test button returns a real result; tests cover it.

**Phase D: The flow, steps 1-3.** `flow.py`, change store, request form and Request page (Pipeline, tabs, Copy
box), orchestrator with background runs and restart recovery, context builder (with 3.7), Plan step, Build step
(patch applier, worktree, commit).
Done when: with the `demo` provider a request reaches `checking` and prompts and diff are visible; in manual
mode the paste round trip works.

**Phase E: The flow, steps 4-9.** Check runner with retry loop, Review step, Decision box and approvals, merge,
dev deploy, production deploy, "Send back with a note", cancel, retry. Audit log and Activity list.
Done when: `scripts/smoke.py` passes end to end and the failure paths in section 6 are tested.

**Phase F: Orientation.** Today page as in the mockup (computed lists, headline, checklist), demo project
button, Guide page, `check_all.py`, CI switched to `check_all.py`.
Done when: a fresh clone, `pip install -e ".[dev]"`, `uvicorn factory.main:app --host 127.0.0.1`, one click on
"Create demo project" and one request reach "Live" with two approvals.

**Phase G (only after F is green; each item is its own commit and ADR where needed):** principles editor in the
UI (bumps `principles_version`); Decisions tab; Graph tab with a vendored, pinned `mermaid.min.js` (LICENSE
beside it, ADR; `mermaid()` moved to a module shared by `graph_check.py` and the web app); then dogfood:
register this repo as a project in manual mode and run one tiny real request, and report what broke without
fixing anything beyond a list.

## 8. When a record is required

- ADR: a new dependency; a manifest schema change; a change to a component boundary or an edge in the
  graph; any exception to a rule; any change to the UI system (tokens, components, enums, vocabulary); any
  change to the protected core.
- Graph update: any new, removed, or renamed node or edge (`graph_check.py` enforces this).
- UI docs update: any change to tokens, components, or enums. Update `docs/ui/UI_SYSTEM.md` and `.ar.md`.
- FEATURES update: any new control or page, in the same commit as its test.

## 9. Out of scope in this iteration (do not build; they stay `planned` or absent)

Authentication and CSRF (ADR 0007: local only, bind to 127.0.0.1), remote Git hosts, containers or
sandboxing beyond section 3.6, multi-user roles, Playwright visual tests, Arabic UI strings (keep logical
CSS properties so RTL stays possible), the Factory editing its own code without a human in the loop,
automatic model selection, streaming model output.

## 10. Definition of done and report

Done means: `python scripts/check_all.py` passes, the app starts, and the owner-goal in 1.2 is demonstrated
by `scripts/smoke.py`. Finish by writing `docs/ITERATION_2_REPORT.md` and `.ar.md` with:

1. **Feature truth table**: copy of `docs/FEATURES.md`, plus how each `working` row was verified.
2. What is deliberately not built.
3. ADRs awaiting owner acceptance (0010-0013 and any new), and screenshots or a statement that none could be taken.
4. Assumptions made (R5), and anything you could not run (for example a real Ollama server) stated plainly.
5. Human to-dos (make the repo private per ADR 0006, `CODEOWNERS`, pull a model into Ollama and set it on the Models page).
6. The output of every check in `check_all.py`.

Then give the owner a short chat summary in Arabic and English.

## Appendix A: replacement for `mermaid()` in `scripts/graph_check.py`

This version produces valid Mermaid (the old one emitted `-->|reads|planned| x`), prefixes node ids so
reserved words like `graph` cannot break the diagram, groups nodes into subgraphs by the optional `group`
field, and draws planned edges dashed. It was parsed successfully with the Mermaid 10 parser.

```python
def mermaid(data: dict) -> str:
    """Render graph.yaml as valid Mermaid: groups as subgraphs, planned items dashed."""
    group_titles = {
        "interface": "Interface (what the owner sees)",
        "engine": "Engine (runs the one fixed flow)",
        "state": "State and records (files, not a database)",
        "projects": "Projects and external tools",
        "quality": "Quality (how we know it works)",
    }

    def ident(value: str) -> str:
        # Prefix avoids Mermaid reserved words (a node called "graph" or "end").
        return "n_" + value.replace("-", "_")

    lines = [
        "# Architecture graph",
        "",
        "Generated from `graph.yaml` by `scripts/graph_check.py`. Do not edit by hand;"
        " regenerate with `python scripts/graph_check.py --write`.",
        "",
        "Solid outline and solid arrow: exists today. Dashed: planned.",
        "",
        "```mermaid",
        "graph LR",
    ]
    nodes = data.get("nodes") or []
    grouped: dict[str, list[dict]] = {}
    for node in nodes:
        grouped.setdefault(node.get("group") or "other", []).append(node)
    for group, members in grouped.items():
        title = group_titles.get(group, group)
        lines.append(f'  subgraph g_{group.replace("-", "_")}["{title}"]')
        for node in members:
            css = "planned" if node.get("status") == "planned" else "implemented"
            name = node.get("name") or node["id"]
            lines.append(f'    {ident(node["id"])}["{name}"]:::{css}')
        lines.append("  end")
    lines.append("  classDef implemented stroke:#2E9E6B,stroke-width:2px;")
    lines.append("  classDef planned stroke:#7B858E,stroke-dasharray:4 3;")
    lines.append("")
    for edge in data.get("edges") or []:
        arrow = "-.->" if edge.get("status") == "planned" else "-->"
        lines.append(
            f"  {ident(edge['from'])} {arrow}|{edge['kind']}| {ident(edge['to'])}"
        )
    lines.append("```")
    lines.append("")
    return "\n".join(lines)
```
