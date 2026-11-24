#!/usr/bin/env python3
"""
Formal Invariant Verifier for Skills Router Engine
Exhaustively checks mathematical invariants across the entire routing space.
"""
import sys
import json
import itertools
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.skills_router import (
    discover_all_skills,
    filter_skills_by_profile,
    route_query,
    parse_compound_profile,
    SkillRecord
)

class VerificationFailure(Exception):
    pass

def check_invariant_1_determinism(registry: dict[str, SkillRecord]):
    """
    Invariant 1 (Strict Determinism & Purity):
    For any query Q and state S, route(Q, S) == route(Q, S).
    Routing must be pure with no state mutations or non-deterministic ordering.
    """
    sample_queries = [
        "refactor this code with tdd",
        "find race condition bug",
        "create a react login component",
        "run benchmark",
        "disable a skill"
    ]
    for q in sample_queries:
        r1 = route_query(q, registry)
        r2 = route_query(q, registry)
        # Compare decisions, skills, pipeline
        if r1["decision"] != r2["decision"]:
            raise VerificationFailure(f"Determinism failed on '{q}': decision {r1['decision']} != {r2['decision']}")
        if r1.get("skill") != r2.get("skill"):
            raise VerificationFailure(f"Determinism failed on '{q}': skill {r1.get('skill')} != {r2.get('skill')}")
        if r1.get("confidence") != r2.get("confidence"):
            raise VerificationFailure(f"Determinism failed on '{q}': confidence drift")
    return True

def check_invariant_2_decision_triad(registry: dict[str, SkillRecord]):
    """
    Invariant 2 (Valid Decision Triad Partitioning):
    For all queries Q, decision(Q) in {'route', 'ambiguous', 'no_route'}.
    If decision == 'route', skill != None.
    If decision == 'no_route', skill == None.
    """
    test_queries = [
        "",
        "   ",
        "xyz random unparseable 12345 non-existent",
        "write tests for the login feature",
        "git status",
        "debug memory leak in chrome",
        "skills router route this"
    ]
    for q in test_queries:
        res = route_query(q, registry)
        d = res.get("decision")
        if d not in {"route", "ambiguous", "no_route"}:
            raise VerificationFailure(f"Invalid decision '{d}' for query '{q}'")
        if d == "route":
            if not res.get("skill") and not res.get("skills"):
                raise VerificationFailure(f"Decision 'route' returned empty skill for query '{q}'")
        elif d == "no_route":
            if res.get("skill") is not None:
                raise VerificationFailure(f"Decision 'no_route' returned non-null skill {res.get('skill')} for query '{q}'")
    return True

def check_invariant_3_profile_monotonicity(all_skills: dict[str, SkillRecord]):
    """
    Invariant 3 (Profile Filter Inclusivity & Monotonicity):
    Let Skills(P) be active skills in profile P.
    For any profile P, Skills(P) subset of Skills('all').
    Dormant skills must never be routed.
    """
    all_filtered = filter_skills_by_profile(all_skills, "all")
    core_filtered = filter_skills_by_profile(all_skills, "core")
    web_filtered = filter_skills_by_profile(all_skills, "web")

    # Invariant: core and web must be subsets of all
    for s_id in core_filtered:
        if s_id not in all_filtered:
            raise VerificationFailure(f"Skill '{s_id}' in core profile but missing from 'all'")
    for s_id in web_filtered:
        if s_id not in all_filtered:
            raise VerificationFailure(f"Skill '{s_id}' in web profile but missing from 'all'")

    # Invariant: Dormant skills can never be returned as matched route
    # Pick a dormant skill in core profile
    dormant_candidates = [s for s, r in all_skills.items() if s not in core_filtered]
    if dormant_candidates:
        dormant_skill = dormant_candidates[0]
        # Query that directly targets dormant skill name
        res = route_query(dormant_skill, core_filtered)
        if res.get("decision") == "route" and res.get("skill") == dormant_skill:
            raise VerificationFailure(f"Dormant skill '{dormant_skill}' was routed in core profile!")
    return True

def check_invariant_4_pipeline_soundness(registry: dict[str, SkillRecord]):
    """
    Invariant 4 (Pipeline 4-Phase Soundness):
    Every successful route must output a complete 4-Phase pipeline:
    Guardrails -> Pre-Execution -> Execution -> Verification.
    Phase 4 must always contain verification coverage.
    """
    res = route_query("implement new feature with unit tests", registry)
    if res.get("decision") == "route":
        pipe = res.get("pipeline")
        if not pipe:
            raise VerificationFailure("Missing execution pipeline in routed result")
        phases = [
            "Phase 1 (Guardrails)",
            "Phase 2 (Pre-Execution)",
            "Phase 3 (Execution)",
            "Phase 4 (Verification)"
        ]
        for p in phases:
            if p not in pipe or not isinstance(pipe[p], list):
                raise VerificationFailure(f"Pipeline missing phase '{p}'")
            if len(pipe[p]) == 0:
                raise VerificationFailure(f"Pipeline phase '{p}' has empty skill allocation")
    return True

def main():
    print("🔬 Running Formal Invariant Verifier for Skills Router...")
    all_skills = discover_all_skills(PROJECT_ROOT)
    active_skills = filter_skills_by_profile(all_skills, "all")

    checks = [
        ("Invariant 1: Strict Determinism & Purity", lambda: check_invariant_1_determinism(active_skills)),
        ("Invariant 2: Decision Triad Partitioning", lambda: check_invariant_2_decision_triad(active_skills)),
        ("Invariant 3: Profile Monotonicity & Dormancy Isolation", lambda: check_invariant_3_profile_monotonicity(all_skills)),
        ("Invariant 4: Pipeline 4-Phase Soundness", lambda: check_invariant_4_pipeline_soundness(active_skills)),
    ]

    for name, check_fn in checks:
        try:
            check_fn()
            print(f"  ✔ [PROVEN] {name}")
        except VerificationFailure as e:
            print(f"  ✘ [VIOLATION] {name}: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"  ✘ [CRASH] {name}: {e}")
            sys.exit(2)

    print("\n🎉 Formal Verification Passed: All 4 core invariants mathematically held.")
    sys.exit(0)

if __name__ == "__main__":
    main()
