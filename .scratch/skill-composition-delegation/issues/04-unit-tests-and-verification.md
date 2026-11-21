# Ticket 04: CLI Verification, Tests, and Documentation

Type: task  
Status: open  
Blocked by: 01, 02, 03  

## Question
What unit tests and benchmark assertions verify generalized skill-to-skill invocation?

## Context
- Add unit tests in `tests/test_skills_router.py`:
  - `test_skill_involves_recursive_pipeline_expansion` (A involves B -> pipeline contains both).
  - `test_skill_circular_dependency_protection` (A involves B and B involves A without hanging or crashing).
  - `test_skill_delegates_to_subagent_dispatch` (A delegates_to C -> `subagent_dispatch` generated).
  - `test_transitive_hydration_payload` (hydrates both parent and child instructions).
- Update `README.md` and `CONTEXT_LEDGER.md`.
