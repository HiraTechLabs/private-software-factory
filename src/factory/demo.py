"""Create the demo project: a tiny repo on the demo model, so the flow runs fast."""

from __future__ import annotations

from factory import git_ops, store

DEMO_ID = "demo-shop"
DEMO_NAME = "Demo shop"

DEMO_CHECK = (
    'python -c "import pathlib,sys; '
    "sys.exit(0 if list(pathlib.Path('notes').glob('*.md')) else 1)\""
)
DEMO_CHECK_2 = "python -c \"print('hello from the demo project')\""


def demo_exists() -> bool:
    return store.project_yaml(DEMO_ID).exists()


def _demo_manifest() -> dict:
    return {
        "schema_version": 1,
        "id": DEMO_ID,
        "name": DEMO_NAME,
        "description": "A tiny sample project used to try the whole flow in a minute.",
        "stack": "Plain text files",
        "repo_path": "",
        "default_branch": "main",
        "checks": [
            {"name": "notes file exists", "command": DEMO_CHECK},
            {"name": "python runs", "command": DEMO_CHECK_2},
        ],
        "environments": {"dev": {"command": ""}, "prod": {"command": ""}},
        "protected_paths": [],
        "limits": {"max_files": 30, "max_file_kb": 200, "max_attempts": 2},
        "records": {
            "decisions": "docs/decisions",
            "graph": "docs/architecture/graph.yaml",
        },
        "ai_roles": {
            "planning": {"enabled": True, "provider": "demo", "model": "demo"},
            "execution": {"enabled": True, "provider": "demo", "model": "demo"},
            "review": {"enabled": True, "provider": "demo", "model": "demo"},
        },
        "approval_policy": {
            "human_approval_required_for_merge": True,
            "human_approval_required_for_production": True,
        },
    }


def _seed_repo(project_id: str) -> bool:
    repo = store.repo_dir(project_id)
    if git_ops.is_repo(repo):
        return True
    result = git_ops.init_repo(repo)
    if not result.ok:
        return False
    store.write_starter_principles(project_id)
    store.atomic_write_text(
        repo / "README.md",
        "# Demo shop\n\nA tiny sample project. The Factory writes a notes file.\n",
    )
    store.atomic_write_text(
        repo / "docs" / "decisions" / "0001-start.md",
        '---\nid: "0001"\ntitle: "Start the demo project"\n'
        "status: accepted\ndate: 2026-01-01\nsupersedes: []\nsuperseded_by: null\n"
        "---\n\nThe demo project starts here.\n",
    )
    store.atomic_write_text(
        repo / "docs" / "architecture" / "graph.yaml",
        "schema_version: 1\nproject: demo-shop\nnodes: []\nedges: []\n",
    )
    commit = git_ops.commit_all(repo, "chore: start the demo project")
    return commit.ok


def create_demo_project() -> tuple[bool, str]:
    if demo_exists():
        return False, "The demo project already exists."
    store.ensure_dir(store.project_dir(DEMO_ID))
    store.write_yaml_atomic(store.project_yaml(DEMO_ID), _demo_manifest())
    if not _seed_repo(DEMO_ID):
        return (
            False,
            "The demo project settings were written, but its git repository could "
            "not be created. Check that `git` is installed and on PATH.",
        )
    return True, "The demo project is ready. Open it and send a request."
