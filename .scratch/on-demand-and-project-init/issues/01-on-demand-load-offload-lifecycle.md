# Ticket 01: On-Demand Skill Loading and Offloading Engine

Type: task  
Status: resolved  
Blocked by: none  

## Question
How should `skills-router` load dormant skills into a project on demand and cleanly offload them when finished?

## Context
When an agent or user needs a dormant skill (e.g. `chrome-devtools` or `chisle`), they want to load it into the active project context without manually copying directories.
- `skills-router load <skill_id> [--target <dir>]`: Copies or symlinks the skill from the global catalog into `<project_root>/.agents/skills/<skill_id>/`, marks it loaded in `.agents/skills/.loaded.json`, and rebuilds the project manifest.
- `skills-router offload <skill_id>`: Removes the skill from `.agents/skills/`, updates `.loaded.json`, and syncs.
- `skills-router offload --all` (or `unload --all`): Cleans up all temporarily staged skills in one command.

## Resolution
Implemented `cmd_load` and `cmd_offload` in `scripts/skills_router.py`:
- `skills-router load <skill_id> [--target <dir>]`: Copies the dormant or catalog skill directory into `<target>/.agents/skills/<skill_id>/`, marks the entry in `.agents/skills/.loaded.json` with timestamp and source path, and triggers a deterministic manifest rebuild.
- `skills-router offload <skill_id>`: Removes `<target>/.agents/skills/<skill_id>/`, updates `.loaded.json`, and triggers sync.
- `skills-router offload --all` (or `unload --all`): Iterates through all entries recorded in `.loaded.json` and cleanly removes staged directories, preventing disk bloat and prompt token leakage.
- Validated via unit test `test_on_demand_load_and_offload_lifecycle`.
