---
name: route_skills
description: Route task to optimal skills and build the 4-phase execution pipeline.
---

# Route Skills

Activate the skills-manager meta-skill and deterministic router for a request. If the argument is empty or unclear, ask the user whether they want to (1) route/execute a task, (2) sync and audit skills, or (3) enable/disable a dormant skill.

## Steps

1. Run `python3 scripts/skills_router.py route "<args>" --root <project>`
2. Follow the Decision Triad: `route` → execute; `ambiguous` → ask user; `no_route` → generalist
3. Organize into 4-phase pipeline: Guardrails → Pre-Execution → Execution → Verification
4. Report skills used:

> 🛠️ **Skills Applied:**
> - `<skill>`: <why in 5-10 words>

## Skills Applied

> 🛠️ **Skills Applied:**
> - `route_skills`: routed task and assembled 4-phase pipeline
