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
import shutil
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

PROFILES = {
    "all": {
        "description": "Full catalog — all discovered skills active",
        "categories": None,
        "include_skills": None,
    },
    "core": {
        "description": "Minimal universal coding — planning, TDD, debugging, review, economy",
        "categories": ["1. Planning", "3. Debugging & Verification", "4. Token Economy", "6. Meta & Authoring"],
        "include_skills": ["chisle", "ponytail", "implement", "handoff", "skills-manager"],
    },
    "web": {
        "description": "Web & Frontend — Core plus Chrome DevTools, CSS/HTML, modern-web, hallmark",
        "categories": ["1. Planning", "3. Debugging & Verification", "4. Token Economy", "6. Meta & Authoring"],
        "include_skills": [
            "chisle", "ponytail", "implement", "handoff", "skills-manager",
            "chrome-devtools", "a11y-debugging", "cookie-debugging", "debug-optimize-lcp",
            "memory-leak-debugging", "troubleshooting", "modern-web-guidance", "chrome-extensions",
            "hallmark", "frontend-design", "design-taste-frontend"
        ],
    },
    "android": {
        "description": "Android Development — Core plus Android CLI, Device Hub, Compose preview",
        "categories": ["1. Planning", "3. Debugging & Verification", "4. Token Economy", "6. Meta & Authoring"],
        "include_skills": [
            "chisle", "ponytail", "implement", "handoff", "skills-manager",
            "android-cli", "android-device-hub", "compose-preview"
        ],
    },
    "ai": {
        "description": "AI & Multimodal SDK — Core plus Gemini media, Live API, Omni Flash",
        "categories": ["1. Planning", "3. Debugging & Verification", "4. Token Economy", "6. Meta & Authoring"],
        "include_skills": [
            "chisle", "ponytail", "implement", "handoff", "skills-manager",
            "gemini-api-cli", "gemini-api-dev", "gemini-live-api-dev", "gemini-omni-flash-api"
        ],
    },
}

