---
trigger: always_on
description: "Autonomous Skill Router and 4-phase execution pipeline for Windsurf Cascade"
---

<!-- skills-manager:routing-contract:begin -->
# Windsurf Cascade Skill Router Guidelines

When receiving any non-trivial user coding request:
1. **Pre-Flight Routing Check:**
   Run the skills router tool:
   ```bash
   python3 scripts/skills_router.py route "<task prompt>"
   ```
2. **Execution Contract:**
   - **`route`**: Adopt the matched skill. Read only its `SKILL.md` file. Follow the 4-phase execution pipeline.
   - **`ambiguous`**: Clarify the user's intent when top candidates tie.
   - **`no_route`**: Proceed with standard Cascade reasoning without forcing a skill.
<!-- skills-manager:routing-contract:end -->
