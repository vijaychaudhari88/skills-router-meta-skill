# Wayfinder Map: Global Skills Dormancy & Meta-Router Slash Command Upgrade

## Destination
All non-`mattpocock-skills` global plugins are transitioned to dormant state (`.disabled`) on disk, while `skills-router` is upgraded to natively recognize slash commands (`/<command>`), index dormant plugins, and hydrate or route them on demand into agent context.

## Notes
- **Workspace:** `/data/user/0/ai.antigem/files/home/projects/skills-router-meta-skill`
- **Guaranteed Active Base:** `mattpocock-skills` remains fully active.
- **Skills Router Script:** `scripts/skills_router.py` (globally symlinked as `skills-router`).
- **Core Principles:** Zero base prompt bloat, deterministic prompt cache key stability, locate-before-reading, zero stubs.

## Decisions so far

- [[01-slash-command-support.md](file:///data/user/0/ai.antigem/files/home/projects/skills-router-meta-skill/.scratch/skills-dormancy-router-v2/issues/01-slash-command-support.md)]: Direct regex matching on leading slash commands (`/<cmd>`) routes with 1.0 confidence and validates immediately.
- [[02-dormant-catalog-discovery.md](file:///data/user/0/ai.antigem/files/home/projects/skills-router-meta-skill/.scratch/skills-dormancy-router-v2/issues/02-dormant-catalog-discovery.md)]: `discover_all_skills` indexes `.disabled` directories, tagging them `is_dormant=True` and `is_disabled=True` with lower base priority.
- [[03-on-demand-hydration-contract.md](file:///data/user/0/ai.antigem/files/home/projects/skills-router-meta-skill/.scratch/skills-dormancy-router-v2/issues/03-on-demand-hydration-contract.md)]: Dormant skills route with an on-demand `hydration` payload containing `instructions` and `activation_command`.
- [[04-safe-global-plugin-deactivation.md](file:///data/user/0/ai.antigem/files/home/projects/skills-router-meta-skill/.scratch/skills-dormancy-router-v2/issues/04-safe-global-plugin-deactivation.md)]: Safely disabled 9 global plugins and 5 opencode directories; only `mattpocock-skills`, `skills-manager`, and `rtk` remain active on disk. Active count dropped from 102 to 41; 135 dormant skills cataloged.

## Not yet specified
- Dynamic ephemeral plugin hydration vs on-the-fly un-disabling.
- Slash command alias registry generation.

## Out of scope
- Deleting any skill source code (dormancy must be non-destructive via `.disabled` naming).
- Modifying `mattpocock-skills` files.
