# Claude Code Project Guidelines

<!-- skills-manager:routing-contract:begin -->
### Autonomous Skills Router Contract (Claude Code)
Before running bash commands, editing code, or executing tasks:
1. **Pre-Flight Routing Query:**
   Run the router via BashTool:
   ```bash
   python3 scripts/skills_router.py route "<user intent or task description>"
   ```
2. **Decision Triad Protocol:**
   - **`route`**: Follow the returned skill or minimal disjoint multi-skill plan. Declare the 4-phase execution pipeline (`Guardrails → Pre-Execution → Execution → Verification`) and read only the matched `SKILL.md` file(s) (progressive disclosure).
   - **`ambiguous`**: When multiple competing skills tie, present the disambiguation choices to the user before editing code.
   - **`no_route`**: No specialized skill matched. Proceed with standard generalist reasoning without hallucinated skill tools.
3. **Local Sovereignty:** Local project skills (`./.agents/skills/`, `./skills/`) strictly override global plugins (`~/.claude/skills/`).
4. **Lifecycle & Dormancy:** Manage dormant skills with `python3 scripts/skills_router.py disable <id>` and `enable <id>`.
<!-- skills-manager:routing-contract:end -->
