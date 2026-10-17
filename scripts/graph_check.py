"""Check the architecture graph and the decisions log (protected core).

Usage:
    python scripts/graph_check.py --check   verify everything is consistent
    python scripts/graph_check.py --write   regenerate docs/architecture/graph.md

Exits non-zero on any inconsistency; warnings do not fail the run.
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
GRAPH_PATH = ROOT / "docs" / "architecture" / "graph.yaml"
GRAPH_MD_PATH = ROOT / "docs" / "architecture" / "graph.md"
DECISIONS_DIR = ROOT / "docs" / "decisions"
SRC_PACKAGE = "src"

NODE_KINDS = {"service", "module", "store", "doc", "external"}
NODE_STATUSES = {"implemented", "planned"}
EDGE_KINDS = {"depends_on", "reads", "writes", "calls", "generates", "enforces"}
ID_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
ADR_FILE_PATTERN = re.compile(r"^(\d{4})-.+\.md$")


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def fail(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)


def load_graph(report: Report) -> dict:
    if not GRAPH_PATH.exists():
        report.fail("docs/architecture/graph.yaml is missing")
        return {"schema_version": 1, "project": "factory", "nodes": [], "edges": []}
    try:
        data = yaml.safe_load(GRAPH_PATH.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        report.fail(f"graph.yaml is unreadable: {exc}")
        return {"schema_version": 1, "project": "factory", "nodes": [], "edges": []}
    if not isinstance(data, dict):
        report.fail("graph.yaml must be a mapping")
        return {"schema_version": 1, "project": "factory", "nodes": [], "edges": []}
    return data


def check_schema(data: dict, report: Report) -> tuple[list[dict], list[dict]]:
    if data.get("schema_version") != 1:
        fail_ = report.fail
        fail_("schema_version must be the integer 1")
    if not isinstance(data.get("project"), str) or not data["project"]:
        report.fail("project must be a non-empty string")
    nodes = data.get("nodes") or []
    edges = data.get("edges") or []
    if not isinstance(nodes, list) or not isinstance(edges, list):
        report.fail("nodes and edges must be lists")
        return [], []
    return nodes, edges


def check_nodes(nodes: list[dict], report: Report) -> dict[str, dict]:
    seen: dict[str, dict] = {}
    for node in nodes:
        node_id = node.get("id")
        if not isinstance(node_id, str) or not ID_PATTERN.match(node_id):
            report.fail(
                f"node id {node_id!r} must be lowercase letters, digits, hyphens"
            )
            continue
        if node_id in seen:
            report.fail(f"duplicate node id {node_id!r}")
            continue
        seen[node_id] = node
        if node.get("kind") not in NODE_KINDS:
            report.fail(f"node {node_id}: kind must be one of {sorted(NODE_KINDS)}")
        status = node.get("status")
        if status not in NODE_STATUSES:
            report.fail(
                f"node {node_id}: status must be one of {sorted(NODE_STATUSES)}"
            )
        path = node.get("path")
        if status == "implemented":
            if not isinstance(path, str) or not path:
                report.fail(f"node {node_id}: implemented nodes need a path")
            elif node.get("kind") == "store":
                store_dir = ROOT / path
                store_dir.mkdir(parents=True, exist_ok=True)
            elif not (ROOT / path).exists():
                report.fail(f"node {node_id}: path {path!r} does not exist")
        elif path:
            report.fail(f"node {node_id}: planned nodes must not carry a path")
    return seen


def check_edges(edges: list[dict], node_ids: set[str], report: Report) -> None:
    for edge in edges:
        label = f"edge {edge.get('from')}->{edge.get('to')}"
        if edge.get("from") not in node_ids:
            report.fail(f"{label}: unknown 'from' node")
        if edge.get("to") not in node_ids:
            report.fail(f"{label}: unknown 'to' node")
        if edge.get("kind") not in EDGE_KINDS:
            report.fail(f"{label}: kind must be one of {sorted(EDGE_KINDS)}")
        if edge.get("status") not in NODE_STATUSES:
            report.fail(f"{label}: status must be one of {sorted(NODE_STATUSES)}")


def module_paths(nodes: list[dict]) -> dict[str, str]:
    """Map filesystem paths of implemented .py nodes to their node ids."""
    return {
        node["path"]: node["id"]
        for node in nodes
        if node.get("status") == "implemented"
        and str(node.get("path", "")).endswith(".py")
    }


def derive_import_edges(
    report: Report, nodes_by_path: dict[str, str]
) -> set[tuple[str, str]]:
    """Return (from_node, to_node) pairs backed by a real `import factory.*`."""
    modules: dict[str, str] = {}
    src = ROOT / SRC_PACKAGE
    if not src.exists():
        report.fail(f"{SRC_PACKAGE}/ is missing")
        return set()
    for module_file in sorted(src.rglob("*.py")):
        rel = module_file.relative_to(ROOT / SRC_PACKAGE)
        package = ".".join(rel.with_suffix("").parts)
        rel_root = str(module_file.relative_to(ROOT)).replace("\\", "/")
        modules[f"{SRC_PACKAGE}.{package}"] = rel_root

    import_edges: set[tuple[str, str]] = set()
    for package, rel_path in sorted(modules.items()):
        tree = ast.parse(
            (ROOT / rel_path).read_text(encoding="utf-8"), filename=rel_path
        )
        for stmt in ast.walk(tree):
            imported: list[str] = []
            if isinstance(stmt, ast.Import):
                imported = [alias.name for alias in stmt.names]
            elif isinstance(stmt, ast.ImportFrom) and stmt.module and stmt.level == 0:
                imported = [stmt.module]
            for name in imported:
                if not name.startswith(f"{SRC_PACKAGE}."):
                    continue
                target = modules.get(name)
                if target is None or target == rel_path:
                    continue
                target_node = nodes_by_path.get(target)
                if target_node is None:
                    continue
                import_edges.add((package, name))

    declared_depends: dict[tuple[str, str], None] = {}
    graph = yaml.safe_load(GRAPH_PATH.read_text(encoding="utf-8"))
    for edge in graph.get("edges") or []:
        if edge.get("kind") == "depends_on" and edge.get("status") == "implemented":
            declared_depends[(edge.get("from"), edge.get("to"))] = None

    for importer_pkg, imported_pkg in sorted(import_edges):
        importer_node = nodes_by_path.get(modules[importer_pkg])
        if importer_node is None:
            continue
        imported_node = nodes_by_path.get(modules[imported_pkg])
        if (importer_node, imported_node) not in declared_depends:
            report.fail(
                f"undeclared import: {importer_pkg} imports {imported_pkg} "
                f"(node {imported_node}); add an implemented depends_on edge"
            )

    for from_node, to_node in sorted(declared_depends):
        from_path = module_path_of_node(from_node, nodes_by_path)
        to_path = module_path_of_node(to_node, nodes_by_path)
        if from_path is None or to_path is None:
            continue
        pairs_backed = {
            (pkg, name)
            for pkg, name in import_edges
            if modules[pkg] == from_path and modules[name] == to_path
        }
        if not pairs_backed:
            report.warn(
                "declared depends_on edge "
                f"{from_node} -> {to_node} has no matching import"
            )
    return import_edges


PY_PATHS: dict[str, str] = {}


def module_path_of_node(node_id: str, nodes_by_path: dict[str, str]) -> str | None:
    for path, node in nodes_by_path.items():
        if node == node_id and path.endswith(".py"):
            return path
    return None


def parse_adr_frontmatter(path: Path, report: Report) -> dict | None:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"\A---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        report.fail(f"{path.name}: missing frontmatter block")
        return None
    try:
        front = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        report.fail(f"{path.name}: unreadable frontmatter: {exc}")
        return None
    return front


def check_decisions(node_ids: set[str], report: Report) -> None:
    if not DECISIONS_DIR.exists():
        report.fail("docs/decisions is missing")
        return
    seen_ids: dict[str, str] = {}
    for path in sorted(DECISIONS_DIR.glob("*.md")):
        if path.name in {"README.md", "0000-template.md"}:
            continue
        match = ADR_FILE_PATTERN.match(path.name)
        if not match:
            report.fail(f"{path.name}: name must be NNNN-short-title.md")
            continue
        front = parse_adr_frontmatter(path, report)
        if front is None:
            continue
        adr_id = str(front.get("id", ""))
        if adr_id != match.group(1):
            report.fail(
                f"{path.name}: frontmatter id {adr_id!r} does not match the file name"
            )
        if adr_id in seen_ids:
            report.fail(f"{path.name}: duplicate ADR id {adr_id}")
        seen_ids[adr_id] = path.name
        if not str(front.get("title", "")).strip():
            report.fail(f"{path.name}: title is empty")
        if front.get("status") not in {"proposed", "accepted", "superseded"}:
            report.fail(
                f"{path.name}: status must be proposed, accepted, or superseded"
            )
        if str(front.get("date", "")) == "YYYY-MM-DD":
            report.fail(f"{path.name}: date placeholder must be replaced")
        for old_id in front.get("supersedes") or []:
            if str(old_id) not in seen_ids:
                report.fail(f"{path.name}: supersedes unknown ADR id {old_id!r}")
        for node_id in front.get("affects") or []:
            if node_id not in node_ids:
                report.fail(f"{path.name}: affects unknown graph node {node_id!r}")
    for path in sorted(DECISIONS_DIR.glob("*.md")):
        if path.name in {"README.md", "0000-template.md"}:
            continue
        front = parse_adr_frontmatter(path, report)
        if front is None:
            continue
        for old_id in front.get("supersedes") or []:
            if str(old_id) not in seen_ids:
                report.fail(f"{path.name}: supersedes unknown ADR id {old_id!r}")


def mermaid(data: dict) -> str:
    lines = [
        "# Architecture graph",
        "",
        "Generated from `graph.yaml` by `scripts/graph_check.py`. Do not edit by hand;"
        " regenerate with `python scripts/graph_check.py --write`.",
        "",
        "```mermaid",
        "graph LR",
    ]
    for node in data.get("nodes") or []:
        node_id = node["id"].replace("-", "_")
        label = f"{node['id']} · {node.get('kind', 'service')}"
        css = "planned" if node.get("status") == "planned" else "implemented"
        lines.append(f'  {node_id}["{label}"]:::{css}')
    lines.append("  classDef implemented stroke:#2E9E6B,stroke-width:2px;")
    lines.append("  classDef planned stroke:#7B858E,stroke-dasharray:4 3;")
    lines.append("")
    for edge in data.get("edges") or []:
        from_id = edge["from"].replace("-", "_")
        to_id = edge["to"].replace("-", "_")
        status = "|planned|" if edge.get("status") == "planned" else ""
        lines.append(f"  {from_id} -->|{edge['kind']}{status}| {to_id}")
    lines.append("```")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true", help="verify graph records")
    group.add_argument("--write", action="store_true", help="regenerate graph.md")
    args = parser.parse_args()

    report = Report()
    data = load_graph(report)
    nodes, edges = check_schema(data, report)
    nodes_by_id = check_nodes(nodes, report)
    node_ids = set(nodes_by_id)
    check_edges(edges, node_ids, report)
    check_decisions(node_ids, report)

    nodes_by_path = module_paths(nodes)
    derive_import_edges(report, nodes_by_path)

    generated = mermaid(data)
    if args.write:
        GRAPH_MD_PATH.write_text(generated, encoding="utf-8")
    elif GRAPH_MD_PATH.exists():
        committed = GRAPH_MD_PATH.read_text(encoding="utf-8")
        if committed != generated:
            report.fail(
                "docs/architecture/graph.md is stale; run "
                "python scripts/graph_check.py --write and commit the result"
            )
    else:
        report.fail(
            "docs/architecture/graph.md is missing; run scripts/graph_check.py --write"
        )

    for warning in report.warnings:
        print(f"warning: {warning}")
    if report.errors:
        for error in report.errors:
            print(f"error: {error}")
        return 1
    print("graph_check: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
