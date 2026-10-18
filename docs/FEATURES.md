# Feature register

Every control the owner can reach appears here. **status** is `working` only when a test in
`tests/` proves it, or `not-built`. `scripts/features_check.py` fails if a `working` row names a
test function that does not exist.

| id | what you can do | where | status | test |
|----|-----------------|-------|--------|------|
| today-needs | See everything that needs you | Today | working | tests/test_app.py::test_today_lists_computed |
| today-setup | See the setup checklist while setup is incomplete | Today | working | tests/test_app.py::test_today_empty |
| create-demo | Create the demo project in one click | Today | working | tests/test_app.py::test_create_demo_project |
| see-projects | See registered projects | Projects | working | tests/test_app.py::test_projects_page_empty |
| create-project | Create a project, in a new or an existing repository | Projects, create form | working | tests/test_app.py::test_create_project_valid |
| project-settings | Change a project's settings | Project, Settings | working | tests/test_app.py::test_project_settings_saved |
| project-requests | See a project's requests | Project, Requests | working | tests/test_app.py::test_all_pages_return_200 |
| send-request | Send a feature or a bug-fix request | Project, New request | working | tests/test_app.py::test_request_page_reaches_approval |
| request-pipeline | See the pipeline and what happens next | Request | working | tests/test_app.py::test_request_page_reaches_approval |
| result-tabs | Read the plan, changes, checks, and review | Request | working | tests/test_app.py::test_request_page_reaches_approval |
| watch-progress | The page updates itself while a step runs | Request | working | tests/test_app.py::test_status_json |
| approve-merge | Approve merge | Request, Your decision | working | tests/test_orchestrator.py::test_happy_path_demo |
| approve-production | Approve production | Request, Your decision | working | tests/test_orchestrator.py::test_happy_path_demo |
| send-back | Send back with a note | Request, Your decision | working | tests/test_orchestrator.py::test_send_back_note_reaches_prompt |
| cancel-request | Cancel request | Request, Your decision | working | tests/test_orchestrator.py::test_cancel_stops_a_request |
| retry-step | Try this step again | Request, Your decision | working | tests/test_orchestrator.py::test_dirty_repo_blocks_build_then_retry_succeeds |
| submit-answer | Paste a model answer while a role waits for you | Request | working | tests/test_models.py::test_manual_round_trip |
| choose-model | Choose how models answer (provider and model) | Models | working | tests/test_app.py::test_models_role_saved |
| test-model | Test a model connection and read the result in words | Models | working | tests/test_models.py::test_ollama_test_connection_ok |
| local-model-settings | Set the local model address and timeout | Models | working | tests/test_app.py::test_local_model_settings_saved |
| guide | Read the guide in English or Arabic | Guide | working | tests/test_app.py::test_guide_page |
| principles-editor | Edit principles inside the app | Project, Settings | not-built | - |
| decisions-tab | Read decisions inside the app | Project | not-built | - |
| graph-tab | See the project graph inside the app | Project | not-built | - |
| sign-in | Sign in | - | not-built | - |
