# Roo Code Workspace Router Rules

<!-- skills-manager:routing-contract:begin -->
### Autonomous Skills Router Contract (Roo Code / Cline)
Before modifying code or executing commands:
1. **Pre-Flight Routing:**
   Execute:
   ```bash
   python3 scripts/skills_router.py route "<task>"
   ```
2. **Decision Triad:**
   - **`route`**: Execute the returned skill(s). Declare active skills and follow the 4-phase execution pipeline.
   - **`ambiguous`**: Prompt the user to choose between competing skills.
   - **`no_route`**: Continue standard generalist mode.
3. **Progressive Disclosure:** Load full `SKILL.md` documents only for selected skills.
<!-- skills-manager:routing-contract:end -->
