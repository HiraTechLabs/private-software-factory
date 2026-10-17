from pathlib import Path
import re
import yaml

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

ROOT = Path(__file__).resolve().parents[2]
PROJECTS_DIR = ROOT / "data" / "projects"
APP_DIR = Path(__file__).resolve().parent

PROJECTS_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Private Software Factory")
app.mount(
    "/static",
    StaticFiles(directory=str(APP_DIR / "static")),
    name="static",
)
templates = Jinja2Templates(directory=str(APP_DIR / "templates"))


def make_slug(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def load_projects():
    projects = []

    for config_path in sorted(PROJECTS_DIR.glob("*/project.yaml")):
        try:
            with config_path.open("r", encoding="utf-8") as file:
                project = yaml.safe_load(file) or {}
            project["directory"] = config_path.parent.name
            projects.append(project)
        except (OSError, yaml.YAMLError):
            continue

    return sorted(projects, key=lambda item: item.get("name", "").lower())


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    projects = load_projects()
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"projects": projects, "error": None},
    )


@app.post("/projects")
def create_project(
    name: str = Form(...),
    description: str = Form(""),
    repository: str = Form(""),
    stack: str = Form(""),
):
    name = name.strip()
    slug = make_slug(name)

    if not name or not slug:
        return RedirectResponse("/?error=invalid_name", status_code=303)

    project_dir = PROJECTS_DIR / slug

    if project_dir.exists():
        return RedirectResponse("/?error=duplicate", status_code=303)

    project_dir.mkdir(parents=True)

    project = {
        "schema_version": 1,
        "id": slug,
        "name": name,
        "description": description.strip(),
        "repository": repository.strip(),
        "stack": stack.strip(),
        "principles_version": "1.0.0",
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

    config_path = project_dir / "project.yaml"

    with config_path.open("w", encoding="utf-8") as file:
        yaml.safe_dump(
            project,
            file,
            allow_unicode=True,
            sort_keys=False,
        )

    return RedirectResponse("/", status_code=303)


@app.get("/health")
def health():
    return {"status": "ok", "service": "private-software-factory"}
