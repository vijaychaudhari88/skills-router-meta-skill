---
name: sync
description: Sync skills and rebuild SKILLS_REGISTRY.md and routing manifest.
---

# Sync

Discover all skills across project and global paths, deduplicate by Local Sovereignty, and rebuild `SKILLS_REGISTRY.md` plus the JSON routing manifest.

## Usage

```bash
python3 scripts/skills_router.py sync [--root <project>]
```

## Output

`SKILLS_REGISTRY.md` with 5 columns: name, category, scope, status (Active/Disabled), path. Disabled skills marked `(Disabled)`, remain discoverable, excluded from Stage A filtering.

Or use the plugin `list_skills` tool for a JSON listing of active/dormant skills without reading full bodies.

## Skills Applied

> 🛠️ **Skills Applied:**
> - `sync`: rebuilt skills registry and routing manifest
