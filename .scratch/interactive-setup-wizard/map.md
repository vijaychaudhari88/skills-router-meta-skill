# Wayfinder Map: First-Time Initialization Setup Wizard

## Destination
Upgrade `skills-router init` (and `setup`) with an interactive, user-friendly setup wizard:
1. When running `skills-router init` interactively (e.g., via `skills-router setup` or `skills-router init --wizard`), guide the user through a quick 2-step setup:
   - **Step 1: Confirm or Pick Project Tech Stack / Profile** (Web, Android, Core/Python, AI, All).
   - **Step 2: Select AI Agent Harnesses** (All 7, Claude/Gemini only, or IDE rule files only).
   - **Step 3: Initial Catalog Sync & Verification** (Fast check, outputs compact success card).
2. Keep it non-blocking when automated/scripted (support `--non-interactive` / `-y` for CI/agent automation).

## Notes
- **Workspace:** `/data/user/0/ai.antigem/files/home/projects/skills-router-meta-skill`
- **Main Tool:** `scripts/skills_router.py`
- **Constraints:** Python standard library only, mobile/Termux friendly.

## Decisions so far

- [Ticket 01: Interactive Setup Wizard Design & CLI Flags](issues/01-wizard-prompting-and-defaults.md) — Implemented `run_interactive_wizard` with 2-step numbered prompts, stack recommendation as default, and Enter-key fallback.
- [Ticket 02: Core Implementation in `cmd_init` and `cmd_setup`](issues/02-wizard-core-implementation.md) — Implemented `skills-router setup` command and `--wizard` flag on `init`.
- [Ticket 03: Automated Unit Testing & Headless Verification](issues/03-unit-testing-and-headless-verification.md) — Implemented `test_interactive_wizard_with_mocked_inputs`; full suite has 22 passing tests.

## Out of scope
- GUI/Web-based setup wizards (this is a CLI meta-skill engine).
