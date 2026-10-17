"""Dashboard, project registration, UI catalog, and health endpoint (project 0)."""

from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path

import yaml
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from factory import ui_vocab
from factory.manifest import validate_manifest

ROOT = Path(__file__).resolve().parents[2]
PROJECTS_DIR = ROOT / "data" / "projects"
APP_DIR = Path(__file__).resolve().parent
ID_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

PROJECTS_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Private Software Factory")
app.mount(
    "/static",
    StaticFiles(directory=str(APP_DIR / "static")),
    name="static",
)
templates = Jinja2Templates(directory=str(APP_DIR / "templates"))

ERROR_MESSAGES: dict[str, str] = {
    "invalid_name": "Enter a valid project name using letters or numbers.",
    "missing_id": "This name has no letters to build an ID from. Give the project an "
    "ID with lowercase letters, numbers, and hyphens, like order-system.",
    "invalid_id": "The ID must use lowercase letters, numbers, and hyphens, like "
    "order-system.",
    "duplicate": "A project with this ID already exists. Choose another ID.",
}


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def load_projects() -> list[dict]:
    """Load every project directory as {directory, manifest | error}.

    Invalid YAML or an invalid manifest never disappears: it becomes an error
    record that renders as ErrorState with the file path and the message.
    """
    records: list[dict] = []
    for path in sorted(PROJECTS_DIR.glob("*/project.yaml")):
        directory = path.parent.name
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except (OSError, yaml.YAMLError) as exc:
            records.append(
                {"directory": directory, "manifest": None, "error": str(exc)}
            )
            continue
        manifest = validate_manifest(data)
        if isinstance(manifest, str):
            records.append(
                {"directory": directory, "manifest": None, "error": manifest}
            )
        else:
            records.append(
                {"directory": directory, "manifest": manifest, "error": None}
            )
    records.sort(key=lambda record: record["directory"])
    return records


def project_stats(records: list[dict]) -> dict:
    """Every number on the dashboard is computed from data (rule R4)."""
    registered = sum(1 for record in records if record["manifest"])
    invalid = sum(1 for record in records if record["error"])
    ai_roles_enabled = sum(
        record["manifest"].roles_enabled() for record in records if record["manifest"]
    )
    return {
        "registered": registered,
        "invalid": invalid,
        "ai_roles_enabled": ai_roles_enabled,
    }


def readiness_of(record: dict) -> str:
    return "invalid" if record["error"] else "registered"


def write_manifest_atomic(path: Path, manifest: dict) -> None:
    """Write project.yaml atomically: temp file then replace."""
    tmp_fd, tmp_name = tempfile.mkstemp(
        dir=str(path.parent), prefix=".project-", suffix=".yaml"
    )
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as file:
            yaml.safe_dump(manifest, file, allow_unicode=True, sort_keys=False)
        os.replace(tmp_name, path)
    except BaseException:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
        raise


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    records = load_projects()
    stats = project_stats(records)
    error_code = request.query_params.get("error")
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "records": records,
            "stats": stats,
            "error_message": ERROR_MESSAGES.get(error_code) if error_code else None,
            "ui_vocab": ui_vocab,
        },
    )


def manifest_dict(
    project_id: str,
    name: str,
    description: str,
    repository: str,
    stack: str,
) -> dict:
    return {
        "schema_version": 1,
        "id": project_id,
        "name": name,
        "description": description,
        "repository": repository,
        "stack": stack,
        "principles_version": None,
        "environments": {
            "dev": {"configured": False},
            "prod": {"configured": False},
        },
        "ai_roles": {
            "planning": {"enabled": False, "model": ""},
            "execution": {"enabled": False, "model": ""},
            "review": {"enabled": False, "model": ""},
        },
        "approval_policy": {
            "human_approval_required_for_merge": True,
            "human_approval_required_for_production": True,
        },
    }


@app.post("/projects")
def create_project(
    name: str = Form(...),
    project_id: str = Form(""),
    description: str = Form(""),
    repository: str = Form(""),
    stack: str = Form(""),
):
    name = name.strip()
    explicit_id = project_id.strip().lower()

    if not name:
        return RedirectResponse("/?error=invalid_name", status_code=303)

    slug = explicit_id or slugify(name)
    if not slug:
        return RedirectResponse("/?error=missing_id", status_code=303)
    if not ID_PATTERN.fullmatch(slug):
        return RedirectResponse("/?error=invalid_id", status_code=303)

    project_dir = PROJECTS_DIR / slug
    resolved_dir = project_dir.resolve()
    resolved_projects = PROJECTS_DIR.resolve()
    if not str(resolved_dir).startswith(str(resolved_projects) + os.sep):
        return RedirectResponse("/?error=invalid_id", status_code=303)

    try:
        project_dir.mkdir()
    except FileExistsError:
        return RedirectResponse("/?error=duplicate", status_code=303)

    write_manifest_atomic(
        project_dir / "project.yaml",
        manifest_dict(
            slug, name, description.strip(), repository.strip(), stack.strip()
        ),
    )
    return RedirectResponse("/", status_code=303)


@app.get("/ui", response_class=HTMLResponse)
def ui_catalog(request: Request):
    # Built in full in the UI system implementation commit.
    return templates.TemplateResponse(
        request=request,
        name="ui/catalog.html",
        context={"mappings": {"readiness": ui_vocab.READINESS}},
    )


@app.get("/health")
def health():
    return {"status": "ok", "service": "private-software-factory"}
