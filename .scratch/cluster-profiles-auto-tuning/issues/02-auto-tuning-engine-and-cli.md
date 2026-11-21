# Ticket 02: Auto-Tuning Engine and CLI Commands

Type: task  
Status: resolved  
Blocked by: 01  

## Question
How should the router auto-tune active profiles based on project structure and execution feedback history?

## Resolution
- Implemented `cmd_tune(project_root, apply=False)` and added `tune` CLI subcommand and `profile auto [--apply]`.
- Analyzes tech stack markers combined with frequent skills ($\ge 2$ executions) in `.routing-history.json` to synthesize recommended profiles.
- Integrated hybrid stack recommendations into `run_interactive_wizard`.
