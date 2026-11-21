# Ticket 01: Slash Command Parsing & Direct Routing in Meta-Router

Type: task  
Status: resolved  
Blocked by: none  

## Question
How should `skills-router` parse, strip, and route user-typed slash commands (`/<command>` or `/<skill-name>`) with priority over general fuzzy matching?

## Context
Users frequently invoke skills by typing slash commands in chat (e.g. `/wayfinder`, `/tdd`, `/test-driven-development`, `/chrome-devtools`, `/chisle`, `/ponytail`). Currently, a leading slash or bare command may be treated as raw text and penalized if no task object/action is provided. The router must recognize leading `/`, match against skill names, aliases, and declared commands, and return a validated `route` decision with 1.0 confidence.

## Answer
Implemented in `scripts/skills_router.py`:
- Added regex extraction for leading slash commands: `^/([a-zA-Z0-9_-]+)(?:\s+(.*))?$`.
- Direct instant lookup against skill names, aliases, and registered commands.
- Bypasses ambiguity thresholds, returning `confidence: 1.0`, `status: "slash_command"`, and full 4-phase execution pipeline.
- Verified by unit tests (`test_slash_command_routing` in `tests/test_skills_router.py`).
