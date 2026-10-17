# Architecture graph

Generated from `graph.yaml` by `scripts/graph_check.py`. Do not edit by hand; regenerate with `python scripts/graph_check.py --write`.

```mermaid
graph LR
  web_app["web-app · service"]:::implemented
  manifest["manifest · module"]:::planned
  registry["registry · store"]:::implemented
  ui_system["ui-system · doc"]:::implemented
  decisions_log["decisions-log · doc"]:::implemented
  graph["graph · doc"]:::implemented
  checks["checks · service"]:::implemented
  ci["ci · service"]:::implemented
  orchestrator["orchestrator · service"]:::planned
  model_gateway["model-gateway · external"]:::planned
  shared_principles["shared-principles · doc"]:::planned
  git_server["git-server · external"]:::planned
  classDef implemented stroke:#2E9E6B,stroke-width:2px;
  classDef planned stroke:#7B858E,stroke-dasharray:4 3;

  web_app -->|depends_on|planned|| manifest
  web_app -->|reads| registry
  web_app -->|writes| registry
  web_app -->|depends_on| ui_system
  checks -->|enforces| graph
  checks -->|enforces| ui_system
  checks -->|enforces| decisions_log
  ci -->|calls| checks
  orchestrator -->|reads|planned|| manifest
  orchestrator -->|reads|planned|| shared_principles
  orchestrator -->|reads|planned|| decisions_log
  orchestrator -->|reads|planned|| graph
  orchestrator -->|calls|planned|| model_gateway
  orchestrator -->|calls|planned|| git_server
```
