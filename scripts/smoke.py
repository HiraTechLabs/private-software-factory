"""End-to-end smoke test (protected core, ADR 0009).

Walks one request from intake to live through the real web app (the demo project on the
scripted demo model) and prints PASS or FAIL per step. Runs in-process by default; point
it at a running server with `--base-url http://127.0.0.1:8000`.
"""

from __future__ import annotations

import argparse
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def _patch_data_dir() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="factory-smoke-"))
    import factory.store as store

    store.DATA_DIR = tmp
    store.PROJECTS_DIR = tmp / "projects"
    store.PROJECTS_DIR.mkdir(parents=True)
    store.SHARED_PRINCIPLES_DIR = tmp / "shared" / "principles"
    store.FACTORY_YAML = tmp / "factory.yaml"

    import factory.main as main_module

    main_module.PROJECTS_DIR = store.PROJECTS_DIR

    import factory.orchestrator as orchestrator

    orchestrator.SYNC = True


def _wait_for_state(client, project_id, change_id, expected, tries=40):
    for _ in range(tries):
        response = client.get(
            f"/projects/{project_id}/requests/{change_id}/status.json"
        )
        if response.status_code == 200 and response.json().get("state") == expected:
            return True
        time.sleep(0.5)
    return False


def run(client) -> int:
    results: list[tuple[str, bool]] = []

    def step(name: str, ok: bool, detail: str = "") -> None:
        results.append((name, ok))
        print(f"{'PASS' if ok else 'FAIL'}  {name}{('  ' + detail) if detail else ''}")

    health = client.get("/health")
    step("health endpoint answers", health.status_code == 200)

    demo = client.post("/demo")
    step("create demo project", demo.status_code == 200 and "Demo shop" in demo.text)

    created = client.post(
        "/projects/demo-shop/requests",
        data={
            "title": "Add a welcome note",
            "kind": "feature",
            "description": "Please add a note for new visitors.",
        },
    )
    change_id = str(created.url.path).rsplit("/", 1)[-1]
    step("send a request", created.status_code == 200 and change_id.startswith("c-"))

    reached = _wait_for_state(client, "demo-shop", change_id, "awaiting_approval")
    step("wait for merge approval", reached)
    if not reached:
        return 1

    page = client.get(f"/projects/demo-shop/requests/{change_id}")
    step("request page shows the diff", "notes/" in page.text)

    client.post(f"/projects/demo-shop/requests/{change_id}/approve-merge")
    dev = _wait_for_state(client, "demo-shop", change_id, "awaiting_prod")
    step("approve merge, reach dev", dev)
    if not dev:
        return 1

    client.post(f"/projects/demo-shop/requests/{change_id}/approve-production")
    live = _wait_for_state(client, "demo-shop", change_id, "live")
    step("approve production, reach live", live)

    final = client.get(f"/projects/demo-shop/requests/{change_id}")
    step("page says Live", "Live" in final.text)

    failed = [name for name, ok in results if not ok]
    print()
    if failed:
        print(f"smoke: FAIL ({len(failed)} step(s) failed)")
        return 1
    print(f"smoke: PASS ({len(results)} steps)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-url", default="", help="a running server, e.g. http://127.0.0.1:8000"
    )
    args = parser.parse_args()

    import httpx

    if args.base_url:
        with httpx.Client(
            base_url=args.base_url, follow_redirects=True, timeout=60
        ) as client:
            return run(client)

    _patch_data_dir()
    from fastapi.testclient import TestClient

    from factory.main import app

    with TestClient(app, base_url="http://testserver", follow_redirects=True) as client:
        return run(client)


if __name__ == "__main__":
    sys.exit(main())
