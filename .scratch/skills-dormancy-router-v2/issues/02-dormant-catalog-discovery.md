# Ticket 02: Indexing Dormant / Disabled Skills in Catalog Discovery

Type: task  
Status: resolved  
Blocked by: 01  

## Question
How should `discover_all_skills` index `.disabled` directories while preserving prompt cache isolation (marking them dormant without exposing them to the base system prompt)?

## Context
When a plugin directory is named `<name>.disabled` (e.g. `chrome-devtools-plugin.disabled`, `superpowers.disabled`), the agent harness ignores it during prompt startup, saving thousands of tokens. However, the router must still know about these dormant capabilities so it can route matching user queries or slash commands to them.

## Answer
Implemented in `scripts/skills_router.py`:
- `discover_all_skills` now traverses `.disabled` directories instead of pruning them.
- Any skill within a `.disabled` ancestor directory is detected via `in_disabled_tree = any(p.endswith(".disabled") for p in rel_parts)`.
- Flags record `is_disabled = True` and `is_dormant = True`, with lower baseline priority (`rec_priority = priority - 20`) so active skills cleanly win ties.
- Verified by unit test (`test_dormant_skill_indexing_and_routing`).
