# Wayfinder Map: Body-Aware Signature Fingerprinting

## Destination
Upgrade `skills-router` from frontmatter-only scanning to **Body-Aware Signature Fingerprinting**:
1. Solve the "Progressive Disclosure Accuracy Trap" (where stripping tool execution bodies drops routing accuracy by 37–44% on overlapping skills like `code-review`, `chisle-review`, `ponytail-review`, `tdd`, `debugging`, etc.).
2. Extract compact semantic fingerprints from `SKILL.md` bodies during deterministic `sync` without bloating token overhead:
   - Specific commands (e.g. `python3 ...`, `/cmd`, CLI flags).
   - Heading sections (`## Process`, `## When to Use`, `## Rules`, `## Capabilities`).
   - Trigger phrases, negative triggers, and explicit code keywords.
3. Incorporate body fingerprint matching into Stage B semantic ranking with calibrated weights and boundary safety.
4. Maintain sub-35ms routing latency, 100% stdlib Python, and prompt cache determinism.

## Notes
- **Workspace:** `/data/user/0/ai.antigem/files/home/projects/skills-router-meta-skill`
- **Main Tool:** `scripts/skills_router.py`
- **Core Constraints:** Zero external dependencies, bounded scanning (read only structural headers/signatures, not thousands of prose lines), deterministic manifest generation.

## Decisions so far

- [Ticket 01: Body Fingerprint Extraction Engine in `extract_metadata`](issues/01-body-fingerprint-extraction.md) — Extracted markdown headings, bold anchors, and code spans from first 80 lines into `SkillRecord.signatures` (bounded $\le 25$).
- [Ticket 02: Stage B Ranking Calibration for Body Signatures](issues/02-stage-b-ranking-calibration.md) — Added `signature: 0.14` to `RANK_WEIGHTS` with boundary phrase matching and multi-match scaling.
- [Ticket 03: Disambiguation Benchmarks & Regression Verification](issues/03-disambiguation-benchmarks.md) — Added `test_body_signature_fingerprinting_disambiguation` proving clear separation between `code-review`, `ponytail-review`, and `chisle-review`. 23/23 tests pass.

## Out of scope
- Full text vector embeddings or external embedding models.
