---
name: lifecycle
description: Manage dormant skill lifecycle — enable/disable skills to save tokens.
---

# Dormancy Lifecycle

Silence unused or experimental skills by renaming `SKILL.md` ↔ `SKILL.md.disabled`. Keeps them catalogued in the registry without polluting live prompt contexts.

## Commands

```bash
python3 scripts/skills_router.py disable <id>   # SKILL.md -> SKILL.md.disabled
python3 scripts/skills_router.py enable <id>    # SKILL.md.disabled -> SKILL.md
```

Disabled skills stay in `SKILLS_REGISTRY.md` marked `(Disabled)`, excluded from Stage A filtering, but discoverable via `list_skills` / `read_skill`.

## Auto-unload

Routed skills accumulate idle turns; after 5 idle turns without being called, they auto-unload to `.disabled`. Pinned skills are exempt.

## Skills Applied

> 🛠️ **Skills Applied:**
> - `lifecycle`: toggled skill dormancy to save context tokens
