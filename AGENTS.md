# Gemini / Antigravity Agent Architecture

<!-- skills-manager:routing-contract:begin -->
### Autonomous Skills Router Contract (Gemini / Antigravity)
Before modifying code, designing architecture, or executing sub-tasks:
1. **Pre-Flight Routing Query:**
   Consult the deterministic skills router before turn execution:
   ```bash
   python3 scripts/skills_router.py route "<user intent or task description>"
   ```
2. **Decision Triad Protocol:**
   - **`route`**: Proceed with the returned skill or minimal disjoint multi-skill plan. Declare the 4-phase execution pipeline (`Guardrails → Pre-Execution → Execution → Verification`) and load only the matched `SKILL.md` file(s).
   - **`ambiguous`**: When multiple competing skills tie or conflict, present the disambiguation choices to the user or clarify intent before editing code.
   - **`no_route`**: No specialized skill matched. Proceed with standard generalist reasoning without hallucinating skill activations.
3. **Local Sovereignty:** Skills in `./.agents/skills/` and `./skills/` take absolute precedence over global runtime plugins.
4. **Lifecycle & Dormancy:** Manage dormant skills via `python3 scripts/skills_router.py disable <skill-id>` and `enable <skill-id>`.
<!-- skills-manager:routing-contract:end -->
