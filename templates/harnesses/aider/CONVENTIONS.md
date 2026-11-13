# Project Conventions (Aider)

<!-- skills-manager:routing-contract:begin -->
### Autonomous Skills Router Conventions
Before executing changes or modifying files:
1. Consult the skills router:
   ```bash
   python3 scripts/skills_router.py route "<user intent or task description>"
   ```
2. Follow the Decision Triad:
   - **`route`**: Apply the matched skill instructions and execute with test-driven discipline.
   - **`ambiguous`**: Ask the user which approach/tool to use.
   - **`no_route`**: Standard generalist development.
3. Never read all skills upfront; read only the routed `SKILL.md` file.
<!-- skills-manager:routing-contract:end -->
