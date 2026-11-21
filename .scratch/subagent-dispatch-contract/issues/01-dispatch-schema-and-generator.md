# Ticket 01: Standardized Subagent Dispatch Schema & Generator

Type: task  
Status: resolved  
Blocked by: none  

## Question
What standardized JSON schema and generator function should produce subagent dispatch contracts in `skills-router route`?

## Resolution
- Upgraded `HEAVY_SUBAGENT_SKILLS` with explicit typed entries: `role`, `typeName`, `model`, `isolation`, `reason`, and `deliverable_contract`.
- Implemented `build_subagent_dispatch(selected_candidates, query)` returning a machine-readable specification when heavy audit/debugging skills match.
- Injected `subagent_dispatch` into `route_query` response payloads for single and multi-skill routing plans.
