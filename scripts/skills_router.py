#!/usr/bin/env python3
"""
skills_router.py — Dairy Sathi V5 Enhanced Skills Router & Lifecycle Manager

Synthesizes the deterministic two-stage routing engine from coderdoctor97/skill-router
with the non-vectorized Agentic Search and progressive disclosure from legendtkl/agentic-skill-router.

Commands:
    python3 scripts/skills_router.py sync [--root .]
    python3 scripts/skills_router.py route "<query>" [--root .] [--debug]
    python3 scripts/skills_router.py benchmark [--root .]
    python3 scripts/skills_router.py list [--root .]
    python3 scripts/skills_router.py disable <skill-id> [--yes]
    python3 scripts/skills_router.py enable <skill-id>
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration & Scoring Constants
# ---------------------------------------------------------------------------
CONFIG = {
    "filter_floor": 0.15,      # Cheap Stage A threshold
    "max_candidates": 15,      # Candidate cap for Stage B
    "route_floor": 0.45,       # Min confidence to ROUTE
    "no_route_floor": 0.14,    # Below this is NO_ROUTE
    "ambiguity_gap": 0.15,     # Gap between 1st & 2nd candidate
    "multi_floor": 0.33,       # Min confidence to join multi-skill plan
    "multi_cap": 4,            # Max skills in one plan
    "conflict_penalty": 0.30,  # Penalty for conflicting competitor
    "not_when_penalty": 0.60,  # Soft penalty for negative trigger match
    "not_when_disqualify": 0.15, # Hard disqualification multiplier
}

STAGE_A_WEIGHTS = {
    "name": 0.60,
    "alias": 0.55,
    "trigger": 0.45,
    "intent": 0.35,
    "keyword": 0.25,
    "capability": 0.20,
    "object": 0.18,
    "action": 0.16,
}

RANK_WEIGHTS = {
    "intent": 0.35,
    "object": 0.18,
    "action": 0.16,
    "capability": 0.16,
    "trigger": 0.14,
    "name_alias": 0.16,
    "domain": 0.16,
    "specificity": 0.08,
}

STOPWORDS = {
    "a", "an", "the", "and", "or", "of", "to", "for", "in", "on", "at", "by",
    "with", "is", "are", "be", "this", "that", "it", "our", "my", "your",
    "from", "as", "into", "through", "about", "using", "use", "make", "run"
}

CATEGORY_MAP = {
    # 1. Planning
    "brainstorming": "1. Planning",
    "writing-plans": "1. Planning",
    "master-implementation-planning": "1. Planning",
    "master-prd-engineering": "1. Planning",
    "idea-to-blueprint": "1. Planning",
    "planning-and-task-breakdown": "1. Planning",
    "architecture-decision-records": "1. Planning",
    "senior-architect": "1. Planning",
    "product-manager-toolkit": "1. Planning",
    "spec-driven-development": "1. Planning",
    "to-prd": "1. Planning",

    # 2. Implementation
    "frontend-architecture": "2. Implementation",
    "frontend-data-contracts": "2. Implementation",
    "frontend-design": "2. Implementation",
    "design-taste-frontend": "2. Implementation",
    "tailwind-patterns": "2. Implementation",
    "react-best-practices": "2. Implementation",
    "zod-validation-expert": "2. Implementation",
    "zustand-store-ts": "2. Implementation",
    "clean-code": "2. Implementation",
    "modern-web-guidance": "2. Implementation",
    "chrome-extensions": "2. Implementation",
    "gemini-api-dev": "2. Implementation",
    "gemini-live-api-dev": "2. Implementation",
    "gemini-omni-flash-api": "2. Implementation",
    "hallmark": "2. Implementation",

    # 3. Debugging & Verification
    "test-driven-development": "3. Debugging & Verification",
    "verification-before-completion": "3. Debugging & Verification",
    "systematic-debugging": "3. Debugging & Verification",
    "chrome-devtools": "3. Debugging & Verification",
    "a11y-debugging": "3. Debugging & Verification",
    "troubleshooting": "3. Debugging & Verification",
    "cookie-debugging": "3. Debugging & Verification",
    "debug-optimize-lcp": "3. Debugging & Verification",
    "memory-leak-debugging": "3. Debugging & Verification",
    "code-review-and-quality": "3. Debugging & Verification",
    "code-review-checklist": "3. Debugging & Verification",
    "receiving-code-review": "3. Debugging & Verification",
    "requesting-code-review": "3. Debugging & Verification",
    "frontend-lighthouse": "3. Debugging & Verification",
    "performance-optimization": "3. Debugging & Verification",

    # 4. Token Economy
    "agent-memory-discipline": "4. Token Economy",
    "tokenleak": "4. Token Economy",
    "context-compression": "4. Token Economy",
    "context-degradation": "4. Token Economy",
    "context-engineering": "4. Token Economy",
    "context-window-management": "4. Token Economy",
    "geminiignore-finops": "4. Token Economy",
    "zipai-optimizer": "4. Token Economy",
    "corpus-reconciliation-synthesis": "4. Token Economy",
    "deep-research": "4. Token Economy",

    # 5. Domain & Infrastructure
    "dairy-agritech-domain": "5. Domain & Infrastructure",
    "database-design": "5. Domain & Infrastructure",
    "progressive-web-app": "5. Domain & Infrastructure",
    "android-cli": "5. Domain & Infrastructure",
    "android-device-hub": "5. Domain & Infrastructure",
    "compose-preview": "5. Domain & Infrastructure",
    "retrieving-developer-knowledge": "5. Domain & Infrastructure",

    # 6. Meta & Authoring
    "skills-manager": "6. Meta & Authoring",
    "writing-skills": "6. Meta & Authoring",
    "using-superpowers": "6. Meta & Authoring",
    "diagnosing-superpowers": "6. Meta & Authoring",
    "dispatching-parallel-agents": "6. Meta & Authoring",
    "executing-plans": "6. Meta & Authoring",
    "finishing-a-development-branch": "6. Meta & Authoring",
    "subagent-driven-development": "6. Meta & Authoring",
    "using-git-worktrees": "6. Meta & Authoring",
    "multi-agent-task-orchestrator": "6. Meta & Authoring",
    "documentation-templates": "6. Meta & Authoring",
}

# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------
@dataclass
class SkillRecord:
    name: str
    description: str
    source_path: str
    scope: str
    category: str
    priority: int
    is_override: bool = False
    is_disabled: bool = False
    aliases: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    capabilities: list[str] = field(default_factory=list)
    use_when: list[str] = field(default_factory=list)
    not_when: list[str] = field(default_factory=list)
    objects: list[str] = field(default_factory=list)
    actions: list[str] = field(default_factory=list)
    conflicts_with: list[str] = field(default_factory=list)
    domains: list[str] = field(default_factory=list)
    commands: list[str] = field(default_factory=list)
    intents: dict[str, list[str]] = field(default_factory=dict)

# ---------------------------------------------------------------------------
# Normalization & Text Processing
# ---------------------------------------------------------------------------
def tokenize(text: str) -> list[str]:
    """Tokenize and normalize text, stripping punctuation and common noise."""
    tokens = re.findall(r"[a-z0-9_-]+", text.lower())
    return [t for t in tokens if t not in STOPWORDS and len(t) > 1]

def credit_ratio(phrase: str, request_tokens: set[str]) -> float:
    """Multi-token phrase coverage. Multi-token phrases require >=2 tokens to avoid noise."""
    p_tokens = tokenize(phrase)
    if not p_tokens:
        return 0.0
    matched = [t for t in p_tokens if t in request_tokens]
    if len(p_tokens) > 1 and len(matched) < 2:
        return 0.0
    return len(matched) / len(p_tokens)

def phrase_matches(phrase: str, query_lower: str) -> bool:
    """Accurate boundary phrase match preventing accidental substring collisions."""
    if not phrase:
        return False
    phrase_clean = phrase.strip().lower()
    if len(phrase_clean) <= 1:
        return False
    pattern = r"(?:^|[\s\-_.,;:'\"/\\()[\]{}])" + re.escape(phrase_clean) + r"(?:$|[\s\-_.,;:'\"/\\()[\]{}])"
    return bool(re.search(pattern, query_lower))

# ---------------------------------------------------------------------------
# Discovery & Sync Engine
# ---------------------------------------------------------------------------
def extract_metadata(skill_file: Path) -> dict:
    """Extract YAML frontmatter and manifest metadata from SKILL.md and optional manifest.json."""
    data = {
        "name": "",
        "description": "",
        "aliases": [],
        "keywords": [],
        "capabilities": [],
        "use_when": [],
        "not_when": [],
        "objects": [],
        "actions": [],
        "conflicts_with": [],
        "domains": [],
        "commands": [],
        "intents": {},
    }
    
    # 1. Inspect SKILL.md frontmatter
    try:
        with open(skill_file, "r", encoding="utf-8", errors="ignore") as f:
            lines = [f.readline() for _ in range(40)]
        in_fm = 0
        desc_lines = []
        capture_desc = False
        for line in lines:
            line_str = line.strip()
            if line_str == "---":
                in_fm += 1
                if in_fm == 2:
                    break
                continue
            if in_fm == 1:
                if line_str.startswith("name:"):
                    data["name"] = line_str[5:].strip().strip("\"'")
                    capture_desc = False
                elif line_str.startswith("description:"):
                    raw_desc = line_str[12:].strip().strip("\"'").lstrip(">-").strip()
                    desc_lines.append(raw_desc)
                    capture_desc = True
                elif line_str.startswith("commands:"):
                    raw_cmds = line_str[9:].strip().strip("[]\"'")
                    data["commands"] = [c.strip().strip("\"'") for c in raw_cmds.split(",") if c.strip()]
                    capture_desc = False
                elif capture_desc:
                    if re.match(r"^[a-zA-Z0-9_-]+:", line_str):
                        capture_desc = False
                    else:
                        desc_lines.append(line_str.strip("\"'"))
        data["description"] = " ".join([d for d in desc_lines if d]).strip()
    except Exception:
        pass

    if not data["name"]:
        data["name"] = skill_file.parent.name

    name = data["name"]
    desc = data["description"]
    desc_lower = desc.lower()

    # Extract automatic initials/acronyms for hyphenated names (e.g., test-driven-development -> tdd)
    parts = name.split("-")
    if len(parts) >= 2:
        acronym = "".join(p[0] for p in parts if p)
        if len(acronym) >= 2 and acronym not in data["aliases"]:
            data["aliases"].append(acronym)

    # Automatically extract use_when from description if present
    if "use when" in desc_lower:
        idx = desc_lower.find("use when")
        snippet = desc[idx + 8:].split(".")[0].strip()
        clauses = re.split(r"[,;]|\bor\b|\band\b", snippet)
        for c in clauses:
            clean_c = c.strip()
            if len(clean_c) > 3 and clean_c not in data["use_when"]:
                data["use_when"].append(clean_c)

    # 2. Inspect manifest.json if present
    manifest_path = skill_file.parent / "manifest.json"
    if manifest_path.exists():
        try:
            m_data = json.loads(manifest_path.read_text(encoding="utf-8"))
            for key in ["aliases", "keywords", "capabilities", "use_when", "not_when",
                        "objects", "actions", "conflicts_with", "domains"]:
                if key in m_data and isinstance(m_data[key], list):
                    data[key].extend(m_data[key])
            if "intents" in m_data and isinstance(m_data["intents"], dict):
                data["intents"].update(m_data["intents"])
            if "commands" in m_data and isinstance(m_data["commands"], list):
                for cmd in m_data["commands"]:
                    cname = cmd if isinstance(cmd, str) else cmd.get("name")
                    if cname and cname not in data["commands"]:
                        data["commands"].append(cname)
        except Exception:
            pass

    # 3. Seed domain-specific heuristic tags for Dairy Sathi V5
    if name == "dairy-agritech-domain":
        data["objects"].extend(["milk", "cow", "buffalo", "cattle", "gestation", "snf", "fat", "insemination", "calving", "evp", "vaccine", "pregnancy", "breeding"])
        data["actions"].extend(["calculate", "verify", "gate", "formula", "quarantine", "lock", "record", "breed"])
        data["domains"].extend(["agritech", "biology", "dairy"])
        data["use_when"].extend(["biological calculation", "gestation window", "snf formula", "milk withdrawal", "pregnancy check", "cattle breeding", "breeding cycle"])
        data["intents"]["gestation"] = ["calculate gestation", "gestation window", "pregnancy check date", "calving date"]
        data["intents"]["snf"] = ["snf calculation", "richmond formula", "fat snf rate"]
        data["intents"]["breeding"] = ["cattle breeding", "breeding cycle", "breeding tables"]
    elif name in ("frontend-design", "design-taste-frontend"):
        data["objects"].extend(["screen", "view", "ui", "modal", "card", "typography", "palette", "sunlight", "night vision", "landing page", "layout"])
        data["actions"].extend(["design", "style", "layout", "wireframe", "beautify", "redesign"])
        data["domains"].extend(["ui", "frontend", "ergonomics", "design"])
        data["use_when"].extend(["design new ui", "barn ergonomics", "sunlight mode", "touch target", "redesign layout", "landing page"])
        data["intents"]["redesign"] = ["redesign landing page", "redesign layout", "new page design"]
    elif name == "hallmark":
        data["objects"].extend(["website", "page", "landing page", "layout", "theme"])
        data["actions"].extend(["design", "redesign", "build"])
        data["domains"].extend(["design", "ui"])
        data["use_when"].extend(["redesign landing page", "design website", "new page design"])
    elif name == "zod-validation-expert":
        data["objects"].extend(["schema", "form", "validation", "input", "error", "zod"])
        data["actions"].extend(["validate", "refine", "bind", "check"])
        data["domains"].extend(["data", "form", "validation"])
        data["use_when"].extend(["form validation", "zod schema", "input validation"])
    elif name == "database-design":
        data["objects"].extend(["dexie", "indexeddb", "database", "table", "tables", "store", "index", "persistence", "storage", "migration", "schema"])
        data["actions"].extend(["persist", "store", "save", "query", "migrate", "migration"])
        data["domains"].extend(["database", "offline", "storage"])
        data["use_when"].extend(["dexie persistence", "indexeddb store", "database table", "dexie migration", "schema migration"])
        data["intents"]["migration"] = ["dexie migration", "schema migration", "database migration"]
    elif name in ("chrome-devtools", "a11y-debugging"):
        data["objects"].extend(["browser", "dom", "touch target", "wcag", "contrast", "console", "viewport", "mobile viewport"])
        data["actions"].extend(["test", "inspect", "audit", "automate", "verify", "screenshot"])
        data["domains"].extend(["browser", "e2e", "accessibility", "a11y"])
        data["use_when"].extend(["browser automation", "audit viewport", "touch target check", "wcag contrast"])
    elif name == "test-driven-development":
        data["objects"].extend(["test", "unit test", "spec", "suite", "model", "reproduction"])
        data["actions"].extend(["test", "assert", "red", "green", "refactor", "run tests"])
        data["domains"].extend(["testing", "tdd"])
        data["use_when"].extend(["tdd unit tests", "write tests first", "test-driven development", "strict tdd"])
    elif name == "progressive-web-app":
        data["objects"].extend(["pwa", "service worker", "workbox", "cache", "offline", "manifest"])
        data["actions"].extend(["cache", "offline", "sync", "install"])
        data["domains"].extend(["pwa", "offline", "web"])
        data["use_when"].extend(["offline pwa", "service worker cache", "offline support"])

    return data

def discover_all_skills(project_root: Path) -> dict[str, SkillRecord]:
    """Scan project and global paths with strict precedence and deduplication."""
    home = Path(os.environ.get("HOME", "/data/user/0/com.termux/files/home"))
    search_dirs = [
        (100, "Project", project_root / ".agents" / "skills"),
        (95, "Project", project_root / "skills"),
        (90, "Project", project_root / ".antigravity" / "skills"),
        (50, "Global", home / ".gemini" / "config" / "plugins"),
        (45, "Global", home / ".config" / "opencode" / "skills"),
        (40, "Global", home / ".claude" / "skills"),
    ]

    registry: dict[str, SkillRecord] = {}

    for priority, scope, s_dir in search_dirs:
        if not s_dir.exists():
            continue
        for root, _, files in os.walk(s_dir):
            skill_filename = None
            is_disabled = False
            if "SKILL.md" in files:
                skill_filename = "SKILL.md"
            elif "SKILL.md.disabled" in files:
                skill_filename = "SKILL.md.disabled"
                is_disabled = True
            
            if not skill_filename:
                continue

            skill_path = Path(root) / skill_filename
            meta = extract_metadata(skill_path)
            name = meta["name"]
            if not name:
                continue

            try:
                rel_path = f"./{skill_path.relative_to(project_root)}"
            except ValueError:
                try:
                    rel_path = f"~/{skill_path.relative_to(home)}"
                except ValueError:
                    rel_path = str(skill_path)

            cat = CATEGORY_MAP.get(name)
            if not cat:
                if name.startswith("gsd-") or "plan" in name or "prd" in name:
                    cat = "1. Planning"
                elif "test" in name or "debug" in name or "review" in name:
                    cat = "3. Debugging & Verification"
                elif "token" in name or "context" in name:
                    cat = "4. Token Economy"
                elif "domain" in name or "db" in name or "pwa" in name:
                    cat = "5. Domain & Infrastructure"
                elif "agent" in name or "superpower" in name or "skill" in name:
                    cat = "6. Meta & Authoring"
                else:
                    cat = "2. Implementation"

            rec = SkillRecord(
                name=name,
                description=meta["description"],
                source_path=rel_path,
                scope=scope,
                category=cat,
                priority=priority,
                is_disabled=is_disabled,
                aliases=meta["aliases"],
                keywords=meta["keywords"],
                capabilities=meta["capabilities"],
                use_when=meta["use_when"],
                not_when=meta["not_when"],
                objects=meta["objects"],
                actions=meta["actions"],
                conflicts_with=meta["conflicts_with"],
                domains=meta["domains"],
                commands=meta["commands"],
                intents=meta["intents"],
            )

            if name in registry:
                if priority > registry[name].priority:
                    rec.is_override = True
                    registry[name] = rec
                elif scope == "Global" and registry[name].scope == "Project":
                    registry[name].is_override = True
            else:
                registry[name] = rec

    return registry

# ---------------------------------------------------------------------------
# Two-Stage Deterministic Routing Engine
# ---------------------------------------------------------------------------
@dataclass
class ScoredCandidate:
    skill: SkillRecord
    cheap_score: float = 0.0
    rank_score: float = 0.0
    confidence: float = 0.0
    evidence: list[str] = field(default_factory=list)
    penalties: list[str] = field(default_factory=list)
    components: dict[str, float] = field(default_factory=dict)
    matched_object: str | None = None
    matched_action: str | None = None

def route_query(query: str, registry: dict[str, SkillRecord], debug: bool = False) -> dict:
    """Execute two-stage deterministic routing over the discovered skill registry."""
    req_tokens = set(tokenize(query))
    if not req_tokens:
        return {
            "decision": "no_route",
            "status": "no_match",
            "skill": None,
            "skills": [],
            "command": None,
            "confidence": 0.0,
            "evidence": "empty query",
            "validated": False,
            "pipeline": {}
        }

    # -----------------------------------------------------------------------
    # STAGE A: Cheap Candidate Filter (whole library -> <= 15 candidates)
    # -----------------------------------------------------------------------
    candidates: list[ScoredCandidate] = []
    query_lower = query.lower()

    for skill in registry.values():
        if skill.is_disabled:
            continue
        c_score = 0.0
        s_name = skill.name.lower()
        
        # Name match
        if phrase_matches(s_name, query_lower) or phrase_matches(s_name.replace("-", " "), query_lower):
            c_score += STAGE_A_WEIGHTS["name"]
        
        # Alias match
        for alias in skill.aliases:
            if phrase_matches(alias, query_lower):
                c_score += STAGE_A_WEIGHTS["alias"]
                break
                
        # Trigger coverage
        for trig in skill.use_when:
            ratio = credit_ratio(trig, req_tokens)
            if ratio >= 0.5:
                c_score += STAGE_A_WEIGHTS["trigger"] * ratio
                break
                
        # Object match
        for obj in skill.objects:
            if phrase_matches(obj, query_lower) or credit_ratio(obj, req_tokens) >= 0.5:
                c_score += STAGE_A_WEIGHTS["object"]
                break
                
        # Action match
        for act in skill.actions:
            if phrase_matches(act, query_lower) or credit_ratio(act, req_tokens) >= 0.5:
                c_score += STAGE_A_WEIGHTS["action"]
                break

        # Keyword match
        for kw in skill.keywords:
            if phrase_matches(kw, query_lower):
                c_score += STAGE_A_WEIGHTS["keyword"]
                break

        if c_score >= CONFIG["filter_floor"]:
            candidates.append(ScoredCandidate(skill=skill, cheap_score=c_score))

    candidates.sort(key=lambda c: c.cheap_score, reverse=True)
    candidates = candidates[:int(CONFIG["max_candidates"])]

    if not candidates:
        return {
            "decision": "no_route",
            "status": "no_match",
            "skill": None,
            "skills": [],
            "command": None,
            "confidence": 0.0,
            "evidence": "no candidate passed Stage A filter",
            "validated": False,
            "pipeline": {}
        }

    # -----------------------------------------------------------------------
    # STAGE B: Structured Semantic Ranking (candidates only)
    # -----------------------------------------------------------------------
    for cand in candidates:
        s = cand.skill
        s_name = s.name.lower()
        evidence_parts = []
        components = {}

        # 1. Intent match
        intent_score = 0.0
        for intent_id, phrases in s.intents.items():
            for phrase in phrases:
                ratio = credit_ratio(phrase, req_tokens)
                if ratio >= 0.5:
                    intent_score = max(intent_score, ratio)
                    evidence_parts.append(f"intent '{phrase}'")
        components["intent"] = intent_score

        # 2. Object match
        obj_score = 0.0
        matched_obj = None
        for obj in s.objects:
            if phrase_matches(obj, query_lower) or credit_ratio(obj, req_tokens) >= 0.5:
                obj_score = 1.0
                matched_obj = obj
                evidence_parts.append(f"object '{obj}'")
                break
        components["object"] = obj_score
        cand.matched_object = matched_obj

        # 3. Action match
        act_score = 0.0
        matched_act = None
        for act in s.actions:
            if phrase_matches(act, query_lower) or credit_ratio(act, req_tokens) >= 0.5:
                act_score = 1.0
                matched_act = act
                evidence_parts.append(f"action '{act}'")
                break
        components["action"] = act_score
        cand.matched_action = matched_act

        # 4. Capability match
        cap_score = 0.0
        for cap in s.capabilities:
            ratio = credit_ratio(cap, req_tokens)
            if ratio >= 0.5:
                cap_score = max(cap_score, ratio)
                evidence_parts.append(f"capability '{cap}'")
                break
        components["capability"] = cap_score

        # 5. Trigger strength
        trig_score = 0.0
        for trig in s.use_when:
            ratio = credit_ratio(trig, req_tokens)
            if ratio >= 0.5:
                trig_score = max(trig_score, min(0.9, ratio * (0.4 + 0.12 * len(tokenize(trig)))))
                evidence_parts.append(f"trigger '{trig}'")
                break
        components["trigger"] = trig_score

        # 6. Name / Alias
        name_score = 0.0
        if phrase_matches(s_name, query_lower) or phrase_matches(s_name.replace("-", " "), query_lower):
            name_score = 1.0
            evidence_parts.append(f"name '{s.name}'")
        else:
            for alias in s.aliases:
                if phrase_matches(alias, query_lower):
                    name_score = 0.9
                    evidence_parts.append(f"alias '{alias}'")
                    break
        components["name_alias"] = name_score

        # 7. Domain match
        dom_score = 0.0
        for dom in s.domains:
            if phrase_matches(dom, query_lower):
                dom_score = 1.0
                evidence_parts.append(f"domain '{dom}'")
                break
        components["domain"] = dom_score

        # 8. Specificity
        spec_score = min(1.0, len(evidence_parts) * 0.2)
        components["specificity"] = spec_score

        # Raw confidence calculation
        norm_sum = sum(RANK_WEIGHTS.values())
        raw_conf = sum(components[dim] * RANK_WEIGHTS[dim] for dim in RANK_WEIGHTS) / norm_sum

        # Anti-adversarial Anchor Check: Name bonus requires task-identity anchor (obj, intent, or domain)
        if name_score > 0 and (obj_score > 0 or intent_score > 0 or dom_score > 0):
            raw_conf += 0.25

        cand.rank_score = raw_conf
        cand.confidence = raw_conf
        cand.evidence = evidence_parts
        cand.components = components

    # -----------------------------------------------------------------------
    # Defensive Penalties (3 Passes)
    # -----------------------------------------------------------------------
    for cand in candidates:
        s = cand.skill
        # Pass 1: negative triggers (not_when)
        for nw in s.not_when:
            if credit_ratio(nw, req_tokens) >= 0.6:
                if (cand.components.get("intent", 0) + cand.components.get("object", 0)) < 0.2:
                    cand.confidence *= CONFIG["not_when_disqualify"]
                    cand.penalties.append(f"disqualified_not_when:{nw}")
                else:
                    cand.confidence *= CONFIG["not_when_penalty"]
                    cand.penalties.append(f"soft_penalty_not_when:{nw}")

        # Pass 2: Object mismatch penalty
        if s.objects and not cand.matched_object:
            cand.confidence *= 0.85
            cand.penalties.append("object_mismatch")

    # Pass 3: Conflicts-with competition penalty
    candidates.sort(key=lambda c: c.confidence, reverse=True)
    best_conf = candidates[0].confidence if candidates else 0.0
    for cand in candidates:
        for other in candidates:
            if other.skill.name in cand.skill.conflicts_with:
                if other.confidence >= max(0.30, best_conf - 0.10):
                    cand.confidence -= CONFIG["conflict_penalty"]
                    cand.penalties.append(f"conflict_with:{other.skill.name}")
                    break

    candidates.sort(key=lambda c: c.confidence, reverse=True)
    winner = candidates[0]
    second = candidates[1] if len(candidates) > 1 else None

    def format_cand(c: ScoredCandidate) -> dict:
        return {
            "name": c.skill.name,
            "confidence": round(c.confidence, 3),
            "cheap_score": round(c.cheap_score, 3),
            "rank_score": round(c.rank_score, 3),
            "evidence": c.evidence,
            "penalties": c.penalties,
            "components": {k: round(v, 3) for k, v in c.components.items()}
        }

    def generate_skills_summary(selected_candidates: list[ScoredCandidate]) -> list[dict]:
        summary = []
        for c in selected_candidates:
            reason = c.matched_object or c.skill.category
            if c.evidence:
                reason = c.evidence[0]
            summary.append({
                "skill": c.skill.name,
                "reason": reason
            })
        return summary

    def format_skills_applied_markdown(summary: list[dict]) -> str:
        lines = ["> 🛠️ **Skills Applied:**"]
        for s in summary:
            lines.append(f"> - `{s['skill']}`: {s['reason']}")
        return "\n".join(lines)

    # -----------------------------------------------------------------------
    # Multi-Skill Plan Assembly
    # -----------------------------------------------------------------------
    multi_plan = []
    seen_skills = set()
    seen_categories = set()
    seen_objects = set()
    for cand in candidates:
        if cand.confidence >= CONFIG["multi_floor"] and len(multi_plan) < CONFIG["multi_cap"]:
            s_name = cand.skill.name
            cat = cand.skill.category
            cand_obj = cand.matched_object
            if s_name not in seen_skills:
                # Disallow conflicting skills in one plan
                if any(other.skill.name in cand.skill.conflicts_with for other in multi_plan):
                    continue
                # Join if category is unique OR matched distinct object
                if cat not in seen_categories or (cand_obj and cand_obj not in seen_objects):
                    multi_plan.append(cand)
                    seen_skills.add(s_name)
                    seen_categories.add(cat)
                    if cand_obj:
                        seen_objects.add(cand_obj)

    # -----------------------------------------------------------------------
    # Decision Formation
    # -----------------------------------------------------------------------
    raw_words = set(re.findall(r"[a-z0-9&]+", query_lower))
    has_conjunction = bool(raw_words & {"and", "then", "with", "plus", "also", "&"})

    # Check for multi-skill plan first if task explicitly connects multiple facets
    if len(multi_plan) >= 2 and has_conjunction:
        skill_names = [m.skill.name for m in multi_plan]
        summary = generate_skills_summary(multi_plan)
        return {
            "decision": "route",
            "status": "multi_skill_plan",
            "skill": skill_names[0],
            "skills": skill_names,
            "skills_summary": summary,
            "skills_applied_text": format_skills_applied_markdown(summary),
            "command": multi_plan[0].skill.commands[0] if multi_plan[0].skill.commands else None,
            "confidence": round(winner.confidence, 3),
            "evidence": "; ".join(winner.evidence),
            "validated": True,
            "pipeline": build_pipeline_declaration(multi_plan),
            "debug": [format_cand(c) for c in candidates[:5]] if debug else None
        }

    # Single ROUTE
    if winner.confidence >= CONFIG["route_floor"]:
        if not second or (winner.confidence - second.confidence) > CONFIG["ambiguity_gap"]:
            cmd = winner.skill.commands[0] if winner.skill.commands else None
            summary = generate_skills_summary([winner])
            return {
                "decision": "route",
                "status": "matched",
                "skill": winner.skill.name,
                "skills": [winner.skill.name],
                "skills_summary": summary,
                "skills_applied_text": format_skills_applied_markdown(summary),
                "command": cmd,
                "confidence": round(winner.confidence, 3),
                "evidence": "; ".join(winner.evidence),
                "alternative": second.skill.name if second else None,
                "validated": bool(cmd),
                "pipeline": build_pipeline_declaration([winner]),
                "debug": [format_cand(c) for c in candidates[:5]] if debug else None
            }

    # AMBIGUOUS
    if winner.confidence >= CONFIG["no_route_floor"] and second:
        alt_names = [c.skill.name for c in candidates[:3]]
        return {
            "decision": "ambiguous",
            "status": "ambiguous",
            "skill": None,
            "skills": alt_names,
            "skills_summary": [],
            "skills_applied_text": "",
            "command": None,
            "confidence": round(winner.confidence, 3),
            "evidence": f"near tie between {winner.skill.name} ({round(winner.confidence, 2)}) and {second.skill.name} ({round(second.confidence, 2)})",
            "alternatives": alt_names,
            "validated": False,
            "pipeline": {},
            "debug": [format_cand(c) for c in candidates[:5]] if debug else None
        }

    # NO_ROUTE
    return {
        "decision": "no_route",
        "status": "no_match",
        "skill": None,
        "skills": [],
        "skills_summary": [],
        "skills_applied_text": "",
        "command": None,
        "confidence": round(winner.confidence, 3),
        "evidence": f"best score {round(winner.confidence, 2)} fell below floor {CONFIG['no_route_floor']}",
        "validated": False,
        "pipeline": {},
        "debug": [format_cand(c) for c in candidates[:5]] if debug else None
    }

def build_pipeline_declaration(selected_candidates: list[ScoredCandidate]) -> dict:
    """Format canonical 4-phase execution pipeline."""
    guardrails = ["using-superpowers", "agent-memory-discipline", "tokenleak"]
    pre_exec = []
    exec_skills = []
    verify_skills = ["verification-before-completion"]

    for c in selected_candidates:
        name = c.skill.name
        cat = c.skill.category
        if "Planning" in cat:
            pre_exec.append(name)
        elif "Implementation" in cat or "Domain" in cat:
            exec_skills.append(name)
        elif "Debugging" in cat or "Verification" in cat:
            verify_skills.append(name)
        else:
            pre_exec.append(name)

    if not pre_exec:
        pre_exec = ["writing-plans"]
    if not exec_skills:
        exec_skills = ["test-driven-development"]

    return {
        "Phase 1 (Guardrails)": guardrails,
        "Phase 2 (Pre-Execution)": list(dict.fromkeys(pre_exec)),
        "Phase 3 (Execution)": list(dict.fromkeys(exec_skills)),
        "Phase 4 (Verification)": list(dict.fromkeys(verify_skills)),
    }

# ---------------------------------------------------------------------------
# CLI & Command Handlers
# ---------------------------------------------------------------------------
def cmd_sync(project_root: Path) -> int:
    """Rebuild SKILLS_REGISTRY.md and skill-registry/routing-manifest.json."""
    print(f"Scanning skills across project and global paths for {project_root.name}...")
    registry = discover_all_skills(project_root)
    
    # 1. Generate routing-manifest.json
    reg_dir = project_root / "skill-registry"
    reg_dir.mkdir(parents=True, exist_ok=True)
    manifest_data = {
        "version": 2,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_skills": len(registry),
        "skills": {name: s.__dict__ for name, s in registry.items()}
    }
    (reg_dir / "routing-manifest.json").write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")
    
    # 2. Generate SKILLS_REGISTRY.md
    cats = {
        "1. Planning": [],
        "2. Implementation": [],
        "3. Debugging & Verification": [],
        "4. Token Economy": [],
        "5. Domain & Infrastructure": [],
        "6. Meta & Authoring": []
    }
    for item in registry.values():
        cats.get(item.category, cats["2. Implementation"]).append(item)

    lines = [
        "# Project Skills Registry — Dairy Sathi V5",
        "",
        "> **Auto-generated by `@skills-manager` (Enhanced Two-Stage Router)**  ",
        f"> **Total Active Skills:** {len(registry)} | **Project:** {sum(1 for s in registry.values() if s.scope == 'Project')} | **Global:** {sum(1 for s in registry.values() if s.scope == 'Global')}  ",
        f"> **Project Overrides:** {sum(1 for s in registry.values() if s.is_override)}",
        "",
        "---",
        ""
    ]

    for cat_name, skills in cats.items():
        lines.append(f"## {cat_name}\n")
        lines.append("| Skill | Scope | Source Path | Trigger Summary |")
        lines.append("|---|---|---|---|")
        for s in sorted(skills, key=lambda x: x.name):
            sc = s.scope
            if s.is_override:
                sc += " **[Override]**"
            if s.is_disabled:
                sc += " *(Disabled)*"
            desc = s.description.replace("\n", " ").replace("|", "/")
            if len(desc) > 85:
                desc = desc[:82] + "..."
            lines.append(f"| `{s.name}` | {sc} | `{s.source_path}` | {desc or 'See skill doc.'} |")
        lines.append("")

    (project_root / "SKILLS_REGISTRY.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"✔ Successfully synced {len(registry)} skills into SKILLS_REGISTRY.md and skill-registry/routing-manifest.json")
    return 0

def resolve_skill_path(skill: SkillRecord, project_root: Path) -> Path:
    src_str = skill.source_path
    if src_str.startswith("./"):
        return project_root / src_str[2:]
    elif src_str.startswith("~/"):
        return Path.home() / src_str[2:]
    return Path(src_str)

def cmd_disable(skill_id: str, project_root: Path, yes: bool = False) -> int:
    registry = discover_all_skills(project_root)
    if skill_id not in registry:
        print(f"✘ Error: Skill '{skill_id}' not found in registry.", file=sys.stderr)
        return 1
    skill = registry[skill_id]
    src_file = resolve_skill_path(skill, project_root)
    if not src_file.exists():
        print(f"✘ Error: Skill file '{src_file}' does not exist.", file=sys.stderr)
        return 1
    if skill.is_disabled or src_file.name == "SKILL.md.disabled":
        print(f"ℹ Skill '{skill_id}' is already disabled.")
        return 0
    target_file = src_file.parent / "SKILL.md.disabled"
    src_file.rename(target_file)
    print(f"✔ Disabled '{skill_id}': {src_file.name} -> {target_file.name}")
    cmd_sync(project_root)
    return 0

def cmd_enable(skill_id: str, project_root: Path) -> int:
    registry = discover_all_skills(project_root)
    if skill_id not in registry:
        print(f"✘ Error: Skill '{skill_id}' not found in registry.", file=sys.stderr)
        return 1
    skill = registry[skill_id]
    src_file = resolve_skill_path(skill, project_root)
    if not src_file.exists():
        print(f"✘ Error: Skill file '{src_file}' does not exist.", file=sys.stderr)
        return 1
    if not skill.is_disabled and src_file.name == "SKILL.md":
        print(f"ℹ Skill '{skill_id}' is already enabled.")
        return 0
    target_file = src_file.parent / "SKILL.md"
    src_file.rename(target_file)
    print(f"✔ Enabled '{skill_id}': {src_file.name} -> {target_file.name}")
    cmd_sync(project_root)
    return 0

def cmd_route(query: str, project_root: Path, debug: bool = False) -> int:
    registry = discover_all_skills(project_root)
    result = route_query(query, registry, debug=debug)
    print(json.dumps(result, indent=2))
    return 0

def cmd_benchmark(project_root: Path) -> int:
    registry = discover_all_skills(project_root)
    test_cases = [
        ("calculate Cow gestation window and pregnancy check date", "route", ["dairy-agritech-domain"]),
        ("build an offline milk entry form with Dexie persistence and Zod validation", "route", ["frontend-design", "zod-validation-expert", "database-design"]),
        ("audit mobile viewport touch targets and WCAG color contrast with Chrome DevTools", "route", ["chrome-devtools", "a11y-debugging"]),
        ("redesign this landing page layout", "ambiguous", []),
        ("what is the weather in Mumbai today", "no_route", []),
        ("run strict TDD unit tests for reproduction models", "route", ["test-driven-development"]),
    ]
    
    passed = 0
    t0 = time.time()
    for q, exp_dec, exp_skills in test_cases:
        res = route_query(q, registry)
        dec = res["decision"]
        act_skills = res["skills"]
        match = (dec == exp_dec)
        if exp_skills and exp_dec == "route":
            match = match and any(s in act_skills for s in exp_skills)
        if match:
            passed += 1
            print(f"✔ PASS: '{q[:40]}...' -> {dec} {act_skills}")
        else:
            print(f"✘ FAIL: '{q[:40]}...' -> exp {exp_dec}, got {dec} {act_skills}")

    dur_ms = (time.time() - t0) * 1000
    print(f"\nBenchmark Results: {passed}/{len(test_cases)} passed in {dur_ms:.2f} ms ({dur_ms/len(test_cases):.2f} ms/query)")
    return 0 if passed == len(test_cases) else 1

# ---------------------------------------------------------------------------
# Harness Installation Engine
# ---------------------------------------------------------------------------
HARNESS_MAP = {
    "claude": [
        ("CLAUDE.md", "claude-code/CLAUDE.md")
    ],
    "gemini": [
        ("AGENTS.md", "gemini-antigravity/AGENTS.md"),
        ("GEMINI.md", "gemini-antigravity/GEMINI.md")
    ],
    "cursor": [
        (".cursor/rules/skills-router.mdc", "cursor/.cursor/rules/skills-router.mdc"),
        (".cursorrules", "cursor/.cursorrules")
    ],
    "windsurf": [
        (".windsurf/rules/skills-router.md", "windsurf/.windsurf/rules/skills-router.md"),
        (".windsurfrules", "windsurf/.windsurfrules")
    ],
    "roo": [
        (".roo/rules/00-skills-router.md", "roo-cline/.roo/rules/00-skills-router.md"),
        (".clinerules", "roo-cline/.clinerules")
    ],
    "aider": [
        ("CONVENTIONS.md", "aider/CONVENTIONS.md"),
        (".aider.conf.yml", "aider/.aider.conf.yml")
    ]
}

def inject_or_create(target_path: Path, template_text: str) -> str:
    begin_marker = "<!-- skills-manager:routing-contract:begin -->"
    end_marker = "<!-- skills-manager:routing-contract:end -->"

    target_path.parent.mkdir(parents=True, exist_ok=True)
    if not target_path.exists():
        target_path.write_text(template_text, encoding="utf-8")
        return f"created {target_path.name}"

    existing = target_path.read_text(encoding="utf-8")
    if begin_marker in existing and end_marker in existing:
        b_idx = template_text.find(begin_marker)
        e_idx = template_text.find(end_marker) + len(end_marker)
        new_block = template_text[b_idx:e_idx]

        eb_idx = existing.find(begin_marker)
        ee_idx = existing.find(end_marker) + len(end_marker)
        updated = existing[:eb_idx] + new_block + existing[ee_idx:]
        target_path.write_text(updated, encoding="utf-8")
        return f"updated {target_path.name} (idempotent contract replaced)"
    else:
        b_idx = template_text.find(begin_marker)
        e_idx = template_text.find(end_marker) + len(end_marker)
        new_block = template_text[b_idx:e_idx] if begin_marker in template_text else template_text
        updated = existing.rstrip() + "\n\n" + new_block + "\n"
        target_path.write_text(updated, encoding="utf-8")
        return f"updated {target_path.name} (contract appended)"

def cmd_install_harness(harness_names: list[str], target_dir: Path) -> int:
    """Install or update harness integration contracts for AI coding harnesses."""
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent
    tmpl_base = repo_root / "templates" / "harnesses"

    if not harness_names or "all" in [h.lower() for h in harness_names]:
        selected = list(HARNESS_MAP.keys())
    else:
        selected = [h.lower() for h in harness_names if h.lower() in HARNESS_MAP]

    if not selected:
        print(f"✘ Error: Unknown harness(es) '{harness_names}'. Supported: {list(HARNESS_MAP.keys()) + ['all']}", file=sys.stderr)
        return 1

    print(f"Installing harness integration(s) for: {', '.join(selected)} into '{target_dir}'...")
    installed_count = 0
    for h in selected:
        configs = HARNESS_MAP[h]
        for rel_dest, rel_src in configs:
            target_file = target_dir / rel_dest
            src_file = tmpl_base / rel_src
            if src_file.exists():
                tmpl_text = src_file.read_text(encoding="utf-8")
            else:
                tmpl_text = f"# {rel_dest}\n\n<!-- skills-manager:routing-contract:begin -->\n### Skills Router Contract\npython3 scripts/skills_router.py route \"<task>\"\n<!-- skills-manager:routing-contract:end -->\n"
            msg = inject_or_create(target_file, tmpl_text)
            print(f"  ✔ [{h:8}] {msg}")
            installed_count += 1

    print(f"✔ Successfully configured {installed_count} harness files across {len(selected)} agent harness(es).")
    return 0

# ---------------------------------------------------------------------------
# Main CLI Dispatcher
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Dairy Sathi V5 Enhanced Skills Router")
    subparsers = parser.add_subparsers(dest="command")

    # sync
    sync_p = subparsers.add_parser("sync", help="Sync skills and build registry")
    sync_p.add_argument("--root", default=".", help="Project root directory")

    # route
    route_p = subparsers.add_parser("route", help="Route task to skill")
    route_p.add_argument("query", help="Task query string")
    route_p.add_argument("--root", default=".", help="Project root directory")
    route_p.add_argument("--debug", action="store_true", help="Print debug score breakdown")

    # benchmark
    bench_p = subparsers.add_parser("benchmark", help="Run benchmark suite")
    bench_p.add_argument("--root", default=".", help="Project root directory")

    # list
    list_p = subparsers.add_parser("list", help="List discovered skills")
    list_p.add_argument("--root", default=".", help="Project root directory")

    # disable
    dis_p = subparsers.add_parser("disable", help="Disable a skill by renaming SKILL.md to SKILL.md.disabled")
    dis_p.add_argument("skill_id", help="Skill identifier to disable")
    dis_p.add_argument("--root", default=".", help="Project root directory")
    dis_p.add_argument("--yes", action="store_true", help="Confirm without prompting")

    # enable
    ena_p = subparsers.add_parser("enable", help="Enable a dormant skill by renaming SKILL.md.disabled to SKILL.md")
    ena_p.add_argument("skill_id", help="Skill identifier to enable")
    ena_p.add_argument("--root", default=".", help="Project root directory")

    # install-harness
    inst_p = subparsers.add_parser("install-harness", help="Install router integration for major AI agent harnesses")
    inst_p.add_argument("harness", nargs="*", default=["all"], help="Harnesses to configure: claude, gemini, cursor, windsurf, roo, aider, or all")
    inst_p.add_argument("--target", default=".", help="Target project directory")

    args = parser.parse_args()
    root = Path(args.root if hasattr(args, "root") else ".").resolve()

    if args.command == "sync":
        sys.exit(cmd_sync(root))
    elif args.command == "route":
        sys.exit(cmd_route(args.query, root, debug=args.debug))
    elif args.command == "benchmark":
        sys.exit(cmd_benchmark(root))
    elif args.command == "disable":
        sys.exit(cmd_disable(args.skill_id, root, yes=args.yes))
    elif args.command == "enable":
        sys.exit(cmd_enable(args.skill_id, root))
    elif args.command == "install-harness":
        target = Path(args.target).resolve()
        sys.exit(cmd_install_harness(args.harness, target))
    elif args.command == "list":
        reg = discover_all_skills(root)
        for name, s in sorted(reg.items()):
            ov = "[Override]" if s.is_override else ""
            print(f"{name:35} {s.category:25} {s.scope:10} {ov}")
        sys.exit(0)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