HEAVY_SUBAGENT_SKILLS = {
    "chrome-devtools": ("Browser Automation QA", "Prevents high-volume CDP DOM & console log token pollution in root orchestrator"),
    "a11y-debugging": ("Accessibility Auditor", "Isolates WCAG tree inspection and color contrast audits"),
    "memory-leak-debugging": ("Performance Profiler", "Isolates heap snapshot analysis and leak traces"),
    "debug-optimize-lcp": ("CWV Optimizer", "Isolates network waterfall and paint timing diagnostics"),
    "evaluation": ("Evaluation Specialist", "Runs automated test harnesses and LLM-as-judge scoring in clean context"),
    "advanced-evaluation": ("Evaluation Specialist", "Runs pairwise and arena evaluations in isolated subagent"),
    "code-review": ("Code Reviewer", "Executes 2-axis Standards/Spec review without polluting main chat history"),
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
    is_dormant: bool = False
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
    elif name == "skills-manager":
        data["objects"].extend(["skill", "skills", "registry", "router", "manifest", "profile", "lifecycle"])
        data["actions"].extend(["route", "sync", "disable", "enable", "profile", "surface", "benchmark", "deduplicate"])
        data["domains"].extend(["skills", "router", "meta", "lifecycle"])
        data["use_when"].extend(["route task", "sync skill registry", "manage skills", "switch profile", "disable skill", "enable skill"])
        data["intents"]["route"] = ["route task to skill", "skills router route", "pre flight routing"]
        data["intents"]["sync"] = ["sync skill registry", "rebuild skills registry", "rebuild manifest"]
        data["intents"]["profile"] = ["switch profile", "set profile", "surface cluster"]
        data["commands"].extend(["skills-router route", "skills-router sync", "skills-router profile", "skills-router surface"])

    return data

def discover_all_skills(project_root: Path, custom_search_dirs: list[tuple[int, str, Path]] | None = None) -> dict[str, SkillRecord]:
    """Scan project and global paths with strict precedence and deduplication."""
    home = Path(os.environ.get("HOME", "/data/user/0/com.termux/files/home"))
    if custom_search_dirs is not None:
        search_dirs = custom_search_dirs
    else:
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
        for root, dirs, files in os.walk(s_dir):
            dirs.sort()
            files.sort()
            
            # Check if this directory or any parent is .disabled
            try:
                rel_parts = Path(root).relative_to(s_dir).parts
            except ValueError:
                rel_parts = Path(root).parts
            in_disabled_tree = any(p.endswith(".disabled") for p in rel_parts)

            skill_filename = None
            is_disabled = in_disabled_tree
            is_dormant = in_disabled_tree
            if "SKILL.md" in files:
                skill_filename = "SKILL.md"
            elif "SKILL.md.disabled" in files:
                skill_filename = "SKILL.md.disabled"
                is_disabled = True
                is_dormant = True
            
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

            rec_priority = priority - 20 if is_dormant else priority

            rec = SkillRecord(
                name=name,
                description=meta["description"],
                source_path=rel_path,
                scope=scope,
                category=cat,
                priority=rec_priority,
                is_disabled=is_disabled,
                is_dormant=is_dormant,
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
                if rec_priority > registry[name].priority:
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

    def to_dict(self) -> dict:
        return {
            "name": self.skill.name,
            "confidence": round(self.confidence, 3),
            "cheap_score": round(self.cheap_score, 3),
            "rank_score": round(self.rank_score, 3),
            "evidence": self.evidence,
            "penalties": self.penalties,
            "components": {k: round(v, 3) for k, v in self.components.items()}
        }

def resolve_skill_path(skill: SkillRecord, project_root: Path) -> Path:
    src_str = skill.source_path
    if src_str.startswith("./"):
        return project_root / src_str[2:]
    elif src_str.startswith("~/"):
        return Path.home() / src_str[2:]
    return Path(src_str)

def format_cand(c: ScoredCandidate) -> dict:
    return c.to_dict()

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

def extract_hydration_payload(skill: SkillRecord, project_root: Path | None = None) -> dict:
    root = project_root or Path.cwd()
    src_path = resolve_skill_path(skill, root)
    if not src_path.exists():
        p = Path(skill.source_path)
        if p.exists():
            src_path = p
    instructions = ""
    if src_path.exists():
        try:
            instructions = src_path.read_text(encoding="utf-8")
        except Exception:
            instructions = ""
    return {
        "skill": skill.name,
        "source_path": skill.source_path,
        "is_dormant": getattr(skill, "is_dormant", False),
        "instructions": instructions,
        "activation_command": f"skills-router enable {skill.name}" if getattr(skill, "is_dormant", False) else None
    }

def route_query(query: str, registry: dict[str, SkillRecord], debug: bool = False, hydrate: bool = False, project_root: Path | None = None) -> dict:
    """Execute two-stage deterministic routing over the discovered skill registry."""
    raw_query = query.strip()
    slash_match = re.match(r"^/([a-zA-Z0-9_-]+)(?:\s+(.*))?$", raw_query, re.DOTALL)
    if slash_match:
        cmd_name = slash_match.group(1).lower()
        sub_prompt = (slash_match.group(2) or "").strip()
        
        # Check direct skill name match or alias or command
        matched_skill = None
        if cmd_name in registry:
            matched_skill = registry[cmd_name]
        else:
            for s in registry.values():
                if cmd_name in [a.lower() for a in s.aliases] or cmd_name in [c.lower() for c in s.commands]:
                    matched_skill = s
                    break
        
        if matched_skill:
            cand = ScoredCandidate(
                skill=matched_skill,
                cheap_score=1.0,
                rank_score=1.0,
                confidence=1.0,
                evidence=[f"slash command '/{cmd_name}' matched skill '{matched_skill.name}'"]
            )
            summary = generate_skills_summary([cand])
            cmd_val = matched_skill.commands[0] if matched_skill.commands else f"/{cmd_name}"
            res = {
                "decision": "route",
                "status": "slash_command",
                "skill": matched_skill.name,
                "skills": [matched_skill.name],
                "skills_summary": summary,
                "skills_applied_text": format_skills_applied_markdown(summary),
                "command": cmd_val,
                "confidence": 1.0,
                "evidence": f"slash command '/{cmd_name}' matched '{matched_skill.name}'",
                "is_dormant": getattr(matched_skill, "is_dormant", False),
                "validated": True,
                "pipeline": build_pipeline_declaration([cand]),
                "debug": None
            }
            if getattr(matched_skill, "is_dormant", False) or hydrate:
                res["hydration"] = extract_hydration_payload(matched_skill, project_root)
            return res

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
        elif name_score == 1.0 and len(req_tokens) <= 3:
            raw_conf = max(raw_conf, 0.65)

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
            is_dormant = getattr(winner.skill, "is_dormant", False)
            res = {
                "decision": "route",
                "status": "dormant_match" if is_dormant else "matched",
                "skill": winner.skill.name,
                "skills": [winner.skill.name],
                "skills_summary": summary,
                "skills_applied_text": format_skills_applied_markdown(summary),
                "command": cmd,
                "confidence": round(winner.confidence, 3),
                "evidence": "; ".join(winner.evidence),
                "alternative": second.skill.name if second else None,
                "is_dormant": is_dormant,
                "validated": bool(cmd),
                "pipeline": build_pipeline_declaration([winner]),
                "debug": [format_cand(c) for c in candidates[:5]] if debug else None
            }
            if is_dormant or hydrate:
                res["hydration"] = extract_hydration_payload(winner.skill, project_root)
            return res

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
    subagent_offload = []

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

        if name in HEAVY_SUBAGENT_SKILLS:
            role, reason = HEAVY_SUBAGENT_SKILLS[name]
            subagent_offload.append({
                "skill": name,
                "recommended_role": role,
                "isolation": "ephemeral_subagent",
                "reason": reason
            })

    if not pre_exec:
        pre_exec = ["writing-plans"]
    if not exec_skills:
        exec_skills = ["test-driven-development"]

    decl = {
        "Phase 1 (Guardrails)": guardrails,
        "Phase 2 (Pre-Execution)": list(dict.fromkeys(pre_exec)),
        "Phase 3 (Execution)": list(dict.fromkeys(exec_skills)),
        "Phase 4 (Verification)": list(dict.fromkeys(verify_skills)),
    }
    if subagent_offload:
        decl["subagent_offload"] = subagent_offload

    return decl

# ---------------------------------------------------------------------------
# Profile Management & Staging Engine
# ---------------------------------------------------------------------------
def get_active_profile(project_root: Path) -> str:
    prof_file = project_root / ".skills-profile"
    if prof_file.exists():
        val = prof_file.read_text(encoding="utf-8").strip().lower()
        if val in PROFILES:
            return val
    return "all"

def set_active_profile(project_root: Path, profile_name: str) -> bool:
    prof = profile_name.strip().lower()
    if prof not in PROFILES:
        return False
    prof_file = project_root / ".skills-profile"
    if prof == "all":
        if prof_file.exists():
            prof_file.unlink()
    else:
        prof_file.write_text(prof, encoding="utf-8")
    return True

def filter_skills_by_profile(registry: dict[str, SkillRecord], profile_name: str) -> dict[str, SkillRecord]:
    prof = PROFILES.get(profile_name)
    if not prof or prof["categories"] is None:
        return registry
    
    allowed_cats = set(prof["categories"])
    allowed_skills = set(prof.get("include_skills") or [])

    filtered = {}
    for name, s in registry.items():
        if s.scope == "Project":
            filtered[name] = s
        elif s.category in allowed_cats or name in allowed_skills:
            filtered[name] = s
    return filtered

def cmd_profile(profile_name: str | None, project_root: Path) -> int:
    active = get_active_profile(project_root)
    if not profile_name or profile_name == "list":
        print(f"Active Profile: '{active}'\n")
        print("Available Profiles:")
        for p, info in PROFILES.items():
            marker = "* " if p == active else "  "
            print(f" {marker}{p:10} - {info['description']}")
        return 0

    p_norm = profile_name.strip().lower()
    if p_norm in ("reset", "clear", "all"):
        set_active_profile(project_root, "all")
        print("✔ Profile reset to 'all' (all discovered skills active).")
        cmd_sync(project_root)
        return 0

    if p_norm not in PROFILES:
        print(f"✘ Error: Unknown profile '{profile_name}'. Available: {', '.join(PROFILES.keys())}", file=sys.stderr)
        return 1

    set_active_profile(project_root, p_norm)
    print(f"✔ Activated profile '{p_norm}'.")
    cmd_sync(project_root)
    return 0

# ---------------------------------------------------------------------------
# CLI & Command Handlers
# ---------------------------------------------------------------------------
def cmd_sync(project_root: Path) -> int:
    """Rebuild SKILLS_REGISTRY.md and skill-registry/routing-manifest.json."""
    profile = get_active_profile(project_root)
    print(f"Scanning skills across project and global paths for {project_root.name} (profile: {profile})...")
    registry = discover_all_skills(project_root)
    active_skills = filter_skills_by_profile(registry, profile)
    
    # 1. Generate routing-manifest.json
    reg_dir = project_root / "skill-registry"
    reg_dir.mkdir(parents=True, exist_ok=True)
    manifest_data = {
        "version": 2,
        "active_profile": profile,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_skills": len(active_skills),
        "skills": {name: active_skills[name].__dict__ for name in sorted(active_skills.keys())}
    }
    (reg_dir / "routing-manifest.json").write_text(json.dumps(manifest_data, indent=2, sort_keys=True), encoding="utf-8")
    
    # 2. Generate SKILLS_REGISTRY.md
    cats = {
        "1. Planning": [],
        "2. Implementation": [],
        "3. Debugging & Verification": [],
        "4. Token Economy": [],
        "5. Domain & Infrastructure": [],
        "6. Meta & Authoring": []
    }
    for name in sorted(active_skills.keys()):
        item = active_skills[name]
        cats.get(item.category, cats["2. Implementation"]).append(item)

    lines = [
        f"# Project Skills Registry — {project_root.name}",
        "",
        "> **Auto-generated by `@skills-manager` (Enhanced Two-Stage Router)**  ",
        f"> **Active Profile:** `{profile}` | **Total Active Skills:** {len(active_skills)} | **Project:** {sum(1 for s in active_skills.values() if s.scope == 'Project')} | **Global:** {sum(1 for s in active_skills.values() if s.scope == 'Global')}  ",
        f"> **Project Overrides:** {sum(1 for s in active_skills.values() if s.is_override)}",
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

def load_loaded_meta(project_root: Path) -> tuple[Path, dict]:
    """Helper to read .agents/skills/.loaded.json safely."""
    agents_skills_dir = project_root / ".agents" / "skills"
    meta_file = agents_skills_dir / ".loaded.json"
    data = {"loaded": {}}
    if meta_file.exists():
        try:
            parsed = json.loads(meta_file.read_text(encoding="utf-8"))
            if isinstance(parsed, dict) and "loaded" in parsed:
                data = parsed
        except Exception:
            data = {"loaded": {}}
    return meta_file, data

def save_loaded_meta(meta_file: Path, data: dict) -> None:
    """Helper to write .agents/skills/.loaded.json deterministically."""
    meta_file.parent.mkdir(parents=True, exist_ok=True)
    meta_file.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")

def cmd_load(skill_id: str, project_root: Path, custom_search_dirs: list[tuple[int, str, Path]] | None = None) -> int:
    """Load a skill on-demand from global/dormant catalog into project .agents/skills/<skill_id>."""
    registry = discover_all_skills(project_root, custom_search_dirs=custom_search_dirs)
    if skill_id not in registry:
        print(f"✘ Error: Skill '{skill_id}' not found in registry.", file=sys.stderr)
        return 1
    
    skill = registry[skill_id]
    src_file = resolve_skill_path(skill, project_root)
    if not src_file.exists():
        src_path = Path(skill.source_path)
        if src_path.exists():
            src_file = src_path
        else:
            print(f"✘ Error: Source file '{src_file}' does not exist.", file=sys.stderr)
            return 1
            
    src_dir = src_file.parent if src_file.is_file() else src_file
    dest_dir = project_root / ".agents" / "skills" / skill_id
    
    if dest_dir.exists():
        print(f"ℹ Skill '{skill_id}' is already loaded in {dest_dir}.")
        return 0
        
    dest_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src_dir, dest_dir)
    
    # If the source was disabled/dormant (e.g. SKILL.md.disabled), activate it in .agents/skills/
    dormant_skill_md = dest_dir / "SKILL.md.disabled"
    active_skill_md = dest_dir / "SKILL.md"
    if dormant_skill_md.exists() and not active_skill_md.exists():
        dormant_skill_md.rename(active_skill_md)

    # Track in .loaded.json
    meta_file, loaded_data = load_loaded_meta(project_root)
    loaded_data.setdefault("loaded", {})[skill_id] = {
        "loaded_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source": str(src_dir)
    }
    save_loaded_meta(meta_file, loaded_data)
    
    print(f"✔ Successfully loaded '{skill_id}' on-demand into .agents/skills/{skill_id}")
    cmd_sync(project_root)
    return 0

def cmd_offload(skill_id: str | None, project_root: Path, all_loaded: bool = False) -> int:
    """Offload/unload on-demand skills from .agents/skills/ back to dormant state."""
    agents_skills_dir = project_root / ".agents" / "skills"
    meta_file, loaded_data = load_loaded_meta(project_root)
    
    should_offload_all = all_loaded or skill_id in ("--all", "-a", "all") or (skill_id is None)
    if should_offload_all:
        to_remove = list(loaded_data.get("loaded", {}).keys())
        if not to_remove:
            print("ℹ No on-demand loaded skills found to offload.")
            return 0
        for sid in to_remove:
            s_path = agents_skills_dir / sid
            if s_path.exists():
                shutil.rmtree(s_path, ignore_errors=True)
                print(f"✔ Offloaded: '{sid}'")
        loaded_data["loaded"] = {}
        save_loaded_meta(meta_file, loaded_data)
        cmd_sync(project_root)
        print(f"✔ Successfully offloaded all {len(to_remove)} on-demand skills.")
        return 0

    target_dir = agents_skills_dir / skill_id
    if not target_dir.exists():
        print(f"ℹ Skill '{skill_id}' is not loaded in {agents_skills_dir}.")
        return 0
        
    shutil.rmtree(target_dir, ignore_errors=True)
    if "loaded" in loaded_data and skill_id in loaded_data["loaded"]:
        del loaded_data["loaded"][skill_id]
        save_loaded_meta(meta_file, loaded_data)
        
    print(f"✔ Successfully offloaded '{skill_id}' from {agents_skills_dir}")
    cmd_sync(project_root)
    return 0

def detect_project_stack(target_dir: Path) -> tuple[str, str]:
    """Auto-detect project tech stack and return (profile_name, stack_description)."""
    # Android stack detection
    if (
        (target_dir / "android").exists()
        or (target_dir / "build.gradle").exists()
        or (target_dir / "build.gradle.kts").exists()
        or (target_dir / "settings.gradle").exists()
        or (target_dir / "settings.gradle.kts").exists()
        or (target_dir / "app" / "src" / "main" / "AndroidManifest.xml").exists()
    ):
        return "android", "Android (Gradle/Kotlin/Compose)"
        
    # Web / Frontend stack detection
    if (
        (target_dir / "package.json").exists()
        or (target_dir / "tsconfig.json").exists()
        or (target_dir / "pnpm-workspace.yaml").exists()
        or (target_dir / "index.html").exists()
        or (target_dir / "vite.config.ts").exists()
        or (target_dir / "vite.config.js").exists()
    ):
        return "web", "Web / Frontend (JavaScript/TypeScript)"
        
    # Python / Backend stack detection
    if (
        (target_dir / "requirements.txt").exists()
        or (target_dir / "pyproject.toml").exists()
        or (target_dir / "setup.py").exists()
        or (target_dir / "Pipfile").exists()
    ):
        return "core", "Python (Backend/CLI)"
        
    return "core", "Generalist Codebase"

def cmd_init(target_dir: Path, profile: str | None = None) -> int:
    """Initialize a project repository for deterministic skill routing and harness integration."""
    target_dir = target_dir.resolve()
    print(f"Initializing Skills Router in '{target_dir.name}'...")
    
    (target_dir / ".agents" / "skills").mkdir(parents=True, exist_ok=True)
    (target_dir / "skill-registry").mkdir(parents=True, exist_ok=True)
    
    det_prof, stack_desc = detect_project_stack(target_dir)
    chosen_profile = profile if profile and profile in PROFILES else det_prof
    set_active_profile(target_dir, chosen_profile)
    
    # Configure AI harnesses
    cmd_install_harness(["all"], target_dir)
    
    # Rebuild registries deterministically
    cmd_sync(target_dir)
    
    print("\n" + "=" * 60)
    print(f"✔ Skills Router successfully initialized in: {target_dir}")
    print(f"✔ Detected Stack : {stack_desc}")
    print(f"✔ Active Profile : {chosen_profile}")
    print(f"✔ Harness Setup  : Configured across 7 AI agent harnesses")
    print("=" * 60 + "\n")
    return 0

def cmd_session_start(target_dir: Path, cleanup: bool = False) -> int:
    """Pre-flight check and optional ephemeral cleanup for a fresh chat session."""
    target_dir = target_dir.resolve()
    
    # Auto-init if not yet initialized
    if not (target_dir / "skill-registry").exists() or not (target_dir / ".agents" / "skills").exists():
        cmd_init(target_dir)
        
    meta_file, loaded_data = load_loaded_meta(target_dir)
    loaded_count = len(loaded_data.get("loaded", {}))
            
    if cleanup and loaded_count > 0:
        cmd_offload(None, target_dir, all_loaded=True)
        _, loaded_data = load_loaded_meta(target_dir)
        loaded_count = len(loaded_data.get("loaded", {}))
        
    profile = get_active_profile(target_dir)
    reg = discover_all_skills(target_dir)
    filtered_reg = filter_skills_by_profile(reg, profile)
    active_count = sum(1 for s in filtered_reg.values() if not s.is_dormant and not s.is_disabled)
    dormant_count = sum(1 for s in reg.values() if s.is_dormant or s.is_disabled)
    
    receipt = (
        f"✔ Skills Router Ready | Profile: {profile} | "
        f"Active: {active_count} | Dormant: {dormant_count} | On-Demand: {loaded_count}"
    )
    print(receipt)
    return 0

def cmd_route(query: str, project_root: Path, debug: bool = False, hydrate: bool = False) -> int:
    registry = discover_all_skills(project_root)
    profile = get_active_profile(project_root)
    registry = filter_skills_by_profile(registry, profile)
    result = route_query(query, registry, debug=debug, hydrate=hydrate, project_root=project_root)
    print(json.dumps(result, indent=2))
    return 0

def cmd_benchmark(project_root: Path) -> int:
    registry = discover_all_skills(project_root)
    profile = get_active_profile(project_root)
    registry = filter_skills_by_profile(registry, profile)

    test_cases = [
        ("run strict TDD unit tests for reproduction models", "route", ["test-driven-development"]),
        ("audit mobile viewport touch targets and WCAG color contrast with Chrome DevTools", "route", ["chrome-devtools", "a11y-debugging"]),
        ("sync skill registry and route tasks to skills", "route", ["skills-manager"]),
        ("what is the weather in Mumbai today", "no_route", []),
    ]

    # Add project-specific tests if domain skills are present
    if "dairy-agritech-domain" in registry:
        test_cases.append(("calculate Cow gestation window and pregnancy check date", "route", ["dairy-agritech-domain"]))
    if "zod-validation-expert" in registry and "database-design" in registry:
        test_cases.append(("build an offline milk entry form with Dexie persistence and Zod validation", "route", ["frontend-design", "zod-validation-expert", "database-design"]))

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
    ],
    "antigem": []
}

