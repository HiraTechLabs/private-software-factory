# Architecture graph

Generated from `graph.yaml` by `scripts/graph_check.py`. Do not edit by hand; regenerate with `python scripts/graph_check.py --write`.

Solid outline and solid arrow: exists today. Dashed: planned.

```mermaid
graph LR
  subgraph g_interface["Interface (what the owner sees)"]
    n_web_app["Factory web app"]:::implemented
    n_ui_system["UI system"]:::implemented
    n_guide["In-app guide"]:::planned
    n_records_view["Records view"]:::planned
    n_demo_project["Demo project"]:::planned
  end
  subgraph g_engine["Engine (runs the one fixed flow)"]
    n_orchestrator["Orchestrator"]:::planned
    n_flow["Flow definition"]:::planned
    n_context_builder["Context builder"]:::planned
    n_model_gateway["Model gateway"]:::planned
    n_patch_applier["Patch applier"]:::planned
    n_check_runner["Project check runner"]:::planned
    n_approvals["Approvals"]:::planned
    n_deployer["Deployer"]:::planned
    n_git_ops["Git operations"]:::planned
  end
  subgraph g_state["State and records (files, not a database)"]
    n_manifest["Manifest model"]:::implemented
    n_registry["Project registry"]:::implemented
    n_change_store["Change store"]:::planned
    n_audit_log["Audit log"]:::planned
    n_shared_principles["Shared principles"]:::planned
    n_project_principles["Project principles"]:::planned
    n_decisions_log["Decisions log"]:::implemented
    n_graph["Architecture graph"]:::implemented
  end
  subgraph g_projects["Projects and external tools"]
    n_project_repo["Project repository"]:::planned
    n_git_server["Git"]:::planned
    n_local_model_server["Local model server"]:::planned
  end
  subgraph g_quality["Quality (how we know it works)"]
    n_checks["Factory self-checks"]:::implemented
    n_ci["CI"]:::implemented
    n_feature_register["Feature register"]:::planned
    n_e2e_smoke["End-to-end smoke test"]:::planned
  end
  classDef implemented stroke:#2E9E6B,stroke-width:2px;
  classDef planned stroke:#7B858E,stroke-dasharray:4 3;

  n_web_app -->|depends_on| n_manifest
  n_web_app -->|reads| n_registry
  n_web_app -->|writes| n_registry
  n_web_app -->|depends_on| n_ui_system
  n_checks -->|enforces| n_graph
  n_checks -->|enforces| n_ui_system
  n_checks -->|enforces| n_decisions_log
  n_ci -->|calls| n_checks
  n_checks -.->|enforces| n_feature_register
  n_ci -.->|calls| n_e2e_smoke
  n_e2e_smoke -.->|calls| n_web_app
  n_web_app -.->|calls| n_orchestrator
  n_web_app -.->|calls| n_approvals
  n_web_app -.->|reads| n_change_store
  n_web_app -.->|reads| n_audit_log
  n_web_app -.->|calls| n_model_gateway
  n_web_app -.->|depends_on| n_records_view
  n_web_app -.->|reads| n_guide
  n_web_app -.->|calls| n_demo_project
  n_demo_project -.->|writes| n_registry
  n_demo_project -.->|depends_on| n_git_ops
  n_records_view -.->|reads| n_project_repo
  n_orchestrator -.->|depends_on| n_flow
  n_orchestrator -.->|reads| n_manifest
  n_orchestrator -.->|writes| n_change_store
  n_orchestrator -.->|writes| n_audit_log
  n_orchestrator -.->|calls| n_context_builder
  n_orchestrator -.->|calls| n_model_gateway
  n_orchestrator -.->|calls| n_patch_applier
  n_orchestrator -.->|calls| n_check_runner
  n_orchestrator -.->|calls| n_deployer
  n_orchestrator -.->|depends_on| n_git_ops
  n_approvals -.->|depends_on| n_flow
  n_approvals -.->|writes| n_change_store
  n_approvals -.->|writes| n_audit_log
  n_approvals -.->|calls| n_orchestrator
  n_context_builder -.->|reads| n_shared_principles
  n_context_builder -.->|reads| n_project_principles
  n_context_builder -.->|reads| n_decisions_log
  n_context_builder -.->|reads| n_project_repo
  n_model_gateway -.->|calls| n_local_model_server
  n_patch_applier -.->|reads| n_manifest
  n_patch_applier -.->|depends_on| n_git_ops
  n_patch_applier -.->|writes| n_project_repo
  n_check_runner -.->|reads| n_manifest
  n_check_runner -.->|reads| n_project_repo
  n_deployer -.->|reads| n_manifest
  n_git_ops -.->|calls| n_git_server
  n_project_repo -.->|depends_on| n_git_server
```
