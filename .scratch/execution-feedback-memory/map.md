# Wayfinder Map: Action 2 — Execution Feedback Memory & Adaptive Calibration

## Destination
Implement a lightweight, self-optimizing **Execution Feedback Memory** for `skills-router`:
1. **Outcome Recording CLI (`record` / `feedback`):**
   - Record task success, failure, or abandonment:
     `skills-router record <skill_id> --outcome <success|failure> [--query "<task>"]`
2. **Persistent Storage (`.routing-history.json`):**
   - Store success/failure counters, failure reasons, and last recorded timestamp in `<project_root>/.agents/skills/.routing-history.json`.
3. **Adaptive Stage B Calibration:**
   - In `score_candidate`, load history:
     - Proven track record ($S \ge 3$, smoothed rate $\ge 75\%$): $+0.05$ bonus with `proven_track_record`.
     - Repeated failures ($S+F \ge 3$, smoothed rate $\le 35\%$): $0.80\times$ penalty with `unreliable_track_record`.
4. **Summary & Inspection CLI:**
   - `skills-router stats` or `skills-router feedback --show` to display historical skill performance.
5. **Fast & Dependency-Free:** Pure Python stdlib, bounded JSON size, sub-35ms routing latency maintained.

## Notes
- **Workspace:** `/data/user/0/ai.antigem/files/home/projects/skills-router-meta-skill`
- **Main Tool:** `scripts/skills_router.py`

## Decisions so far
- [x] [01-feedback-storage-and-cli](issues/01-feedback-storage-and-cli.md): Standardized `.routing-history.json` under `.agents/skills/` and CLI record/feedback commands.
- [x] [02-adaptive-calibration-scoring](issues/02-adaptive-calibration-scoring.md): Implemented Laplace-smoothed thresholding (bonus $\ge 75\%$, penalty $\le 35\%$) with $\ge 3$ sample gating.
- [x] [03-history-inspection-and-tests](issues/03-history-inspection-and-tests.md): Added unit test lifecycle and adaptive scoring tests; verified full test suite.
