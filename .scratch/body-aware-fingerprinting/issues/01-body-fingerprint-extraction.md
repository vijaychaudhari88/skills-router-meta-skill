# Ticket 01: Body Fingerprint Extraction Engine in `extract_metadata`

Type: task  
Status: resolved  
Blocked by: none  

## Question
How should `skills-router` parse `SKILL.md` files to extract compact body fingerprints without blowing up manifest size or scanning time?

## Resolution
Implemented in `extract_metadata` (`scripts/skills_router.py`):
- Reads the first 80 lines of each `SKILL.md`.
- Parses beyond the frontmatter fences (`in_fm >= 2`).
- Extracts markdown section headings (`## Heading`), bold key concepts (`**Standards**`, `**Bug:**`, `**Risk:**`, `**Scale:**`), and inline code patterns (`` `git diff` ``, `` `/cmd` ``).
- Normalizes and bounds signatures to max 25 distinct tokens per skill.
- Added `signatures: list[str]` to `SkillRecord` and serializes into `routing-manifest.json`.
