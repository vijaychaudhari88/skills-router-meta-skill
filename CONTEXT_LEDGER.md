# Context Ledger — Skills Router Meta-Skill

*Preserving Coding Invariants Across Compaction Cycles (Unified Token Economy Contract)*

---

### 1. Created / Modified File Paths
- [`scripts/skills_router.py`](file:///data/user/0/ai.antigem/files/home/projects/skills-router-meta-skill/scripts/skills_router.py): Core routing, composition, cycle protection, subagent synthesis, atomic history writing, resilient XML parsing, and pre-computed normalized name variants.
- [`tests/test_skills_router.py`](file:///data/user/0/ai.antigem/files/home/projects/skills-router-meta-skill/tests/test_skills_router.py): Comprehensive test suite (37 unit tests, including OCR slash/alias tests).
- [`.agents/skills/open-code-review-delegate/SKILL.md`](file:///data/user/0/ai.antigem/files/home/projects/skills-router-meta-skill/.agents/skills/open-code-review-delegate/SKILL.md): Alibaba Open Code Review delegation mode skill specification (`/ocr-review`, `/ocr`).
- [`.scratch/skill-composition-delegation/map.md`](file:///data/user/0/ai.antigem/files/home/projects/skills-router-meta-skill/.scratch/skill-composition-delegation/map.md): Completed composition map (Tickets 01–04).

---

### 2. Active Module Signatures & Contracts

```python
# scripts/skills_router.py

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
    signatures: list[str] = field(default_factory=list)
    involves: list[str] = field(default_factory=list)
    delegates_to: list[str] = field(default_factory=list)
    intents: dict[str, list[str]] = field(default_factory=dict)
    normalized_name: str = ""
    normalized_spaced_name: str = ""

def save_routing_history(history_file: Path, data: dict) -> None:
    """Atomic write via .tmp and replace for .routing-history.json."""

def resolve_skill_dependencies(
    skill_name: str,
    registry: dict[str, SkillRecord],
    visited: set[str] | None = None,
    depth: int = 0,
    max_depth: int = 3
) -> tuple[list[SkillRecord], list[str]]:
    """Traverse involved dependencies with cycle detection (visited set) and max depth <= 3."""

def build_pipeline_declaration(
    selected_candidates: list[ScoredCandidate],
    query: str = "",
    registry: dict[str, SkillRecord] | None = None
) -> dict:
    """Stage expanded candidate + involved skills into Phase 1-4 with subagent offload."""

def build_subagent_dispatch(
    selected_candidates: list[ScoredCandidate],
    query: str = "",
    registry: dict[str, SkillRecord] | None = None
) -> dict | None:
    """Generate structured subagent dispatch payload for heavy skills & delegated skills."""
```

---

### 3. Active Errors & Stack Traces
- **None.** All 37 unit tests PASS cleanly in ~2.58s.
- Benchmark: 4/4 queries PASS in ~55ms (~13.76ms/query, SLA < 35ms).

---

### 4. Architectural Decisions & Constraints
1. **Pure Standard Library Invariant:** No external pip dependencies.
2. **Dual-Mode Composition Extraction:** Supports declarative YAML (`involves:`, `delegates_to:`) and prose regex scanning (`call the Skill tool with "..."`).
3. **Cycle Guard:** Cycle prevention via `visited: set[str]` and recursion depth cap ($\le 3$) emitting warnings in `decl["composition_warnings"]`.
4. **Decision Triad:** `route` (matched skill/plan), `ambiguous` (clarify alternatives), `no_route` (generalist engineering).
5. **Alibaba Open Code Review Integration & Remediation:** Fully integrated delegation mode (`open-code-review-delegate`), fixed all code review findings (atomic feedback writes, XML error shielding, pre-computed string variants), 37 tests passing.

---

### 5. Pending Task Checklist
- [x] Ticket 01: Metadata Schema & Parser Extension (involves, delegates_to)
- [x] Ticket 02: Recursive Pipeline & Cycle Protection Engine
- [x] Ticket 03: Subagent Delegation Mapping & Contract Synthesis
- [x] Ticket 04: Test Suite & End-to-End Verification (37 tests)
- [x] Alibaba Open Code Review full repository audit executed (100% coverage)
- [x] All OCR remediation items implemented & verified
- [x] Commit & push to `origin/main` (`68e0044`)
- [ ] Ready for user's next directive.

---

### 6. Operational Rules
- Local repository precedence over global plugins.
- Pre-flight routing query before non-trivial steps.
- Scoped caveman / ultra-terse prose reporting.