def install_antigem_commands(target_dir: Path) -> str:
    xml_path = Path("/data/user/0/com.termux/shared_prefs/custom_slash_commands.xml")
    if not xml_path.exists():
        xml_path = target_dir / "shared_prefs" / "custom_slash_commands.xml"
    if not xml_path.exists():
        return "skipped (AntiGem shared_prefs not found)"
    try:
        import xml.etree.ElementTree as ET
        tree = ET.parse(xml_path)
        node = tree.getroot().find('.//string[@name="commands"]')
        if node is None or not node.text:
            return "skipped (commands string node missing in XML)"
        commands = json.loads(node.text)
        commands = [c for c in commands if c.get("name") not in ("skills-manager", "route", "route_skills")]

        script_dir = Path(__file__).resolve().parent
        snippet_file = script_dir.parent / "templates" / "harnesses" / "antigem" / "custom_slash_commands_snippet.json"
        if snippet_file.exists():
            new_cmds = json.loads(snippet_file.read_text(encoding="utf-8"))
        else:
            new_cmds = [
                {
                    "name": "skills-manager",
                    "description": "Autonomous Skills Router — discover, route, assemble 4-phase pipeline & report skills",
                    "expansion": "skills-router route \"$ARGUMENTS\"",
                    "pluginId": "",
                    "skill": "skills-manager"
                }
            ]
        commands.extend(new_cmds)
        node.text = json.dumps(commands, indent=2)
        tree.write(str(xml_path), encoding="utf-8", xml_declaration=True)
        return f"updated {xml_path.name} (AntiGem /skills-manager and /route commands registered)"
    except Exception as e:
        return f"failed ({e})"

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
        if h == "antigem":
            msg = install_antigem_commands(target_dir)
            print(f"  ✔ [{h:8}] {msg}")
            installed_count += 1
            continue
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
    route_p.add_argument("--hydrate", action="store_true", help="Include full on-demand skill instructions in output")

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
    inst_p.add_argument("harness", nargs="*", default=["all"], help="Harnesses to configure: claude, gemini, cursor, windsurf, roo, aider, antigem, or all")
    inst_p.add_argument("--target", default=".", help="Target project directory")

    # profile
    prof_p = subparsers.add_parser("profile", help="View or switch skill cluster profiles")
    prof_p.add_argument("name", nargs="?", default=None, help="Profile name to activate (core, web, android, ai, all)")
    prof_p.add_argument("--root", default=".", help="Project root directory")

    # surface (alias for profile)
    surf_p = subparsers.add_parser("surface", help="Alias for profile: surface specific skill cluster")
    surf_p.add_argument("name", nargs="?", default=None, help="Profile name to activate (core, web, android, ai, all)")
    surf_p.add_argument("--root", default=".", help="Project root directory")

    # load
    load_p = subparsers.add_parser("load", help="Load a dormant skill into project on-demand")
    load_p.add_argument("skill_id", help="Skill identifier to load on-demand")
    load_p.add_argument("--root", "--target", dest="root", default=".", help="Project root or target directory")

    # offload
    offload_p = subparsers.add_parser("offload", help="Offload on-demand skills from project back to dormant state")
    offload_p.add_argument("skill_id", nargs="?", default=None, help="Skill identifier to offload")
    offload_p.add_argument("--all", "-a", action="store_true", help="Offload all temporarily loaded skills")
    offload_p.add_argument("--root", "--target", dest="root", default=".", help="Project root or target directory")

    # unload (alias for offload)
    unload_p = subparsers.add_parser("unload", help="Alias for offload")
    unload_p.add_argument("skill_id", nargs="?", default=None, help="Skill identifier to offload")
    unload_p.add_argument("--all", "-a", action="store_true", help="Offload all temporarily loaded skills")
    unload_p.add_argument("--root", "--target", dest="root", default=".", help="Project root or target directory")

    # init
    init_p = subparsers.add_parser("init", help="Initialize project directory for deterministic skill routing and harness integration")
    init_p.add_argument("target", nargs="?", default=".", help="Target project directory")
    init_p.add_argument("--profile", default=None, help="Force specific profile (core, web, android, ai, all)")

    # session-start
    session_p = subparsers.add_parser("session-start", help="Fast session pre-flight check and ephemeral cleanup")
    session_p.add_argument("--root", "--target", dest="root", default=".", help="Project root or target directory")
    session_p.add_argument("--cleanup", action="store_true", help="Clean up any ephemeral loaded skills from prior session")

    args = parser.parse_args()
    root = Path(args.root if hasattr(args, "root") else ".").resolve()

    if args.command == "sync":
        sys.exit(cmd_sync(root))
    elif args.command == "route":
        sys.exit(cmd_route(args.query, root, debug=args.debug, hydrate=args.hydrate))
    elif args.command == "benchmark":
        sys.exit(cmd_benchmark(root))
    elif args.command == "profile" or args.command == "surface":
        sys.exit(cmd_profile(args.name, root))
    elif args.command == "load":
        sys.exit(cmd_load(args.skill_id, root))
    elif args.command in ("offload", "unload"):
        sys.exit(cmd_offload(args.skill_id, root, all_loaded=args.all))
    elif args.command == "init":
        target = Path(args.target).resolve()
        sys.exit(cmd_init(target, profile=args.profile))
    elif args.command == "session-start":
        sys.exit(cmd_session_start(root, cleanup=args.cleanup))
    elif args.command == "disable":
        sys.exit(cmd_disable(args.skill_id, root, yes=args.yes))
    elif args.command == "enable":
        sys.exit(cmd_enable(args.skill_id, root))
    elif args.command == "install-harness":
        target = Path(args.target).resolve()
        sys.exit(cmd_install_harness(args.harness, target))
    elif args.command == "list":
        reg = discover_all_skills(root)
        active_prof = get_active_profile(root)
        reg = filter_skills_by_profile(reg, active_prof)
        print(f"Discovered {len(reg)} skills (Active Profile: '{active_prof}'):")
        for name, s in sorted(reg.items()):
            ov = "[Override]" if s.is_override else ""
            print(f"{name:35} {s.category:25} {s.scope:10} {ov}")
        sys.exit(0)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
