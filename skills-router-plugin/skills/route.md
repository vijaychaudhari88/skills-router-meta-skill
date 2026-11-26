---
name: route
description: Fast route query to skills-router for optimal skill or multi-skill plan.
---

# Route

Route a task query against the project and global skill catalog using the deterministic two-stage router.

## Usage

Host CLI:

```bash
python3 scripts/skills_router.py route "<task>" --root <project>
```

Plugin:

```json
{ "tool": "route", "arguments": { "query": "<task>", "root": "<project>" } }
```

Note: the JS VM has no shell access, so `route` returns the exact host command to run. Execute it on the host and follow the returned decision.

## Decision Triad

- `route`: adopt winner(s), declare 4-phase pipeline, read only matched SKILL.md
- `ambiguous`: present competing choices, ask user before editing
- `no_route`: proceed with generalist reasoning

## Skills Applied

> 🛠️ **Skills Applied:**
> - `route`: matched task to optimal skill via deterministic router
