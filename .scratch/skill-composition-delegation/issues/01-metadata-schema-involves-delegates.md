# Ticket 01: Declarative Metadata Schema for Involves and Delegates

Type: task  
Status: open  
Blocked by: none  

## Question
What metadata fields in `SKILL.md` frontmatter and `SkillRecord` dataclass represent generalized skill-to-skill invocation?

## Context
- Add `involves: list[str]` and `delegates_to: list[str]` to `SkillRecord`.
- Update `extract_metadata` to parse `involves`, `depends_on`, and `delegates_to` from YAML frontmatter.
- Support both list format (`- skill-a`) and inline comma format (`skill-a, skill-b`).
