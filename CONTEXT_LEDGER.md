# Context Ledger: Skills Router Meta-Skill & Token Optimization

**Timestamp:** 2026-11-21T07:48:00+05:30  
**Workspace Root:** `/data/user/0/ai.antigem/files/home/projects/skills-router-meta-skill`  
**Current Branch:** `main` (clean working diffs on test/script files)  
**Status:** All 20 Unit Tests PASS (0.44s) | Benchmark 4/4 PASS (~47ms/query)  

---

## 1. Created & Modified File Paths

- [`scripts/skills_router.py`](file:///data/user/0/ai.antigem/files/home/projects/skills-router-meta-skill/scripts/skills_router.py): Enhanced with deterministic manifest generation, cluster profiles (`surface`/`profile`), subagent offload contracts, direct slash command routing (`/^(\/[a-zA-Z0-9_-]+)/`), dormant catalog indexing across `.disabled` directories, on-demand hydration payload generation (`--hydrate`), on-demand staging lifecycle (`load`/`offload`/`unload`), first-time project workspace setup (`init`), and new chat session pre-flight initialization (`session-start`).
- [`tests/test_skills_router.py`](file:///data/user/0/ai.antigem/files/home/projects/skills-router-meta-skill/tests/test_skills_router.py): Expanded from 11 to 20 tests (+262 lines) covering deterministic sync, local project shadowing, profile lifecycle filtering, subagent offloading contracts, direct slash command routing, dormant hydration payloads, on-demand staging/unstaging, project auto-init stack detection, and session-start preflight/cleanup.
- [`HANDOFF.md`](file:///data/user/0/ai.antigem/files/home/projects/skills-router-meta-skill/HANDOFF.md): Updated project status, architecture milestones, and command reference.
- [`.scratch/on-demand-and-project-init/map.md`](file:///data/user/0/ai.antigem/files/home/projects/skills-router-meta-skill/.scratch/on-demand-and-project-init/map.md): Wayfinder map tracking the 4 resolved tickets for on-demand loading and project/session initialization.
- [`.scratch/on-demand-and-project-init/issues/`](file:///data/user/0/ai.antigem/files/home/projects/skills-router-meta-skill/.scratch/on-demand-and-project-init/issues/): Resolved tickets `01-on-demand-load-offload-lifecycle.md`, `02-project-directory-first-time-setup.md`, `03-new-chat-session-initialization.md`, and `04-integration-benchmark-and-verification.md`.

---

## 2. Active Module Signatures

```python
# Core Dataclasses
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

# Routing, Discovery & Hydration Engine
def discover_all_skills(project_root: Path, custom_search_dirs: list[tuple[int, str, Path]] | None = None) -> dict[str, SkillRecord]
def resolve_skill_path(skill: SkillRecord, project_root: Path) -> Path
def extract_metadata(skill_file: Path) -> dict
def extract_hydration_payload(skill: SkillRecord, project_root: Path | None = None) -> dict
def route_query(query: str, registry: dict[str, SkillRecord], debug: bool = False, hydrate: bool = False, project_root: Path | None = None) -> dict
def build_pipeline_declaration(selected_candidates: list[ScoredCandidate]) -> dict

# Profile Staging Engine
def get_active_profile(project_root: Path) -> str
def set_active_profile(project_root: Path, profile_name: str) -> bool
def filter_skills_by_profile(registry: dict[str, SkillRecord], profile_name: str) -> dict[str, SkillRecord]

# On-Demand Staging & Project/Session Engine
def detect_project_stack(project_root: Path) -> tuple[str, str]
def cmd_load(skill_id: str, project_root: Path) -> int
def cmd_offload(skill_id: str | None, project_root: Path, all_loaded: bool = False) -> int
def cmd_init(project_root: Path, requested_profile: str | None = None) -> int
def cmd_session_start(project_root: Path, cleanup: bool = False) -> int

# CLI Command Handlers
def cmd_sync(project_root: Path) -> int
def cmd_disable(skill_id: str, project_root: Path, yes: bool = False) -> int
def cmd_enable(skill_id: str, project_root: Path) -> int
def cmd_route(query: str, project_root: Path, debug: bool = False, hydrate: bool = False) -> int
def cmd_benchmark(project_root: Path) -> int
def cmd_profile(profile_name: str | None, project_root: Path) -> int
def cmd_install_harness(harness_names: list[str], target_dir: Path) -> int
```

---

## 3. Active Errors & Stack Traces

- **Zero Active Runtime Errors:** 20/20 tests passing in 0.44s (`OK`).
- **Benchmark:** 4/4 passing (~47.8 ms total / ~12 ms/query).
- **Code Review Items to Address:**
  - `scripts/skills_router.py`: Support `offload --all` without requiring dummy `skill_id`; alias `--target` to `--root` on `load`/`offload`/`init`; add missing file patterns to `detect_project_stack` (`settings.gradle`, `AndroidManifest.xml`, `tsconfig.json`, `pnpm-workspace.yaml`, `setup.py`); filter active count by profile in `session-start`.
  - `tests/test_skills_router.py`: Move method-level imports to file header; organize test classes by subsystem; add assertions for `offload --all` and `session-start --cleanup`.
  - `README.md`: Document new commands (`init`, `load`, `offload`, `session-start`, `profile`, `surface`, `--hydrate`).

---

## 4. Architectural Decisions & Constraints

1. **3-Tier Composite Pyramid:**
   - **Tier 1 (Base Prompt):** Pinned static prefix contract (`<100` tokens) + deterministic lexicographical manifest sorting (`dirs.sort()`, `files.sort()`, `sort_keys=True`).
   - **Tier 2 (Workspace Boundaries):** Local project scoping (`.agents/skills/`) strictly overrides global plugins; cluster profiles (`skills-router profile <name>`) gate inactive categories while preserving project skills.
   - **Tier 3 (Runtime Execution):** Progressive disclosure with on-demand hydration for dormant skills (`hydration` payload) + ephemeral subagent dispatch contracts for heavy verification skills (`subagent_offload`).
2. **Global Plugins Dormancy Invariant:**
   - Global plugin directories (`~/.gemini/config/plugins/` and `~/.config/opencode/skills/`) transitioned to `.disabled`, dropping live prompt skills from **102 down to 41** (saving >60,000 prompt tokens/session).
   - Only `mattpocock-skills` (39 skills), `skills-manager` (meta-skill router), and `rtk` remain active on disk.
   - All 135 dormant skills remain indexed by `skills-router` and can be invoked/hydrated on demand.
3. **On-Demand Staging Sovereignty:**
   - Staging a dormant skill (`load`) places it directly into `<project_root>/.agents/skills/<skill_id>` and registers it in `.agents/skills/.loaded.json`.
   - Offloading (`offload` or `offload --all`) sweeps staged folders without touching permanent skills or global catalogs.

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
- [x] Implement project auto-detection & initialization (`init`).
- [x] Implement fast new chat session initialization (`session-start`).
- [x] Resolve all 4 Wayfinder tickets in `.scratch/on-demand-and-project-init/`.
- [x] Run parallel two-axis `/code-review` (Standards + Spec).
- [ ] Address code review findings (CLI flags, stack detection manifests, test structure, `README.md`).
- [ ] Commit working changes cleanly with conventional commit message.
- [ ] Prepare PR / release documentation.

---

## 6. Operational Rules

1. Locate before reading: Never read whole files > 100 lines; use `rg -n` and bounded `sed -n 'X,Yp'`.
2. Work efficiently: Batch shell commands with `&&` and `;`.
3. Anti-slop zero-stub discipline: Never commit `// TODO`, `// FIXME`, or truncated implementations.
4. Test-driven verification: Run `python3 -m unittest discover tests` after any router edit.
