# Gemini CLI Conventions

<!-- skills-manager:routing-contract:begin -->
### Autonomous Skills Router Contract
Query before turn execution: `python3 scripts/skills_router.py route "<task>"`
Follow Decision Triad: route (execute pipeline), ambiguous (clarify), no_route (general reasoning).
<!-- skills-manager:routing-contract:end -->

## Token Optimization: pxpipe
- Proxy address: `http://127.0.0.1:47821`
- Active controls: `source ~/.pxpipe-helpers.sh && pxpipe-status`
