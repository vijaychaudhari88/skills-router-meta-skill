# Wayfinder Map: Action 4 — Subagent Dispatch Contract Standardization

## Destination
Standardize the **Subagent Dispatch Contract** across `skills-router route`:
1. **Machine-Readable Dispatch Schema:**
   - In `skills-router route` JSON output, include a top-level `subagent_dispatch` block when routed skills belong to heavy verification/auditing domains.
2. **Schema Specification:**
   - `subagent_dispatch`:
     - `required`: bool
     - `primary_subagent`: dict with `skill`, `role`, `typeName`, `model`, `isolation`, `prompt_template`, `deliverable_contract`.
     - `dispatches`: list of candidate subagent payloads.
     - `isolation_rationale`: string explanation.
3. **Multi-Skill Plan Subagent Offloading:**
   - For multi-skill plans containing heavy skills, extract subagent dispatch blocks for isolated execution.
4. **Interactive / CLI Support:**
   - Added `--subagent` flag to `skills-router route` to directly output subagent dispatch specifications.
5. **Zero-Dependency & Invariant Guarantees:**
   - Pure Python standard library, sub-35ms routing latency maintained.

## Notes
- **Workspace:** `/data/user/0/ai.antigem/files/home/projects/skills-router-meta-skill`
- **Main Tool:** `scripts/skills_router.py`

## Decisions so far
- [x] [01-dispatch-schema-and-generator](issues/01-dispatch-schema-and-generator.md): Defined `HEAVY_SUBAGENT_SKILLS` metadata and implemented `build_subagent_dispatch`.
- [x] [02-cli-subagent-formatting](issues/02-cli-subagent-formatting.md): Added `--subagent` CLI flag to `cmd_route`.
- [x] [03-unit-tests-and-verification](issues/03-unit-tests-and-verification.md): Added unit tests and verified 31/31 tests pass.
