# Wayfinder Map: Generalized Skill-to-Skill Invocation & Composition

## Destination
A generalized, universal skill-to-skill invocation and delegation system for `skills-router`:
Any skill (project or global) can explicitly declare companion skills it **involves** (inline pipeline inclusion) or **delegates to** (subagent offloading), and runtime calls (`skills-router route` / programmatic queries) recursively resolve, stage, hydrate, and guard against circular deadlocks.

## Notes
- **Workspace:** `/data/user/0/ai.antigem/files/home/projects/skills-router-meta-skill`
- **Engine File:** `scripts/skills_router.py`
- **Test File:** `tests/test_skills_router.py`
- **Pattern Inspiration:** Matt Pocock's "Call the Skill tool with `<skill>`" pattern generalized into declarative metadata (`involves`, `delegates_to`) and recursive pipeline assembly.

## Decisions so far

<!-- the index: one line per closed ticket -->

## Not yet specified
- Should deep transitive dependencies be fully flattened into hydration payload, or only direct children? (Default: transitive up to depth 3).

## Out of scope
- Arbitrary code execution inside SKILL.md (declarative metadata only).
- Bypassing profile restrictions without explicit on-demand resolution.
