---
name: init
description: First-time project workspace setup — stack detection, harness install, skill registration.
---

# Init

One-command first-time project setup: detect stack, install harness contracts, register skills.

## Usage

```bash
python3 scripts/skills_router.py init [path] [--profile <name>]
```

## What it does

1. Detects the project stack (language, framework, agent harness)
2. Installs harness contracts for Claude Code, Gemini/Antigravity, Cursor, Windsurf, Roo/Cline, Aider
3. Registers project skills in `./skills/` or `./.agents/skills/`
4. Syncs `SKILLS_REGISTRY.md` and the routing manifest

## Profile

`core` = minimal universal coding (planning, TDD, debugging, review, economy). `all` = full catalog.

## Skills Applied

> 🛠️ **Skills Applied:**
> - `init`: initialized project workspace with harness contracts and skills registry
