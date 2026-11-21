# Ticket 02: Adaptive Stage B Calibration Scoring

Type: task  
Status: resolved  
Blocked by: 01  

## Question
How should empirical feedback adjust candidate confidence scores in Stage B ranking?

## Resolution
- Implemented Laplace-smoothed empirical rate calculation: $\text{Rate} = \frac{\text{success} + 1}{\text{total} + 2}$.
- Gated to skills with $\ge 3$ total recorded executions to avoid cold-start skew.
- High success ($\ge 75\%$): $+0.05$ confidence bonus with `proven_track_record` evidence tag.
- Low success ($\le 35\%$): $0.80\times$ confidence penalty multiplier with `unreliable_track_record` penalty tag.
