# Ticket 01: Multi-Stack Detection and Compound Profile Support

Type: task  
Status: resolved  
Blocked by: none  

## Question
How should multi-stack projects be detected and composite profiles represented?

## Resolution
- Enhanced `detect_project_stack(target_dir)` to evaluate all sub-stacks simultaneously (Android, Web/TypeScript, Python, and AI/LLM integration).
- If multiple stacks match, combines them into composite profile strings (e.g. `android+web`, `ai+web`).
- Implemented `parse_compound_profile` and `is_valid_profile_spec` to handle `+`-joined profile syntax across `filter_skills_by_profile`, `get_active_profile`, and `set_active_profile`.
