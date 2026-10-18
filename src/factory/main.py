"""Factory web app: the Today, Projects, Project, Request, Models, and Guide pages."""

from __future__ import annotations

import html
import re
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import quote

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from factory import approvals, orchestrator, store, ui_vocab
from factory.demo import create_demo_project, demo_exists
from factory.git_ops import commit_all, init_repo, is_repo
from factory.manifest import Manifest, validate_manifest
from factory.models import gateway

ROOT = store.ROOT
APP_DIR = Path(__file__).resolve().parent
PROJECTS_DIR = store.PROJECTS_DIR
PROJECTS_DIR.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    orchestrator.recover_on_start()
    yield


app = FastAPI(title="Private Software Factory", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(APP_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(APP_DIR / "templates"))

ERROR_MESSAGES: dict[str, str] = {
    "invalid_name": "Enter a project name.",
    "missing_id": "This name has no English letters to build an ID from. Give the "
    "project an ID with lowercase letters, numbers, and hyphens, like order-system.",
    "invalid_id": "The ID must use lowercase letters, numbers, and hyphens, "
    "like order-system.",
    "duplicate": "A project with this ID already exists. Choose another ID.",
    "bad_repo_path": "That folder does not exist on this computer. Check the path.",
    "bad_checks": "Each check must be one line in the form name: command.",
}


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


# ------------------------------------------------------------------ loading
def load_project_records() -> list[dict]:
    records: list[dict] = []
    for path in sorted(PROJECTS_DIR.glob("*/project.yaml")):
        directory = path.parent.name
        data = store.read_yaml(path)
        if data is None:
            records.append(
                {
                    "directory": directory,
                    "manifest": None,
                    "error": "The file is not readable as YAML.",
                }
            )
            continue
        manifest = validate_manifest(data)
        if isinstance(manifest, Manifest):
            records.append(
                {"directory": directory, "manifest": manifest, "error": None}
            )
        else:
            records.append(
                {"directory": directory, "manifest": None, "error": manifest}
            )
    records.sort(key=lambda record: record["directory"])
    return records


def load_project(project_id: str) -> Manifest | None:
    data = store.read_yaml(store.project_yaml(project_id))
    if data is None:
        return None
    manifest = validate_manifest(data)
    return manifest if isinstance(manifest, Manifest) else None


def rail_items(current: str, needs: int = 0) -> list[dict]:
    items = [
        {
            "id": "today",
            "href": "/",
            "label": "Today",
            "badge": needs if needs else None,
        },
        {"id": "projects", "href": "/projects", "label": "Projects", "badge": None},
        {"id": "models", "href": "/models", "label": "Models", "badge": None},
        {"id": "guide", "href": "/guide", "label": "Guide", "badge": None},
    ]
    for item in items:
        item["current"] = item["id"] == current
    return items


def needs_count() -> int:
    count = 0
    for change in store.all_changes():
        if change.get("state") in {
            "awaiting_approval",
            "awaiting_prod",
            "waiting_for_you",
            "interrupted",
        }:
            count += 1
    return count


def base_context(request: Request, current: str, **extra) -> dict:
    context = {
        "request": request,
        "rail_items": rail_items(current, needs_count()),
        "ui_vocab": ui_vocab,
    }
    context.update(extra)
    return context


# ------------------------------------------------------------------ pipeline
def pipeline(change: dict) -> dict:
    state = change.get("state", "draft")
    steps = [step for step, _label, _actor in ui_vocab.FLOW_STEPS]
    if state == "live":
        return {"done": set(steps), "now": None}
    if state == "cancelled":
        return {"done": set(), "now": None}
    current = ui_vocab.STATE_STEP.get(state, "request")
    if state == "waiting_for_you" and change.get("pending_step"):
        current = change["pending_step"]
    index = steps.index(current) if current in steps else 0
    return {"done": set(steps[:index]), "now": steps[index]}


# ------------------------------------------------------------------ Today
@app.get("/", response_class=HTMLResponse)
def today(request: Request):
    records = load_project_records()
    registered = [record for record in records if record["manifest"]]
    changes = store.all_changes()
    groups = {
        "needs_approval": [],
        "waiting": [],
        "working": [],
        "failed": [],
    }
    for change in changes:
        manifest = load_project(change.get("project", ""))
        name = manifest.name if manifest else change.get("project", "")
        row = {"change": change, "project_name": name}
        state = change.get("state")
        if state in {"awaiting_approval", "awaiting_prod"}:
            groups["needs_approval"].append(row)
        elif state in {"waiting_for_you", "interrupted"}:
            groups["waiting"].append(row)
        elif state in {
            "planning",
            "planned",
            "implementing",
            "checking",
            "in_review",
            "merged",
            "deployed_dev",
        }:
            groups["working"].append(row)
        elif state in {"failed", "blocked"}:
            groups["failed"].append(row)
    needs = needs_count()
    setup = {
        "models": store.FACTORY_YAML.exists(),
        "project": bool(registered),
        "request": bool(changes),
    }
    if needs == 0:
        headline = "Nothing needs you"
    elif needs == 1:
        headline = "1 thing needs you"
    else:
        headline = f"{needs} things need you"
    return templates.TemplateResponse(
        request=request,
        name="today.html",
        context=base_context(
            request,
            "today",
            headline=headline,
            groups=groups,
            setup=setup,
            demo_exists=demo_exists(),
        ),
    )


# ------------------------------------------------------------------ Projects
@app.get("/projects", response_class=HTMLResponse)
def projects(request: Request):
    records = load_project_records()
    error_code = request.query_params.get("error")
    return templates.TemplateResponse(
        request=request,
        name="projects.html",
        context=base_context(
            request,
            "projects",
            records=records,
            error_message=ERROR_MESSAGES.get(error_code) if error_code else None,
            form={},
        ),
    )


def parse_checks(text: str) -> tuple[list[dict] | None, str | None]:
    checks: list[dict] = []
    for line in (text or "").splitlines():
        line = line.strip()
        if not line:
            continue
        if ":" not in line:
            return None, "bad_checks"
        name, command = line.split(":", 1)
        name, command = name.strip(), command.strip()
        if not name or not command:
            return None, "bad_checks"
        checks.append({"name": name, "command": command})
    return checks, None


def write_new_project(
    *,
    name: str,
    project_id: str,
    description: str,
    stack: str,
    repo_mode: str,
    repo_path: str,
    checks_text: str,
    dev_command: str,
    prod_command: str,
) -> tuple[bool, str, str]:
    name = name.strip()
    explicit_id = project_id.strip().lower()
    if not name:
        return False, "invalid_name", ""
    slug = explicit_id or slugify(name)
    if not slug:
        return False, "missing_id", ""
    if not store.is_valid_id(slug):
        return False, "invalid_id", ""
    project_dir = store.project_dir(slug).resolve()
    if not str(project_dir).startswith(str(PROJECTS_DIR.resolve())):
        return False, "invalid_id", ""
    if store.project_yaml(slug).exists():
        return False, "duplicate", ""
    checks, error = parse_checks(checks_text)
    if checks is None:
        return False, error or "bad_checks", ""
    use_existing = repo_mode == "existing"
    repo_path = repo_path.strip()
    if use_existing:
        if not repo_path or not Path(repo_path).is_dir():
            return False, "bad_repo_path", ""

    store.ensure_dir(store.project_dir(slug))
    manifest = {
        "schema_version": 1,
        "id": slug,
        "name": name,
        "description": description.strip(),
        "stack": stack.strip(),
        "repo_path": repo_path if use_existing else "",
        "default_branch": "main",
        "checks": checks,
        "environments": {
            "dev": {"command": dev_command.strip()},
            "prod": {"command": prod_command.strip()},
        },
        "protected_paths": [],
        "limits": {"max_files": 30, "max_file_kb": 200, "max_attempts": 2},
        "records": {
            "decisions": "docs/decisions",
            "graph": "docs/architecture/graph.yaml",
        },
        "ai_roles": {
            "planning": {"enabled": False, "provider": "manual", "model": ""},
            "execution": {"enabled": False, "provider": "manual", "model": ""},
            "review": {"enabled": False, "provider": "manual", "model": ""},
        },
        "approval_policy": {
            "human_approval_required_for_merge": True,
            "human_approval_required_for_production": True,
        },
    }
    store.write_yaml_atomic(store.project_yaml(slug), manifest)
    store.write_starter_principles(slug)
    if not use_existing:
        repo = store.repo_dir(slug)
        if not is_repo(repo):
            result = init_repo(repo)
            if not result.ok:
                return False, "bad_repo_path", slug
            readme = (
                f"# {name}\n\n"
                f"{description.strip() or 'A project managed by the Factory.'}\n"
            )
            store.atomic_write_text(repo / "README.md", readme)
            store.atomic_write_text(
                repo / "docs" / "decisions" / "README.md",
                "# Decisions\n\nAdd one Markdown file per decision here.\n",
            )
            store.atomic_write_text(
                repo / "docs" / "architecture" / "graph.yaml",
                f"schema_version: 1\nproject: {slug}\nnodes: []\nedges: []\n",
            )
            commit_all(repo, "chore: start the project")
    return True, "", slug


@app.post("/projects")
def create_project(
    name: str = Form(...),
    project_id: str = Form(""),
    description: str = Form(""),
    stack: str = Form(""),
    repo_mode: str = Form("new"),
    repo_path: str = Form(""),
    checks_text: str = Form(""),
    dev_command: str = Form(""),
    prod_command: str = Form(""),
):
    ok, error, slug = write_new_project(
        name=name,
        project_id=project_id,
        description=description,
        stack=stack,
        repo_mode=repo_mode,
        repo_path=repo_path,
        checks_text=checks_text,
        dev_command=dev_command,
        prod_command=prod_command,
    )
    if not ok:
        return RedirectResponse(f"/projects?error={error}", status_code=303)
    return RedirectResponse(f"/projects/{slug}", status_code=303)


# ------------------------------------------------------------------ Project page
@app.get("/projects/{project_id}", response_class=HTMLResponse)
def project_page(request: Request, project_id: str):
    manifest = load_project(project_id)
    if manifest is None:
        return RedirectResponse("/projects?error=invalid_id", status_code=303)
    changes = sorted(
        store.list_changes(project_id),
        key=lambda change: change.get("created", ""),
        reverse=True,
    )
    return templates.TemplateResponse(
        request=request,
        name="project.html",
        context=base_context(
            request,
            "projects",
            manifest=manifest,
            changes=changes,
            principles_path=_display_path(store.principles_dir(project_id)),
        ),
    )


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(store.ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


@app.post("/projects/{project_id}/settings")
def save_settings(
    project_id: str,
    name: str = Form(...),
    description: str = Form(""),
    stack: str = Form(""),
    repo_path: str = Form(""),
    checks_text: str = Form(""),
    dev_command: str = Form(""),
    prod_command: str = Form(""),
):
    manifest = load_project(project_id)
    if manifest is None:
        return RedirectResponse("/projects?error=invalid_id", status_code=303)
    checks, error = parse_checks(checks_text)
    if checks is None:
        target = f"/projects/{project_id}?error=" + (error or "")
        return RedirectResponse(target, status_code=303)
    data = store.read_yaml(store.project_yaml(project_id)) or {}
    data["name"] = name.strip() or manifest.name
    data["description"] = description.strip()
    data["stack"] = stack.strip()
    data["repo_path"] = repo_path.strip()
    data["checks"] = checks
    data["environments"] = {
        "dev": {"command": dev_command.strip()},
        "prod": {"command": prod_command.strip()},
    }
    store.write_yaml_atomic(store.project_yaml(project_id), data)
    return RedirectResponse(f"/projects/{project_id}", status_code=303)


# ------------------------------------------------------------------ Requests
@app.post("/projects/{project_id}/requests")
def create_request(
    project_id: str,
    title: str = Form(...),
    kind: str = Form("feature"),
    description: str = Form(""),
):
    manifest = load_project(project_id)
    if manifest is None:
        return RedirectResponse("/projects?error=invalid_id", status_code=303)
    title = title.strip()
    if not title:
        target = f"/projects/{project_id}?error=invalid_name"
        return RedirectResponse(target, status_code=303)
    change_id = store.next_change_id(project_id)
    now = store.utc_now()
    change = {
        "id": change_id,
        "project": project_id,
        "title": title,
        "kind": "bug" if kind == "bug" else "feature",
        "description": description.strip(),
        "state": "draft",
        "attempt": 0,
        "created": now,
        "updated": now,
    }
    store.save_change(project_id, change_id, change)
    store.write_artifact(
        project_id,
        change_id,
        "request.md",
        f"# {title}\n\nKind: {change['kind']}\n\n{change['description']}\n",
    )
    store.append_audit(
        project_id,
        {
            "change": change_id,
            "actor": "owner",
            "from": "",
            "to": "draft",
            "note": "request created",
        },
    )
    orchestrator.start(project_id, change_id)
    return RedirectResponse(
        f"/projects/{project_id}/requests/{change_id}", status_code=303
    )


@app.get("/projects/{project_id}/requests/{change_id}", response_class=HTMLResponse)
def request_page(request: Request, project_id: str, change_id: str):
    manifest = load_project(project_id)
    change = store.load_change(project_id, change_id)
    if manifest is None or change is None:
        return RedirectResponse(f"/projects/{project_id}", status_code=303)
    artifacts = {
        "plan": store.read_artifact(project_id, change_id, "plan.md"),
        "diff": store.read_artifact(project_id, change_id, "diff.patch"),
        "checks_log": store.read_artifact(project_id, change_id, "checks.log"),
        "checks_json": store.read_artifact(project_id, change_id, "checks.json"),
        "review": store.read_artifact(project_id, change_id, "review.md"),
        "request": store.read_artifact(project_id, change_id, "request.md"),
        "dev_log": store.read_artifact(project_id, change_id, "deploy-dev.log"),
        "prod_log": store.read_artifact(project_id, change_id, "deploy-prod.log"),
    }
    pending_step = change.get("pending_step")
    manual = None
    if change.get("state") == "waiting_for_you" and pending_step:
        manual = {
            "step": pending_step,
            "prompt": store.read_artifact(
                project_id, change_id, f"prompt-{pending_step}.md"
            ),
            "provider": ui_vocab.provider_label("manual"),
        }
    events = store.read_audit(project_id, change_id)
    tab = request.query_params.get("tab")
    if tab not in {"plan", "changes", "checks", "review"}:
        if artifacts["diff"]:
            tab = "changes"
        elif artifacts["checks_log"]:
            tab = "checks"
        elif artifacts["review"]:
            tab = "review"
        else:
            tab = "plan"
    return templates.TemplateResponse(
        request=request,
        name="request.html",
        context=base_context(
            request,
            "projects",
            manifest=manifest,
            change=change,
            artifacts=artifacts,
            pipe=pipeline(change),
            events=events,
            manual=manual,
            tab=tab,
            provider_label=ui_vocab.provider_label,
        ),
    )


@app.get("/projects/{project_id}/requests/{change_id}/status.json")
def request_status(project_id: str, change_id: str):
    change = store.load_change(project_id, change_id)
    if change is None:
        return JSONResponse({"error": "not found"}, status_code=404)
    state = change.get("state", "draft")
    return JSONResponse(
        {
            "state": state,
            "label": ui_vocab.label_for_state(state),
            "kind": ui_vocab.kind_for_state(state),
            "active": ui_vocab.STATE_KINDS.get(state) == "work",
        }
    )


def _decision(project_id: str, change_id: str, action: str) -> RedirectResponse:
    return RedirectResponse(
        f"/projects/{project_id}/requests/{change_id}?action={action}", status_code=303
    )


@app.post("/projects/{project_id}/requests/{change_id}/approve-merge")
def post_approve_merge(project_id: str, change_id: str):
    approvals.approve_merge(project_id, change_id)
    return _decision(project_id, change_id, "approve-merge")


@app.post("/projects/{project_id}/requests/{change_id}/approve-production")
def post_approve_production(project_id: str, change_id: str):
    approvals.approve_production(project_id, change_id)
    return _decision(project_id, change_id, "approve-production")


@app.post("/projects/{project_id}/requests/{change_id}/send-back")
def post_send_back(project_id: str, change_id: str, note: str = Form("")):
    approvals.send_back(project_id, change_id, note)
    return _decision(project_id, change_id, "send-back")


@app.post("/projects/{project_id}/requests/{change_id}/cancel")
def post_cancel(project_id: str, change_id: str):
    approvals.cancel(project_id, change_id)
    return _decision(project_id, change_id, "cancel")


@app.post("/projects/{project_id}/requests/{change_id}/retry")
def post_retry(project_id: str, change_id: str):
    approvals.retry(project_id, change_id)
    return _decision(project_id, change_id, "retry")


@app.post("/projects/{project_id}/requests/{change_id}/submit-answer")
def post_submit_answer(project_id: str, change_id: str, answer: str = Form("")):
    approvals.submit_answer(project_id, change_id, answer)
    return _decision(project_id, change_id, "submit-answer")


# ------------------------------------------------------------------ Models
@app.get("/models", response_class=HTMLResponse)
def models_page(request: Request):
    settings = store.load_settings()
    roles = []
    for role in ("planning", "execution", "review"):
        roles.append(
            {
                "name": role,
                "label": role.title(),
                "provider": settings.get(f"{role}_provider", "manual"),
                "model": settings.get(f"{role}_model", ""),
            }
        )
    result = request.query_params.get("test_result")
    return templates.TemplateResponse(
        request=request,
        name="models.html",
        context=base_context(
            request, "models", settings=settings, roles=roles, test_result=result
        ),
    )


@app.post("/models")
def save_models(
    ollama_url: str = Form(...),
    model_timeout_seconds: str = Form("900"),
):
    settings = store.load_settings()
    settings["ollama_url"] = ollama_url.strip() or settings["ollama_url"]
    try:
        settings["model_timeout_seconds"] = int(model_timeout_seconds)
    except ValueError:
        pass
    store.save_settings(settings)
    return RedirectResponse("/models", status_code=303)


@app.post("/models/roles/{role}")
def save_role(
    role: str,
    provider: str = Form("manual"),
    model: str = Form(""),
):
    if role not in {"planning", "execution", "review"}:
        return RedirectResponse("/models", status_code=303)
    settings = store.load_settings()
    settings[f"{role}_provider"] = (
        provider if provider in {"manual", "ollama", "demo"} else "manual"
    )
    settings[f"{role}_model"] = model.strip()
    store.save_settings(settings)
    return RedirectResponse("/models", status_code=303)


@app.post("/models/test/{role}")
def test_role(role: str):
    if role not in {"planning", "execution", "review"}:
        return RedirectResponse("/models", status_code=303)
    settings = store.load_settings()
    provider = settings.get(f"{role}_provider", "manual")
    model = settings.get(f"{role}_model", "")
    ok, message = gateway.test_provider(provider, model, settings)
    result = f"{role.title()}: {message}"
    return RedirectResponse(
        f"/models?test_result={quote(result)}&ok={1 if ok else 0}", status_code=303
    )


# ------------------------------------------------------------------ Guide
def _md_inline(value: str) -> str:
    value = html.escape(value)
    value = re.sub(r"`([^`]+)`", r"<code>\1</code>", value)
    value = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", value)
    return re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', value)


def markdown_to_html(text: str) -> str:
    out: list[str] = []
    in_code = False
    in_list = False
    table_rows = 0
    for line in text.splitlines():
        if line.startswith("```"):
            if in_list:
                out.append("</ul>")
                in_list = False
            if table_rows:
                out.append("</tbody></table>")
                table_rows = 0
            out.append("<pre><code>" if not in_code else "</code></pre>")
            in_code = not in_code
            continue
        if in_code:
            out.append(html.escape(line))
            continue
        if line.startswith("|") and line.endswith("|"):
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if all(set(cell) <= {"-", ":"} for cell in cells):
                continue
            if table_rows == 0:
                if in_list:
                    out.append("</ul>")
                    in_list = False
                out.append("<table><tbody>")
            tag = "th" if table_rows == 0 else "td"
            row = "".join(f"<{tag}>{_md_inline(c)}</{tag}>" for c in cells)
            out.append("<tr>" + row + "</tr>")
            table_rows += 1
            continue
        if table_rows:
            out.append("</tbody></table>")
            table_rows = 0
        if line.startswith("- "):
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{_md_inline(line[2:])}</li>")
            continue
        if in_list and not line.startswith("- "):
            out.append("</ul>")
            in_list = False
        if line.startswith("### "):
            out.append(f"<h3>{_md_inline(line[4:])}</h3>")
        elif line.startswith("## "):
            out.append(f"<h2>{_md_inline(line[3:])}</h2>")
        elif line.startswith("# "):
            out.append(f"<h1>{_md_inline(line[2:])}</h1>")
        elif line.strip():
            out.append(f"<p>{_md_inline(line)}</p>")
    if in_list:
        out.append("</ul>")
    if table_rows:
        out.append("</tbody></table>")
    if in_code:
        out.append("</code></pre>")
    return "\n".join(out)


@app.get("/guide", response_class=HTMLResponse)
def guide(request: Request):
    text = store.read_text(ROOT / "docs" / "GUIDE.md")
    lang = request.query_params.get("lang")
    if lang == "ar":
        text = store.read_text(ROOT / "docs" / "GUIDE.ar.md")
    return templates.TemplateResponse(
        request=request,
        name="guide.html",
        context=base_context(
            request, "guide", guide_html=markdown_to_html(text), lang=lang or "en"
        ),
    )


# ------------------------------------------------------------------ demo + health
@app.post("/demo")
def make_demo_project():
    ok, _message = create_demo_project()
    if not ok:
        return RedirectResponse("/?error=demo", status_code=303)
    return RedirectResponse("/projects/demo-shop", status_code=303)


@app.get("/health")
def health():
    return {"status": "ok", "service": "private-software-factory"}
