# Ticket 03: On-Demand Hydration Contract for Dormant Skills

Type: task  
Status: resolved  
Blocked by: 02  

## Question
How should the router output hydrate dormant skills (bounded `SKILL.md` content injection vs ephemeral subagent dispatch vs `skills-router enable` command)?

## Context
When a dormant skill is routed, the agent needs its instructions without turning the whole plugin back on permanently on disk. The router should provide a `hydration` block containing the path, summary, and instructions for reading the skill on demand (Tier 2/3 of blueprint).

## Answer
Implemented in `scripts/skills_router.py`:
- Added `extract_hydration_payload(skill, project_root)` function.
- Whenever a dormant skill is routed or `--hydrate` is passed, the response JSON includes a full `hydration` block containing:
  - `source_path`: exact filesystem path to `SKILL.md`.
  - `is_dormant`: boolean flag.
  - `instructions`: full `SKILL.md` documentation body.
  - `activation_command`: `skills-router enable <skill>` for permanent disk activation if desired.
- Allows the caller agent to execute the skill immediately in-session with zero upfront prompt cost in future sessions.
