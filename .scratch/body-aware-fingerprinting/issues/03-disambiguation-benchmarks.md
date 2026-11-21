# Ticket 03: Disambiguation Benchmarks & Regression Verification

Type: task  
Status: resolved  
Blocked by: 01, 02  

## Question
What benchmark test queries verify that overlapping skills are routed accurately without regression?

## Resolution
Added `test_body_signature_fingerprinting_disambiguation` in `tests/test_skills_router.py`:
- Verified 3 overlapping review skills disambiguate accurately:
  1. `review pr against standards and spec...` $\to$ `code-review` (confidence 0.747).
  2. `review my pr for bugs, scale, and what breaks under real load...` $\to$ `ponytail-review` (confidence 0.727).
  3. `chisle review this diff for what could be deleted or simplified` $\to$ `chisle-review` (confidence 1.076).
- All 23 unit tests pass in 2.5s.
- Benchmark passes 4/4 in 51ms (~12.8ms/query).
