# Ticket 02: CLI Formatting & Subagent Inspection Flag

Type: task  
Status: resolved  
Blocked by: 01  

## Question
How should the CLI expose and format subagent dispatch instructions for human operators and orchestrating agents?

## Resolution
- Added `--subagent` flag to `route` subparser.
- When `--subagent` is passed to `cmd_route`, returns formatted subagent dispatch contract or `{"required": false, "message": "..."}` cleanly.
