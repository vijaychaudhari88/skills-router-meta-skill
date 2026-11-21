# Ticket 02: First-Time Project Workspace Setup (`skills-router init`)

Type: task  
Status: resolved  
Blocked by: 01  

## Question
How should `skills-router init` configure a new or existing project directory for deterministic skill routing?

## Context
When running in a new project directory, the user currently has to run `sync` and `install-harness` separately.
`skills-router init [path]`:
1. Creates `.agents/skills/` and `skill-registry/`.
2. Inspects project files to auto-detect tech stack (e.g., `package.json` -> web profile, `build.gradle` -> android profile, `requirements.txt`/`pyproject.toml` -> core profile).
3. Sets recommended profile in `.skills-profile`.
4. Installs AI harness integration rules across all standard harnesses (`CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, etc.).
5. Builds initial deterministic `routing-manifest.json` and `SKILLS_REGISTRY.md`.
6. Prints a concise setup receipt.

## Resolution
Implemented `cmd_init` in `scripts/skills_router.py`:
- Inspects target workspace for build/package manifests to auto-detect tech stack:
  - `build.gradle` / `settings.gradle` / `app/src/main/AndroidManifest.xml` -> Android (`android` profile)
  - `package.json` / `tsconfig.json` / `pnpm-workspace.yaml` -> Web / Frontend (`web` profile)
  - `pyproject.toml` / `requirements.txt` / `setup.py` / generalist -> Core Python/Backend (`core` profile)
- Creates `.agents/skills/` and `skill-registry/` directories.
- Writes `.skills-profile` with the detected profile (or honors `--profile`).
- Runs `install_harnesses(target_dir, "all")` to establish AI harness contracts (`CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, Cursor, Windsurf, Roo, Aider).
- Executes `sync_skills_registry(target_dir)` to generate `routing-manifest.json` and `SKILLS_REGISTRY.md`.
- Emits a clean CLI receipt with detected stack, profile, and configured harnesses.
- Validated via unit test `test_project_init_autodetect_stack`.
