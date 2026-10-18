"""File store: projects, changes, audit events, and global settings (ADRs 0008, 0013).

Everything the Factory keeps is a file under `data/` (git-ignored). Writes are atomic:
a temp file in the same directory, then `os.replace`.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import UTC, datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
PROJECTS_DIR = DATA_DIR / "projects"
SHARED_PRINCIPLES_DIR = DATA_DIR / "shared" / "principles"
FACTORY_YAML = DATA_DIR / "factory.yaml"

ID_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
CHANGE_ID_PATTERN = re.compile(r"^c-\d{4}$")

DEFAULT_SETTINGS: dict = {
    "ollama_url": "http://127.0.0.1:11434",
    "model_timeout_seconds": 900,
    "deploy_timeout_seconds": 600,
    "check_timeout_seconds": 600,
}

PRINCIPLE_CATEGORIES: tuple[str, ...] = (
    "security",
    "business",
    "architecture",
    "stack",
    "clean-code",
    "performance",
)
SHARED_PRINCIPLE_CATEGORIES: tuple[str, ...] = (
    "security",
    "clean-code",
    "design-patterns",
)


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def atomic_write_text(path: Path, text: str) -> None:
    """Write text atomically: temp file in the same directory, then os.replace."""
    ensure_dir(path.parent)
    fd, tmp_name = tempfile.mkstemp(
        dir=str(path.parent), prefix=".tmp-", suffix=path.suffix
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        os.replace(tmp_name, path)
    except BaseException:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
        raise


def write_yaml_atomic(path: Path, data: dict) -> None:
    atomic_write_text(path, yaml.safe_dump(data, allow_unicode=True, sort_keys=False))


def read_yaml(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return None
    return data if isinstance(data, dict) else None


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def is_valid_id(value: str) -> bool:
    return bool(ID_PATTERN.fullmatch(value))


# ---------------------------------------------------------------- project paths
def project_dir(project_id: str) -> Path:
    return PROJECTS_DIR / project_id


def project_yaml(project_id: str) -> Path:
    return project_dir(project_id) / "project.yaml"


def principles_dir(project_id: str) -> Path:
    return project_dir(project_id) / "principles"


def repo_dir(project_id: str) -> Path:
    return project_dir(project_id) / "repo"


def changes_dir(project_id: str) -> Path:
    return project_dir(project_id) / "changes"


def change_dir(project_id: str, change_id: str) -> Path:
    return changes_dir(project_id) / change_id


def work_dir(project_id: str, change_id: str) -> Path:
    return project_dir(project_id) / "work" / change_id


def list_project_ids() -> list[str]:
    if not PROJECTS_DIR.is_dir():
        return []
    return sorted(
        path.name
        for path in PROJECTS_DIR.iterdir()
        if (path / "project.yaml").is_file()
    )


# ---------------------------------------------------------------- change store
def next_change_id(project_id: str) -> str:
    numbers: list[int] = []
    folder = changes_dir(project_id)
    if folder.is_dir():
        for path in folder.iterdir():
            match = re.fullmatch(r"c-(\d+)", path.name)
            if match:
                numbers.append(int(match.group(1)))
    return f"c-{max(numbers, default=0) + 1:04d}"


def change_yaml_path(project_id: str, change_id: str) -> Path:
    return change_dir(project_id, change_id) / "change.yaml"


def save_change(project_id: str, change_id: str, data: dict) -> None:
    write_yaml_atomic(change_yaml_path(project_id, change_id), data)


def load_change(project_id: str, change_id: str) -> dict | None:
    return read_yaml(change_yaml_path(project_id, change_id))


def list_changes(project_id: str) -> list[dict]:
    folder = changes_dir(project_id)
    changes: list[dict] = []
    if not folder.is_dir():
        return changes
    for path in sorted(folder.iterdir()):
        data = read_yaml(path / "change.yaml")
        if isinstance(data, dict):
            data.setdefault("id", path.name)
            changes.append(data)
    return changes


def all_changes() -> list[dict]:
    changes: list[dict] = []
    for project_id in list_project_ids():
        for change in list_changes(project_id):
            change.setdefault("project", project_id)
            changes.append(change)
    return changes


def write_artifact(project_id: str, change_id: str, name: str, text: str) -> None:
    atomic_write_text(change_dir(project_id, change_id) / name, text)


def read_artifact(project_id: str, change_id: str, name: str) -> str:
    return read_text(change_dir(project_id, change_id) / name)


def artifact_exists(project_id: str, change_id: str, name: str) -> bool:
    return (change_dir(project_id, change_id) / name).exists()


def delete_artifact(project_id: str, change_id: str, name: str) -> None:
    path = change_dir(project_id, change_id) / name
    if path.exists():
        path.unlink()


# ---------------------------------------------------------------- audit log
def append_audit(project_id: str, event: dict) -> dict:
    record = {"time": utc_now(), **event}
    path = project_dir(project_id) / "audit.jsonl"
    ensure_dir(path.parent)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


def read_audit(project_id: str, change_id: str | None = None) -> list[dict]:
    path = project_dir(project_id) / "audit.jsonl"
    if not path.exists():
        return []
    events: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if change_id is None or event.get("change") == change_id:
            events.append(event)
    return events


# ---------------------------------------------------------------- global settings
def load_settings() -> dict:
    merged = dict(DEFAULT_SETTINGS)
    data = read_yaml(FACTORY_YAML)
    if data:
        for key, value in data.items():
            if value is not None:
                merged[key] = value
    return merged


def save_settings(settings: dict) -> None:
    write_yaml_atomic(FACTORY_YAML, settings)


# ---------------------------------------------------------------- principles
def write_starter_principles(project_id: str) -> None:
    for category in PRINCIPLE_CATEGORIES:
        path = principles_dir(project_id) / f"{category}.md"
        if path.exists():
            continue
        atomic_write_text(path, _starter_principle(category))


def write_shared_principles() -> None:
    for category in SHARED_PRINCIPLE_CATEGORIES:
        path = SHARED_PRINCIPLES_DIR / f"{category}.md"
        if path.exists():
            continue
        atomic_write_text(path, _starter_principle(category))


def _starter_principle(category: str) -> str:
    title = category.replace("-", " ").title()
    return (
        f"# {title} principles\n\n"
        "Write this project's rules here in plain words. The Factory shows this "
        "file to the models for the planning, build, and review steps. A project "
        "rule may tighten a shared rule; a rule that loosens a shared rule needs "
        "an accepted decision naming the exception.\n"
    )
