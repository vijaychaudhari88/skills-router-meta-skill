# Context Ledger: Skills Router Meta-Skill & Token Optimization

**Timestamp:** 2026-11-21T11:10:00+05:30  
**Workspace Root:** `/data/user/0/ai.antigem/files/home/projects/skills-router-meta-skill`  
**Current Branch:** `main` (pushed to origin/main at `1113c61`)  
**Status:** All 31 Unit Tests PASS (3.2s) | Benchmark 4/4 PASS (~93ms / ~23.5ms/query) | Harnesses Configured  

---

## 1. Created & Modified File Paths

- [`scripts/skills_router.py`](file:///data/user/0/ai.antigem/files/home/projects/skills-router-meta-skill/scripts/skills_router.py): Enhanced with Subagent Dispatch Contract Standardization (`HEAVY_SUBAGENT_SKILLS` typed metadata, `build_subagent_dispatch`, injected `subagent_dispatch` payload in `route_query`, and CLI `--subagent` inspection flag).
- [`tests/test_skills_router.py`](file:///data/user/0/ai.antigem/files/home/projects/skills-router-meta-skill/tests/test_skills_router.py): 31 unit tests (+76 lines added for `test_subagent_dispatch_payload_for_heavy_skills`, `test_subagent_dispatch_not_required_for_standard_skills`, and `test_route_cli_subagent_flag`).
- [`README.md`](file:///data/user/0/ai.antigem/files/home/projects/skills-router-meta-skill/README.md): Updated CLI reference documentation covering `route "<query>" [--subagent]`.
- [`.scratch/subagent-dispatch-contract/`](file:///data/user/0/ai.antigem/files/home/projects/skills-router-meta-skill/.scratch/subagent-dispatch-contract/): Wayfinder map and resolved tickets 01–03.

---

## 2. Active Module Signatures

```python
# Core Dataclasses & Models
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
    intents: dict[str, list[str]] = field(default_factory=dict)

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
    def to_dict(self) -> dict: ...

# Discovery & Hydration Engine
def extract_metadata(skill_file: Path) -> dict
def discover_all_skills(project_root: Path, custom_search_dirs: list[tuple[int, str, Path]] | None = None) -> dict[str, SkillRecord]
def resolve_skill_path(skill: SkillRecord, project_root: Path) -> Path
def extract_hydration_payload(skill: SkillRecord, project_root: Path | None = None) -> dict
def build_subagent_dispatch(selected_candidates: list[ScoredCandidate], query: str = "") -> dict | None
def build_pipeline_declaration(selected_candidates: list[ScoredCandidate], query: str = "") -> dict
def route_query(query: str, registry: dict[str, SkillRecord], debug: bool = False, hydrate: bool = False, project_root: Path | None = None) -> dict

# Profile Staging & Auto-Tuning Engine
def parse_compound_profile(profile_str: str) -> tuple[set[str] | None, set[str] | None, str]
def is_valid_profile_spec(profile_str: str) -> bool
def get_active_profile(project_root: Path) -> str
def set_active_profile(project_root: Path, profile_name: str) -> bool
def filter_skills_by_profile(registry: dict[str, SkillRecord], profile_name: str) -> dict[str, SkillRecord]
def cmd_tune(project_root: Path, apply: bool = False) -> int

# On-Demand Lifecycle & Project Setup
def load_loaded_meta(project_root: Path) -> tuple[Path, dict]
def save_loaded_meta(meta_file: Path, data: dict) -> None
def load_routing_history(project_root: Path | str) -> tuple[Path, dict]
def save_routing_history(history_file: Path, data: dict) -> None
def cmd_record(skill_id: str, outcome: str, project_root: Path | str, query: str | None = None) -> int
def cmd_stats(project_root: Path) -> int
def detect_project_stack(target_dir: Path) -> tuple[str, str]
def run_interactive_wizard(target_dir: Path, detected_profile: str, stack_desc: str) -> tuple[str, list[str]]
def cmd_load(skill_id: str, project_root: Path, custom_search_dirs: list[tuple[int, str, Path]] | None = None) -> int
def cmd_offload(skill_id: str | None, project_root: Path, all_loaded: bool = False) -> int
def cmd_init(target_dir: Path, profile: str | None = None, wizard: bool = False, non_interactive: bool = False) -> int
def cmd_session_start(target_dir: Path, cleanup: bool = False) -> int
def cmd_route(query: str, project_root: Path, debug: bool = False, hydrate: bool = False, subagent_only: bool = False) -> int
```

---

## 3. Active Errors & Stack Traces

- **Zero Active Errors:** 23/23 tests pass cleanly in 2.5s.
- **Zero Drift:** Pushed cleanly to GitHub `origin/main` (`745bc9d`).

---

## 4. Architectural Decisions & Constraints

1. **3-Tier Composite Pyramid:**
   - **Tier 1 (Base Prompt):** Pinned static prefix contract (`<100` tokens) + deterministic lexicographical manifest sorting.
   - **Tier 2 (Workspace Boundaries):** Local project scoping (`.agents/skills/`) strictly overrides global plugins; cluster profiles gate inactive categories while preserving project skills.
   - **Tier 3 (Runtime Execution):** Progressive disclosure with on-demand hydration for dormant skills (`hydration` payload) + ephemeral subagent dispatch contracts for heavy verification skills (`subagent_offload`).
2. **Body-Aware Signature Fingerprinting (Overcoming the Progressive Disclosure Trap):**
   - Stripping tool bodies drops routing accuracy by 37–44% in empirical benchmarks.
   - We extract markdown headings, bold key terms, and code spans from the first 80 lines into `signatures` ($\le 25$ tokens), scored with a dedicated 0.14 weight in Stage B ranking.
   - Overlapping skills (e.g. `code-review`, `ponytail-review`, `chisle-review`) resolve accurately without loading full 500-line skill bodies upfront.
3. **Global Plugins Dormancy Invariant:**
   - Global plugin directories (`~/.gemini/config/plugins/` and `~/.config/opencode/skills/`) transitioned to `.disabled`, dropping live prompt skills from **102 down to 41** (saving >60,000 prompt tokens/session).
   - Only `mattpocock-skills`, `skills-manager`, and `rtk` remain active on disk.
   - All 135 dormant skills remain indexed by `skills-router` and can be loaded/hydrated on demand.

---

## 5. Pending Task Checklist

- [x] Run comprehensive discovery audit of all host skills.
- [x] Enforce deterministic lexicographical sorting for routing manifests and prompt cache keys.
- [x] Implement cluster profile staging (`profile` and `surface`).
- [x] Implement subagent offloading contracts in pipeline declarations.
- [x] Add direct slash command recognition (`/<cmd>`).
- [x] Enable discovery and indexing of dormant skills in `.disabled` directories.
- [x] Implement on-demand hydration payload generation (`--hydrate`).
- [x] Implement on-demand skill load & offload lifecycle (`load`, `offload`, `unload`).
- [x] Implement project auto-detection & initialization (`init`, `setup`).
- [x] Implement fast new chat session initialization (`session-start`).
- [x] Implement Body-Aware Signature Fingerprinting (Action 1) to solve the Progressive Disclosure Trap.
- [x] Verify disambiguation of overlapping skills (`code-review`, `ponytail-review`, `chisle-review`).
- [x] Implement Execution Feedback Memory (`.routing-history.json`) (Action 2).
- [x] Implement Multi-Tool Cluster Profiles Auto-Tuning (Action 3).
- [x] Standardize the Subagent Dispatch Contract (Action 4).

---

## 6. Operational Rules

1. Locate before reading: Never read whole files > 100 lines; use `rg -n` and bounded `sed -n 'X,Yp'`.
2. Work efficiently: Batch shell commands with `&&` and `;`.
3. Anti-slop zero-stub discipline: Never commit `// TODO`, `// FIXME`, or truncated implementations.
4. Test-driven verification: Run `python3 -m unittest discover tests` after any router edit.
