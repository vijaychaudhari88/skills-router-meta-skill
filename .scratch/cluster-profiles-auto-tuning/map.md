# Wayfinder Map: Action 3 — Multi-Tool Cluster Profiles Auto-Tuning

## Destination
Implement multi-stack auto-detection and profile auto-tuning for `skills-router`:
1. **Multi-Stack / Hybrid Project Detection:**
   - Detect compound stacks (e.g., Python + Web, Web + Android) and return compound profile specifications (e.g. `android+web`).
2. **Dynamic / Composite Profile Composition:**
   - Support `+` joined compound profiles in `filter_skills_by_profile` and `set_active_profile` (e.g. `web+android`, `core+ai`).
3. **Intent-Driven Profile Auto-Tuning (`skills-router tune` / `profile auto`):**
   - Inspect workspace markers and `.routing-history.json` frequently used skills to suggest or apply optimal profiles automatically.
4. **Interactive Setup Integration:**
   - Detect hybrid stacks during `skills-router init` and `setup`, recommending composite or custom profiles.
5. **Zero-Dependency & Invariant Guarantees:**
   - Pure Python standard library, maintaining sub-35ms routing latency and prompt cache determinism.

## Notes
- **Workspace:** `/data/user/0/ai.antigem/files/home/projects/skills-router-meta-skill`
- **Main Tool:** `scripts/skills_router.py`

## Decisions so far
- [x] [01-multi-stack-and-compound-profiles](issues/01-multi-stack-and-compound-profiles.md): Enhanced `detect_project_stack` to evaluate compound stacks and implemented `parse_compound_profile` with union of categories/skills.
- [x] [02-auto-tuning-engine-and-cli](issues/02-auto-tuning-engine-and-cli.md): Added `cmd_tune`, `tune` subcommand, and `profile auto` flag.
- [x] [03-unit-tests-and-verification](issues/03-unit-tests-and-verification.md): Added 3 unit tests covering multi-stack detection, filtering, and tuning; 28/28 tests pass.
