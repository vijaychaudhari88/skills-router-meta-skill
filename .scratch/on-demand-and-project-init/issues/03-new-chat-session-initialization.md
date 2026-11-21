# Ticket 03: New Chat Session Initialization (`skills-router session-start`)

Type: task  
Status: resolved  
Blocked by: 01, 02  

## Question
How should `skills-router session-start` run fast pre-flight verification and cleanup for a fresh chat session?

## Context
At the beginning of a new chat session (or in harness session start hooks), the agent needs to know the active routing topology without burning tokens:
`skills-router session-start [--cleanup]`:
1. Checks project setup status (`.agents/skills/` and harnesses).
2. Cleans up any leaked/un-offloaded ephemeral skills if requested or reports active loaded skills.
3. Verifies prompt cache prefix consistency.
4. Outputs a compact receipt (< 4 lines):
   `✔ Skills Router Ready | Profile: <profile> | Active: <N> | Dormant: <M> | On-Demand: <K>`

## Resolution
Implemented `cmd_session_start` in `scripts/skills_router.py`:
- Verifies project initialization status (`.agents/skills/` and harness files); offers automatic initialization if missing.
- Reads `.agents/skills/.loaded.json`; if `--cleanup` is specified, sweeps and deletes all stale ephemeral skills, syncing the catalog.
- If not cleaning up, counts on-demand loaded skills alongside active and dormant skills.
- Emits a compact, single-line receipt (< 20 tokens) suitable for harness startup hooks:
  `[Skills Router Ready | Profile: <profile> | Active: <N> | Dormant: <M> | On-Demand: <K>]`
- Validated via unit test `test_session_start_preflight_and_cleanup`.
