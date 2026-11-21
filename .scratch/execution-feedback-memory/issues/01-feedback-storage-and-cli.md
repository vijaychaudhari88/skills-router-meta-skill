# Ticket 01: Feedback Storage and CLI Handlers

Type: task  
Status: resolved  
Blocked by: none  

## Question
How should task execution outcomes be persisted and recorded via the CLI?

## Resolution
- Implemented `load_routing_history` and `save_routing_history` targeting `<project_root>/.agents/skills/.routing-history.json`.
- Implemented `cmd_record(skill_id, outcome, query, project_root)` with standard library `json` and `time`.
- Added CLI subcommands `record` and `feedback` supporting `--skill`, `--outcome`, and `--query`.
