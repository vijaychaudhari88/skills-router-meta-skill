# Ticket 02: Recursive Pipeline Expansion with Cycle Detection

Type: task  
Status: open  
Blocked by: 01  

## Question
How should the router recursively expand involved skills into the 4-phase pipeline while guarding against circular loops?

## Context
- Implement `resolve_skill_dependencies(skill, registry, visited=None, depth=0, max_depth=3)`:
  - Traverses `involves` tree recursively.
  - Maintains `visited` set to detect and prevent cycles (e.g. A -> B -> A).
- In `build_pipeline_declaration`, merge all transitively involved skills into their appropriate pipeline phases (Planning -> Phase 2, Implementation -> Phase 3, Verification -> Phase 4).
- When `--hydrate` is requested, include instruction blocks for the primary skill and all transitively involved skills.
