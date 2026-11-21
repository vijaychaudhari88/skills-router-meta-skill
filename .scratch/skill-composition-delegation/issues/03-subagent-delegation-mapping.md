# Ticket 03: Subagent Delegation Generation for Delegated Skills

Type: task  
Status: open  
Blocked by: 01  

## Question
How should `delegates_to` map into the standardized `subagent_dispatch` contract?

## Context
- In `build_subagent_dispatch`, check not only `HEAVY_SUBAGENT_SKILLS`, but also any skills declared under `delegates_to`.
- For declared delegated skills without hardcoded heavy entries, synthesize sensible default subagent contracts:
  - `role`: Title-cased skill name + "Specialist"
  - `typeName`: "self" or "research"
  - `model`: "inherit"
  - `isolation`: "ephemeral_subagent"
  - `prompt_template`: targeted execution instructions.
