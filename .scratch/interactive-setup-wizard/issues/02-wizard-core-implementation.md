# Ticket 02: Core Implementation in `cmd_init` and `cmd_setup`

Type: task  
Status: resolved  
Blocked by: 01  

## Question
Where in `scripts/skills_router.py` should the wizard logic live, and how should it integrate with `cmd_install_harness` and `cmd_sync`?

## Resolution
Implemented in `scripts/skills_router.py`:
- Added `run_interactive_wizard` helper function.
- Added `skills-router setup` CLI subcommand as dedicated entry point for interactive setup.
- Updated `init` subparser with `--wizard` and `-y` / `--non-interactive` flags.
- Passes user-selected harness list (`["all"]`, `["claude", "gemini"]`, or `["cursor", "windsurf", "roo"]`) directly into `cmd_install_harness`.
- Synchronizes registry deterministically via `cmd_sync`.
