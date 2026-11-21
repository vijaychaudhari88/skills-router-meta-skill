# Ticket 04: Full Integration Testing, Benchmarking & Harness Verification

Type: task  
Status: resolved  
Blocked by: 01, 02, 03  

## Question
What unit and benchmark tests ensure `init`, `load`, `offload`, and `session-start` function deterministically without regression?

## Context
We must write comprehensive unit tests in `tests/test_skills_router.py`:
- `test_on_demand_load_and_offload_lifecycle`
- `test_project_init_autodetect_stack`
- `test_session_start_preflight_and_cleanup`
- And verify that all benchmark tests pass.

## Resolution
Expanded test suite in `tests/test_skills_router.py` to 20 unit tests:
- Added `test_on_demand_load_and_offload_lifecycle` testing load, `.loaded.json` tracking, manifest sync, offload, and offload `--all`.
- Added `test_project_init_autodetect_stack` verifying stack detection (Android, Web, Core) and harness setup.
- Added `test_session_start_preflight_and_cleanup` verifying pre-flight receipt and `--cleanup` purge.
- Updated `cmd_benchmark` to universal tests (`test-driven-development`, `chrome-devtools`, `skills-manager`, no-match).
- All 20 tests pass in 0.44s. Benchmark passes 4/4 in < 50ms total (~12ms/query).
