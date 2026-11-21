# Ticket 03: History Inspection, Unit Tests & Regression Verification

Type: task  
Status: resolved  
Blocked by: 01, 02  

## Question
What unit tests and CLI inspection views ensure feedback recording and adaptive calibration work deterministically?

## Resolution
- Implemented `cmd_stats` and `feedback --show` CLI table view with counts, percentage success, and timestamps.
- Added comprehensive unit tests in `tests/test_skills_router.py`:
  - `test_record_execution_feedback_lifecycle`
  - `test_adaptive_scoring_with_history`
- Added `.routing-history.json` to `.gitignore`.
- Full test suite verified (25/25 passed).
