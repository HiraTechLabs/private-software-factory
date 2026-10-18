# Feature register

Every control the owner can reach appears here. **status** is `working` only when a test in
`tests/` proves it, or `not-built`. `scripts/features_check.py` fails if a `working` row names a
test function that does not exist.

| id | what you can do | where | status | test |
|----|-----------------|-------|--------|------|
| register-project | Register a project | Projects, create form | working | tests/test_app.py::test_create_project_valid |
| see-projects | See registered projects | Projects list | working | tests/test_app.py::test_stats_are_computed |
