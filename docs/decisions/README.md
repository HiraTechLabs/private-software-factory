# Decisions log

Accepted decisions are never edited except to mark them `superseded`. A change of mind is a new
ADR that supersedes the old one. Any exception to a rule is itself an ADR. Each ADR carries a
short Arabic summary. `affects` values are node ids from `docs/architecture/graph.yaml`.

| ID  | Title                                                        | Status   | Date       |
|-----|--------------------------------------------------------------|----------|------------|
| 0000 | Template                                                    | —        | —          |
| 0001 | MVP stack: Python, FastAPI, Jinja2, YAML                    | accepted | 2026-10-17 |
| 0002 | One fixed flow; humans approve merge and production         | accepted | 2026-10-17 |
| 0003 | The Factory is project 0 and obeys its own rules            | accepted | 2026-10-17 |
| 0004 | Manifest location: project repo preferred; data/ today      | proposed | 2026-10-17 |
| 0005 | UI system: tokens, closed catalogs, enforced                | superseded | 2026-10-17 |
| 0006 | Repo must be private before real project data enters it     | proposed | 2026-10-17 |
| 0007 | No auth or CSRF in the MVP; bind to 127.0.0.1 only          | proposed | 2026-10-17 |
| 0008 | Records are files in Git, not a database                    | proposed | 2026-10-17 |
| 0009 | Iteration 2: vertical slice first; agent file replaced      | accepted | 2026-10-18 |
| 0010 | UI v2: new look, plain words, no dead controls              | proposed | 2026-10-18 |
| 0011 | Manifest additions, providers, httpx                        | proposed | 2026-10-18 |
| 0012 | Execution output is file blocks; model output is data       | proposed | 2026-10-18 |
| 0013 | Run state is files                                          | proposed | 2026-10-18 |
