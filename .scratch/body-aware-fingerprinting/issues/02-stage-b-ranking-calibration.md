# Ticket 02: Stage B Ranking Calibration for Body Signatures

Type: task  
Status: resolved  
Blocked by: 01  

## Question
How should Stage B semantic scoring weight body fingerprints against existing dimensions (intent, object, action, trigger)?

## Resolution
Implemented in `score_candidate` (`scripts/skills_router.py`):
- Added `signature: 0.14` to `RANK_WEIGHTS`.
- Scores body signatures via boundary-safe `phrase_matches` and `credit_ratio(sig, req_tokens) >= 0.7`.
- Multi-signature matches dynamically increase the signature component score up to 1.0.
- Normalized overall confidence calculation by total rank weights sum.
- Avoids false acronym collisions by requiring $\ge 3$ word components for acronym generation.
