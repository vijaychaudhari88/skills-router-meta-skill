# Ticket 01: Interactive Setup Wizard Design & CLI Flags

Type: task  
Status: resolved  
Blocked by: none  

## Question
How should the wizard prompt the user, handle defaults, and support non-interactive execution?

## Resolution
Implemented `run_interactive_wizard(target_dir, detected_profile, stack_desc)`:
- Dynamically orders options so the auto-detected tech stack (e.g. `web`, `android`, or `core`) is placed as option `[1] [Recommended Default]`.
- Pressing `Enter` automatically accepts the detected default without typing numbers or strings.
- Allows user to choose between:
  - Step 1: Skill Profiles (`core`, `web`, `android`, `ai`, `all`).
  - Step 2: Target AI Agent Harnesses (All 7, Claude/Gemini only, or IDE rule files only).
- Flags `--wizard`, `--yes`, `-y`, and `--non-interactive` control execution mode.
