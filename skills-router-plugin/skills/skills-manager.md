---
name: skills-manager
description: Autonomous meta-skill and two-stage deterministic router for discovering, routing, and lifecycle-managing skills across project and global paths.
---

# Skills Manager & Autonomous Skill Router

Discover, route, assemble 4-phase pipelines, and manage dormant skills for AI coding agents (Claude Code, Gemini/Antigravity, Cursor, Windsurf, Roo/Cline, Aider). Runs fully offline via Python stdlib — zero embedding APIs, zero vector DB.

## When to use

- Route a task to the optimal skill(s) before writing code
- Build minimal disjoint multi-skill plans for composite tasks
- Manage dormant skills (enable/disable) to save tokens
- Sync skills and rebuild `SKILLS_REGISTRY.md`

## Tools

Use the AntiGem plugin worker:

- `list_skills` — discover skills from YAML frontmatter (no full-body reads)
- `read_skill` — read full SKILL.md of a routed skill (progressive disclosure on demand)
- `dormancy_check` — list active/dormant skill counts

Or run directly on the host:

```bash
python3 scripts/skills_router.py route "<task>"
python3 scripts/skills_router.py sync
python3 scripts/skills_router.py disable <id>
python3 scripts/skills_router.py enable <id>
```

## Decision Triad

Every query resolves to `route` (execute matched skill(s)), `ambiguous` (ask user to choose), or `no_route` (generalist reasoning — do not force a skill).

## 4-Phase Pipeline

`Guardrails → Pre-Execution → Execution → Verification`. Declare it before executing any routed skill.

## Skills Applied

Report concisely:

> 🛠️ **Skills Applied:**
> - `skills-manager`: deterministic routing and skill lifecycle for this task
