# Wayfinder Map: On-Demand Skills Lifecycle & Project/Session Initialization

## Destination
Upgrade `skills-router` with two major production capabilities:
1. **On-Demand Skills Loading & Offloading (`load` / `offload`):** Dynamically stage dormant skills into project `.agents/skills/` on demand, and offload/cleanup back to dormant baseline when tasks complete.
2. **First-Time Project Setup & Session Initialization (`init` / `session-start`):** One-command project workspace setup (`skills-router init`) that detects stack and configures harnesses, plus a fast session pre-flight check (`skills-router session-start`) that verifies state and cleans up stale loaded skills.

## Notes
- **Workspace:** `/data/user/0/ai.antigem/files/home/projects/skills-router-meta-skill`
- **Main Tool:** `scripts/skills_router.py` (globally symlinked as `skills-router`)
- **Core Constraints:** Zero base prompt token waste, deterministic prompt caching, local sovereignty (`.agents/skills/` overrides global), clean teardown.

## Decisions so far

- [Ticket 01: On-Demand Skill Loading and Offloading Engine](issues/01-on-demand-load-offload-lifecycle.md) — Implemented `skills-router load` and `offload [--all]` with `.loaded.json` state tracking and automatic manifest rebuilds.
- [Ticket 02: First-Time Project Workspace Setup (`skills-router init`)](issues/02-project-directory-first-time-setup.md) — Implemented `skills-router init` with tech stack heuristic auto-detection (Android, Web, Python/Core) and multi-harness installation.
- [Ticket 03: New Chat Session Initialization (`skills-router session-start`)](issues/03-new-chat-session-initialization.md) — Implemented `skills-router session-start [--cleanup]` providing an ultra-compact single-line receipt and ephemeral skill sweep.
- [Ticket 04: Full Integration Testing, Benchmarking & Harness Verification](issues/04-integration-benchmark-and-verification.md) — Expanded suite to 20 tests with 100% pass rate in 0.44s and <12ms benchmark latency.

## Out of scope
- Mutating active git tracked project files outside `.agents/` or harness config files.
