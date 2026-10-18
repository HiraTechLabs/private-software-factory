# Guide

This page explains the Factory in plain words. Learn the flow, the few words you need, how to
answer for the models, and where your files live.

## What the Factory does

You give the Factory a request (a feature or a bug fix). It moves that request along **one fixed
path** — the same path every time — until it is live. Two steps always wait for a click from you:
merging the change, and sending it to production. The Factory is doing the work; you stay the
person who decides.

## The path every request takes

| Step | Who does it | What you get |
|------|-------------|--------------|
| 1. Request | You | The title and description you typed |
| 2. Plan | Planning model | A short plan: what changes, which files, risks, how to test |
| 3. Build | Execution model | The new file contents, committed on a branch |
| 4. Checks | Machine | The commands you listed in the project, with their real output |
| 5. Review | Review model | An opinion: approve, or changes I would make (advice only) |
| 6. Approve merge | **You** | Your click that merges the branch |
| 7. Dev | Machine | The dev command you configured, with its log |
| 8. Approve production | **You** | Your click that allows production |
| 9. Live | Machine | The production command you configured, with its log |

Nothing skips a step. A request cannot jump to Live because a button was clicked; it can only move
where the flow allows.

## The words you will see

- **Status** — where a request is right now, shown as a colored dot **and** a plain label. Needs you
  is amber, working is blue, done is green, failed is red, not started is grey.
- **Pipeline** — the row of nine steps on a request page, so you can see what is done and what is
  next.
- **Your decision** — the box on a request page where you approve, send back, or cancel.
- **Checks** — the commands *you* list in the project settings. These are your project's tests and
  linters, not the Factory's own CI.
- **Provider** — where a model's answer comes from: **You paste** (manual), **Local model**
  (Ollama), or **Demo model** (a scripted model for the demo project and for tests).

## How to answer for the models (manual mode)

If a model role is set to **You paste**, the Factory writes the full prompt for that step and shows
it in a read-only box. Copy it into any AI you like, paste the answer back into the "Paste the
answer" box, and press **Submit answer**. The request waits in "Waiting for your pasted answer"
until you do. This is how the Factory works today, with no local model required.

## What CI is, and what it is not

CI is one command — `python scripts/check_all.py` — that a developer runs locally and GitHub runs
after every push, so a broken push is visible. It checks the **Factory's own code**. It is not the
same thing as the **Checks** step that runs on each project's requests.

## Where your files live

Everything the Factory keeps is under `data/` (excluded from git):

```text
data/
  factory.yaml                    global settings (local model URL, timeouts)
  shared/principles/              shared rules every project follows
  projects/<id>/
    project.yaml                  the project's settings
    principles/                   this project's rules (six files)
    repo/                         the project's git repository
    work/<change-id>/             the branch worktree for one request
    changes/<change-id>/          one request: its request, plan, build, checks, review, logs
    audit.jsonl                   who or what moved each request, and when
```

The principles folders are plain Markdown. Edit them in any editor; every save bumps the project's
principles version.

## Create the demo project

On **Today**, press **Create demo project**. It makes a tiny project that uses the Demo model
(scripted), so you can send a request and watch it travel to Live in about a minute, approving
twice.
