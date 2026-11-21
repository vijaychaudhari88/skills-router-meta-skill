#!/usr/bin/env python3
"""
Unit and integration tests for skills_router.py
Run with: python3 -m unittest tests/test_skills_router.py
"""

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from skills_router import (
    PROFILES,
    ScoredCandidate,
    SkillRecord,
    build_pipeline_declaration,
    cmd_init,
    cmd_install_harness,
    cmd_load,
    cmd_offload,
    cmd_session_start,
    cmd_sync,
    credit_ratio,
    detect_project_stack,
    discover_all_skills,
    filter_skills_by_profile,
    get_active_profile,
    inject_or_create,
    phrase_matches,
    route_query,
    set_active_profile,
    tokenize,
)


class TestTextProcessing(unittest.TestCase):
    def test_tokenize(self):
        tokens = tokenize("Build an offline form with Dexie persistence!")
        self.assertIn("build", tokens)
        self.assertIn("offline", tokens)
        self.assertIn("dexie", tokens)
        self.assertIn("persistence", tokens)
        self.assertNotIn("an", tokens)  # Stopword
        self.assertNotIn("with", tokens)  # Stopword

    def test_phrase_matches_word_boundaries(self):
        # Crucial test: Ensure short 2-char tokens don't match inside longer words
        self.assertFalse(phrase_matches("ed", "cattle breeding tables"))
        self.assertTrue(phrase_matches("ed", "run ed command on table"))
        self.assertFalse(phrase_matches("gr", "database migration script"))
        self.assertTrue(phrase_matches("gr", "execute gr review now"))

    def test_phrase_matches_multi_word(self):
        query = "audit mobile viewport touch targets and contrast"
        self.assertTrue(phrase_matches("mobile viewport", query))
        self.assertTrue(phrase_matches("touch targets", query))
        self.assertFalse(phrase_matches("desktop sidebar", query))

    def test_credit_ratio(self):
        req_tokens = {"build", "offline", "form", "dexie", "persistence"}
        # Multi-token phrase with high overlap
        ratio = credit_ratio("dexie persistence", req_tokens)
        self.assertEqual(ratio, 1.0)
        # Multi-token phrase with partial overlap (< 2 tokens matched out of > 1)
        ratio_partial = credit_ratio("dexie database cloud sync", req_tokens)
        self.assertEqual(ratio_partial, 0.0)  # Only 1 matched out of 4, below 2-token gate


class TestDeterministicRouting(unittest.TestCase):
    def setUp(self):
        self.mock_registry = {
            "dairy-agritech-domain": SkillRecord(
                name="dairy-agritech-domain",
                description="Use when calculating cow gestation window, snf formulas, or pregnancy checks.",
                source_path="./.agents/skills/dairy-agritech-domain/SKILL.md",
                scope="Project",
                category="5. Domain & Infrastructure",
                priority=100,
                objects=["cow", "buffalo", "cattle", "gestation", "pregnancy"],
                actions=["calculate", "verify", "gate"],
                domains=["agritech", "biology", "dairy"],
                use_when=["gestation window", "pregnancy check date"],
                intents={"gestation": ["calculate gestation", "gestation window", "pregnancy check date"]}
            ),
            "test-driven-development": SkillRecord(
                name="test-driven-development",
                description="Use when executing red-green-refactor TDD test cycles.",
                source_path="./skills/test-driven-development/SKILL.md",
                scope="Project",
                category="3. Debugging & Verification",
                priority=95,
                aliases=["tdd"],
                objects=["unit test", "test", "spec"],
                actions=["test", "assert", "red", "green", "refactor"],
                domains=["testing", "tdd"],
                use_when=["strict tdd unit tests", "write tests first"],
                intents={"tdd": ["run strict tdd", "tdd unit tests"]}
            ),
            "frontend-design": SkillRecord(
                name="frontend-design",
                description="Use when designing UI layouts and landing pages.",
                source_path="./skills/frontend-design/SKILL.md",
                scope="Project",
                category="2. Implementation",
                priority=95,
                objects=["landing page", "layout", "screen", "ui"],
                actions=["design", "style", "layout", "redesign"],
                domains=["ui", "frontend"],
                use_when=["redesign landing page", "redesign layout"],
                intents={"redesign": ["redesign landing page", "redesign layout"]}
            ),
            "hallmark": SkillRecord(
                name="hallmark",
                description="Use when designing website layout and landing page aesthetics.",
                source_path="~/.gemini/config/plugins/hallmark/SKILL.md",
                scope="Global",
                category="2. Implementation",
                priority=50,
                objects=["landing page", "layout", "website"],
                actions=["design", "redesign"],
                domains=["ui", "design"],
                use_when=["redesign landing page", "design website"],
                intents={"redesign": ["redesign landing page", "redesign layout"]}
            ),
            "zod-validation-expert": SkillRecord(
                name="zod-validation-expert",
                description="Use when defining Zod validation schemas for forms.",
                source_path="./.agents/skills/zod-validation-expert/SKILL.md",
                scope="Project",
                category="2. Implementation",
                priority=100,
                objects=["form", "schema", "validation", "zod"],
                actions=["validate", "refine"],
                domains=["validation", "form"],
                use_when=["zod validation", "form schema"]
            ),
            "database-design": SkillRecord(
                name="database-design",
                description="Use when designing Dexie IndexedDB schemas and persistence.",
                source_path="./.agents/skills/database-design/SKILL.md",
                scope="Project",
                category="5. Domain & Infrastructure",
                priority=100,
                objects=["dexie", "indexeddb", "persistence", "storage"],
                actions=["persist", "store", "save"],
                domains=["database", "offline"],
                use_when=["dexie persistence", "database storage"]
            ),
        }

    def test_single_winner_route(self):
        res = route_query("calculate Cow gestation window and pregnancy check date", self.mock_registry)
        self.assertEqual(res["decision"], "route")
        self.assertEqual(res["skill"], "dairy-agritech-domain")
        self.assertTrue(res["confidence"] > 0.45)

    def test_acronym_route(self):
        res = route_query("run strict tdd unit tests for reproduction cycle", self.mock_registry)
        self.assertEqual(res["decision"], "route")
        self.assertEqual(res["skill"], "test-driven-development")

    def test_ambiguous_decision_on_tie(self):
        res = route_query("redesign landing page layout aesthetics", self.mock_registry)
        self.assertEqual(res["decision"], "ambiguous")
        self.assertIn("frontend-design", res["alternatives"])
        self.assertIn("hallmark", res["alternatives"])

    def test_no_route_on_irrelevant_query(self):
        res = route_query("what is the weather in Mumbai today?", self.mock_registry)
        self.assertEqual(res["decision"], "no_route")
        self.assertIsNone(res["skill"])

    def test_multi_skill_plan_with_conjunction(self):
        res = route_query("build an offline form with Dexie persistence and Zod validation", self.mock_registry)
        self.assertEqual(res["decision"], "route")
        self.assertEqual(res["status"], "multi_skill_plan")
        self.assertIn("database-design", res["skills"])
        self.assertIn("zod-validation-expert", res["skills"])

    def test_subagent_offload_contract_in_pipeline(self):
        cand = ScoredCandidate(
            skill=SkillRecord(
                name="code-review",
                description="2-axis review",
                source_path="fake/path",
                scope="Global",
                category="4. Quality & Verification",
                priority=50
            ),
            confidence=0.85
        )
        pipeline = build_pipeline_declaration([cand])
        self.assertIn("subagent_offload", pipeline)
        self.assertTrue(len(pipeline["subagent_offload"]) >= 1)
        self.assertEqual(pipeline["subagent_offload"][0]["skill"], "code-review")

    def test_slash_command_routing(self):
        res = route_query("/tdd execute unit tests", self.mock_registry)
        self.assertEqual(res["decision"], "route")
        self.assertEqual(res["skill"], "test-driven-development")
        self.assertEqual(res["confidence"], 1.0)
        self.assertEqual(res["status"], "slash_command")

        res2 = route_query("/test-driven-development", self.mock_registry)
        self.assertEqual(res2["decision"], "route")
        self.assertEqual(res2["skill"], "test-driven-development")
        self.assertEqual(res2["confidence"], 1.0)


class TestHarnessInstallation(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="harness_test_"))

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_install_all_harnesses(self):
        exit_code = cmd_install_harness(["all"], self.test_dir)
        self.assertEqual(exit_code, 0)
        self.assertTrue((self.test_dir / "CLAUDE.md").exists())
        self.assertTrue((self.test_dir / "AGENTS.md").exists())
        self.assertTrue((self.test_dir / ".cursor" / "rules" / "skills-router.mdc").exists())
        self.assertTrue((self.test_dir / ".windsurf" / "rules" / "skills-router.md").exists())
        self.assertTrue((self.test_dir / ".roo" / "rules" / "00-skills-router.md").exists())
        self.assertTrue((self.test_dir / "CONVENTIONS.md").exists())

    def test_idempotent_injection(self):
        claude_file = self.test_dir / "CLAUDE.md"
        claude_file.write_text("# Initial Content\n\nSome custom notes.", encoding="utf-8")
        
        # First injection appends
        msg1 = inject_or_create(claude_file, "<!-- skills-manager:routing-contract:begin -->\nVersion 1\n<!-- skills-manager:routing-contract:end -->")
        self.assertIn("appended", msg1)
        self.assertIn("Version 1", claude_file.read_text(encoding="utf-8"))
        
        # Second injection replaces idempotently
        msg2 = inject_or_create(claude_file, "<!-- skills-manager:routing-contract:begin -->\nVersion 2\n<!-- skills-manager:routing-contract:end -->")
        self.assertIn("replaced", msg2)
        content = claude_file.read_text(encoding="utf-8")
        self.assertIn("Version 2", content)
        self.assertNotIn("Version 1", content)
        self.assertIn("Some custom notes.", content)


class TestManifestSyncAndShadowing(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="manifest_test_"))

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_deterministic_manifest_sync(self):
        # Create out-of-order skills
        skill_z = self.test_dir / "skills" / "zeta-skill"
        skill_z.mkdir(parents=True)
        (skill_z / "SKILL.md").write_text("---\nname: zeta-skill\ndescription: Zeta skill.\n---\nBody", encoding="utf-8")

        skill_a = self.test_dir / "skills" / "alpha-skill"
        skill_a.mkdir(parents=True)
        (skill_a / "SKILL.md").write_text("---\nname: alpha-skill\ndescription: Alpha skill.\n---\nBody", encoding="utf-8")

        skill_m = self.test_dir / "skills" / "middle-skill"
        skill_m.mkdir(parents=True)
        (skill_m / "SKILL.md").write_text("---\nname: middle-skill\ndescription: Middle skill.\n---\nBody", encoding="utf-8")

        ret = cmd_sync(self.test_dir)
        self.assertEqual(ret, 0)

        manifest_file = self.test_dir / "skill-registry" / "routing-manifest.json"
        self.assertTrue(manifest_file.exists())
        
        raw_json = manifest_file.read_text(encoding="utf-8")
        manifest_data = json.loads(raw_json)
        
        # Verify skills are sorted lexicographically in JSON key order
        skills_keys = list(manifest_data["skills"].keys())
        expected_keys = sorted(skills_keys)
        self.assertEqual(skills_keys, expected_keys)
        self.assertIn("alpha-skill", skills_keys)
        self.assertIn("middle-skill", skills_keys)
        self.assertIn("zeta-skill", skills_keys)
        
        # Verify SKILLS_REGISTRY.md dynamic header
        registry_md = (self.test_dir / "SKILLS_REGISTRY.md").read_text(encoding="utf-8")
        self.assertIn(f"# Project Skills Registry — {self.test_dir.name}", registry_md)

    def test_project_skills_shadow_global(self):
        # Setup fake global directory
        global_dir = self.test_dir / "fake_global"
        global_skill = global_dir / "common-tool"
        global_skill.mkdir(parents=True)
        (global_skill / "SKILL.md").write_text("---\nname: common-tool\ndescription: Global version\n---\nGlobal body", encoding="utf-8")

        # Setup project local .agents/skills override
        project_skill = self.test_dir / ".agents" / "skills" / "common-tool"
        project_skill.mkdir(parents=True)
        (project_skill / "SKILL.md").write_text("---\nname: common-tool\ndescription: Local project override\n---\nLocal body", encoding="utf-8")

        custom_dirs = [
            (100, "Project", self.test_dir / ".agents" / "skills"),
            (50, "Global", global_dir)
        ]

        registry = discover_all_skills(self.test_dir, custom_search_dirs=custom_dirs)
        
        self.assertIn("common-tool", registry)
        record = registry["common-tool"]
        self.assertEqual(record.scope, "Project")
        self.assertTrue(record.is_override)
        self.assertEqual(record.description, "Local project override")
        self.assertTrue(record.source_path.startswith("./.agents/skills/common-tool/SKILL.md"))


class TestProfilesAndDormancy(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="profile_test_"))

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_profile_lifecycle_and_filtering(self):
        # 1. Default profile is all
        self.assertEqual(get_active_profile(self.test_dir), "all")
        
        # 2. Switch to web profile
        self.assertTrue(set_active_profile(self.test_dir, "web"))
        self.assertEqual(get_active_profile(self.test_dir), "web")
        self.assertEqual((self.test_dir / ".skills-profile").read_text().strip(), "web")

        # 3. Test filtering logic
        mock_reg = {
            "test-driven-development": SkillRecord(name="test-driven-development", description="TDD", source_path="p1", scope="Global", category="3. Debugging & Verification", priority=50),
            "chrome-devtools": SkillRecord(name="chrome-devtools", description="CDP", source_path="p2", scope="Global", category="2. Implementation", priority=50),
            "android-cli": SkillRecord(name="android-cli", description="Android", source_path="p3", scope="Global", category="2. Implementation", priority=50),
            "local-custom": SkillRecord(name="local-custom", description="Local", source_path="p4", scope="Project", category="2. Implementation", priority=100),
        }

        filtered = filter_skills_by_profile(mock_reg, "web")
        self.assertIn("test-driven-development", filtered)  # Core debugging category
        self.assertIn("chrome-devtools", filtered)          # Specifically included in web profile
        self.assertIn("local-custom", filtered)             # Project scoped is ALWAYS preserved
        self.assertNotIn("android-cli", filtered)           # Filtered out from web profile!

        # 4. Reset profile
        self.assertTrue(set_active_profile(self.test_dir, "all"))
        self.assertEqual(get_active_profile(self.test_dir), "all")
        self.assertFalse((self.test_dir / ".skills-profile").exists())

    def test_dormant_skill_indexing_and_routing(self):
        # Setup dormant plugin directory ending in .disabled
        dormant_dir = self.test_dir / "chrome-devtools-plugin.disabled"
        cdp_skill = dormant_dir / "skills" / "chrome-devtools"
        cdp_skill.mkdir(parents=True)
        (cdp_skill / "SKILL.md").write_text("---\nname: chrome-devtools\ndescription: Uses Chrome DevTools via MCP for debugging.\n---\nFull CDP Instructions", encoding="utf-8")

        custom_dirs = [(50, "Global", self.test_dir)]
        reg = discover_all_skills(self.test_dir, custom_search_dirs=custom_dirs)
        
        # Skill must be indexed as dormant/disabled
        self.assertIn("chrome-devtools", reg)
        record = reg["chrome-devtools"]
        self.assertTrue(record.is_disabled)
        self.assertTrue(getattr(record, "is_dormant", False))

        # Direct slash command route should match and offer hydration
        res = route_query("/chrome-devtools inspect mobile viewport", reg, hydrate=True, project_root=self.test_dir)
        self.assertEqual(res["decision"], "route")
        self.assertEqual(res["skill"], "chrome-devtools")
        self.assertTrue(res.get("is_dormant", False))
        self.assertIn("hydration", res)
        self.assertIn("Full CDP Instructions", res["hydration"]["instructions"])


class TestOnDemandAndProjectInit(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="ondemand_test_"))

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_on_demand_load_and_offload_lifecycle(self):
        # Setup fake dormant global skill
        dormant_dir = self.test_dir / "fake_plugin.disabled" / "skills" / "tool-alpha"
        dormant_dir.mkdir(parents=True)
        (dormant_dir / "SKILL.md").write_text("---\nname: tool-alpha\ndescription: Tool Alpha body\n---\nAlpha doc", encoding="utf-8")

        # 1. Load on-demand into project
        custom_dirs = [
            (100, "Project", self.test_dir / ".agents" / "skills"),
            (50, "Global", self.test_dir / "fake_plugin.disabled")
        ]
        
        ret_load = cmd_load("tool-alpha", self.test_dir, custom_search_dirs=custom_dirs)
        self.assertEqual(ret_load, 0)
        
        # Verify copied to .agents/skills/tool-alpha
        loaded_skill_path = self.test_dir / ".agents" / "skills" / "tool-alpha" / "SKILL.md"
        self.assertTrue(loaded_skill_path.exists())
        self.assertIn("Alpha doc", loaded_skill_path.read_text(encoding="utf-8"))
        
        # Verify tracking file exists
        loaded_meta = self.test_dir / ".agents" / "skills" / ".loaded.json"
        self.assertTrue(loaded_meta.exists())
        meta_data = json.loads(loaded_meta.read_text(encoding="utf-8"))
        self.assertIn("tool-alpha", meta_data.get("loaded", {}))

        # 2. Discover skills: tool-alpha is now Project scope and NOT disabled
        reg = discover_all_skills(self.test_dir, custom_search_dirs=custom_dirs)
        self.assertIn("tool-alpha", reg)
        rec = reg["tool-alpha"]
        self.assertEqual(rec.scope, "Project")
        self.assertFalse(rec.is_disabled)

        # 3. Offload single skill
        ret_offload = cmd_offload("tool-alpha", self.test_dir)
        self.assertEqual(ret_offload, 0)
        self.assertFalse((self.test_dir / ".agents" / "skills" / "tool-alpha").exists())
        meta_data_after = json.loads(loaded_meta.read_text(encoding="utf-8"))
        self.assertNotIn("tool-alpha", meta_data_after.get("loaded", {}))

        # 4. Reload and test offload --all
        cmd_load("tool-alpha", self.test_dir, custom_search_dirs=custom_dirs)
        self.assertTrue((self.test_dir / ".agents" / "skills" / "tool-alpha").exists())
        ret_offload_all = cmd_offload(None, self.test_dir, all_loaded=True)
        self.assertEqual(ret_offload_all, 0)
        self.assertFalse((self.test_dir / ".agents" / "skills" / "tool-alpha").exists())
        meta_data_final = json.loads(loaded_meta.read_text(encoding="utf-8"))
        self.assertEqual(meta_data_final.get("loaded", {}), {})

    def test_project_init_autodetect_stack(self):
        new_proj = self.test_dir / "web_sample_project"
        new_proj.mkdir(parents=True)
        (new_proj / "package.json").write_text('{"name": "sample-web"}', encoding="utf-8")
        
        ret_init = cmd_init(new_proj)
        self.assertEqual(ret_init, 0)

        # Check detected profile is web
        self.assertEqual(get_active_profile(new_proj), "web")
        
        # Check harness files and registries exist
        self.assertTrue((new_proj / "CLAUDE.md").exists())
        self.assertTrue((new_proj / "AGENTS.md").exists())
        self.assertTrue((new_proj / "skill-registry" / "routing-manifest.json").exists())
        self.assertTrue((new_proj / "SKILLS_REGISTRY.md").exists())

    def test_stack_detection_heuristics(self):
        # Android detection via settings.gradle
        android_dir = self.test_dir / "android_proj"
        android_dir.mkdir(parents=True)
        (android_dir / "settings.gradle").write_text("rootProject.name = 'test'", encoding="utf-8")
        prof, desc = detect_project_stack(android_dir)
        self.assertEqual(prof, "android")
        self.assertIn("Android", desc)

        # Web detection via tsconfig.json
        web_dir = self.test_dir / "web_proj"
        web_dir.mkdir(parents=True)
        (web_dir / "tsconfig.json").write_text("{}", encoding="utf-8")
        prof, desc = detect_project_stack(web_dir)
        self.assertEqual(prof, "web")
        self.assertIn("Web", desc)

        # Python detection via setup.py
        py_dir = self.test_dir / "py_proj"
        py_dir.mkdir(parents=True)
        (py_dir / "setup.py").write_text("from setuptools import setup; setup()", encoding="utf-8")
        prof, desc = detect_project_stack(py_dir)
        self.assertEqual(prof, "core")
        self.assertIn("Python", desc)

    def test_session_start_preflight_and_cleanup(self):
        proj = self.test_dir / "session_test_proj"
        proj.mkdir(parents=True)
        cmd_init(proj, non_interactive=True)

        # Add a fake loaded skill
        fake_loaded = proj / ".agents" / "skills" / "temp-tool"
        fake_loaded.mkdir(parents=True)
        (fake_loaded / "SKILL.md").write_text("---\nname: temp-tool\ndescription: Temp\n---\nTemp body", encoding="utf-8")
        meta_file = proj / ".agents" / "skills" / ".loaded.json"
        meta_file.write_text(json.dumps({"loaded": {"temp-tool": {"source": "fake"}}}), encoding="utf-8")

        # Session start with cleanup=True should offload temp-tool
        ret = cmd_session_start(proj, cleanup=True)
        self.assertEqual(ret, 0)
        self.assertFalse(fake_loaded.exists())
        meta_after = json.loads(meta_file.read_text(encoding="utf-8"))
        self.assertEqual(meta_after.get("loaded", {}), {})

    def test_interactive_wizard_with_mocked_inputs(self):
        from unittest.mock import patch

        wizard_proj = self.test_dir / "wizard_custom_proj"
        wizard_proj.mkdir(parents=True)

        # Simulate user selecting option '2' (web or custom profile) and '2' (claude+gemini harnesses)
        with patch("builtins.input", side_effect=["2", "2"]):
            ret = cmd_init(wizard_proj, wizard=True)
            self.assertEqual(ret, 0)

        # Confirm harness files created
        self.assertTrue((wizard_proj / "CLAUDE.md").exists())
        self.assertTrue((wizard_proj / "AGENTS.md").exists())
        # Cursor should not be created since choice was 2 (claude + gemini only)
        self.assertFalse((wizard_proj / ".cursor" / "rules" / "skills-router.mdc").exists())

    def test_body_signature_fingerprinting_disambiguation(self):
        # Verify that body signatures correctly disambiguate overlapping review skills
        mock_registry = {
            "code-review": SkillRecord(
                name="code-review",
                description="Review changes along standards and spec axes.",
                source_path="fake/cr",
                scope="Global",
                category="3. Debugging & Verification",
                priority=50,
                objects=["pr", "branch", "diff", "standards", "spec"],
                actions=["review", "audit"],
                domains=["review", "standards", "spec"],
                signatures=["## spec", "## standards", "pin the fixed point"],
                intents={"review": ["review pr against standards and spec", "code review"]}
            ),
            "ponytail-review": SkillRecord(
                name="ponytail-review",
                description="Quality review of a change: is logic right, holds under load.",
                source_path="fake/pr",
                scope="Global",
                category="3. Debugging & Verification",
                priority=50,
                objects=["pr", "diff", "load", "scale", "bugs"],
                actions=["review", "check"],
                domains=["review", "performance"],
                signatures=["holds under load", "senior dev", "scale"],
                intents={"review": ["ponytail review", "review for bugs scale and load", "senior dev review"]}
            ),
            "chisle-review": SkillRecord(
                name="chisle-review",
                description="Review diff for what could be deleted or simplified.",
                source_path="fake/chr",
                scope="Global",
                category="3. Debugging & Verification",
                priority=50,
                objects=["diff", "file", "bloat", "over engineering"],
                actions=["review", "delete", "simplify"],
                domains=["review", "efficiency"],
                signatures=["what to flag", "what could be deleted or simplified", "over-built"],
                intents={"review": ["chisle review", "review for what could be deleted"]}
            ),
        }

        # 1. Query targeting standards/spec signatures routes to code-review
        r1 = route_query("review pr against standards and spec with parallel subagents", mock_registry)
        self.assertEqual(r1["decision"], "route")
        self.assertEqual(r1["skill"], "code-review")

        # 2. Query targeting holds under load / scale signatures routes to ponytail-review
        r2 = route_query("review my pr for bugs, scale, and what breaks under real load like a senior dev", mock_registry)
        self.assertEqual(r2["decision"], "route")
        self.assertEqual(r2["skill"], "ponytail-review")

        # 3. Query targeting chisle / what could be deleted routes to chisle-review
        r3 = route_query("chisle review this diff for what could be deleted or simplified", mock_registry)
        self.assertEqual(r3["decision"], "route")
        self.assertEqual(r3["skill"], "chisle-review")

    def test_record_execution_feedback_lifecycle(self):
        """Test recording execution feedback and viewing stats via CLI handlers."""
        import tempfile
        import io
        from contextlib import redirect_stdout
        from skills_router import cmd_record, cmd_stats, load_routing_history

        with tempfile.TemporaryDirectory(prefix="history_test_") as tmp_dir:
            proj_root = Path(tmp_dir)

            # 1. Initially empty history
            hist_file, data = load_routing_history(proj_root)
            self.assertEqual(data.get("skills"), {})

            # 2. Record 2 successes and 1 failure for 'test-driven-development'
            cmd_record("test-driven-development", "success", proj_root, query="run unit tests")
            cmd_record("test-driven-development", "pass", proj_root, query="verify suite")
            cmd_record("test-driven-development", "failure", proj_root, query="syntax error")

            _, updated = load_routing_history(proj_root)
            tdd_stats = updated["skills"]["test-driven-development"]
            self.assertEqual(tdd_stats["success"], 2)
            self.assertEqual(tdd_stats["failure"], 1)
            self.assertEqual(tdd_stats["last_query"], "syntax error")

            # 3. Output check via cmd_stats
            buf = io.StringIO()
            with redirect_stdout(buf):
                res = cmd_stats(proj_root)
            self.assertEqual(res, 0)
            output = buf.getvalue()
            self.assertIn("Execution Feedback Statistics", output)
            self.assertIn("test-driven-development", output)
            self.assertIn("66.7%", output)

    def test_adaptive_scoring_with_history(self):
        """Test that empirical success/failure history calibrates candidate confidence in Stage B."""
        import tempfile
        from skills_router import SkillRecord, route_query, cmd_record

        with tempfile.TemporaryDirectory(prefix="adaptive_test_") as tmp_dir:
            proj_root = Path(tmp_dir)

            mock_registry = {
                "proven-tool": SkillRecord(
                    name="proven-tool",
                    description="A dependable utility for executing data workflows.",
                    source_path="fake/p",
                    scope="Project",
                    category="2. Planning & Architecture",
                    priority=50,
                    objects=["data", "workflow"],
                    actions=["execute", "run"],
                    domains=["workflow"],
                    intents={"run": ["run data workflow", "execute data pipeline"]}
                ),
                "shaky-tool": SkillRecord(
                    name="shaky-tool",
                    description="An unstable utility for executing data workflows.",
                    source_path="fake/s",
                    scope="Project",
                    category="2. Planning & Architecture",
                    priority=50,
                    objects=["data", "workflow"],
                    actions=["execute", "run"],
                    domains=["workflow"],
                    intents={"run": ["run data workflow", "execute data pipeline"]}
                ),
            }

            # Baseline query with no history
            r_base_proven = route_query("run data workflow", mock_registry, project_root=proj_root)
            self.assertEqual(r_base_proven["decision"], "ambiguous")

            # Record 4 successes for proven-tool (smoothed rate = (4+1)/(4+2) = 5/6 = 83.3% >= 75%)
            for _ in range(4):
                cmd_record("proven-tool", "success", proj_root, query="run workflow")

            # Record 3 failures for shaky-tool (smoothed rate = (0+1)/(3+2) = 1/5 = 20.0% <= 35%)
            for _ in range(3):
                cmd_record("shaky-tool", "failure", proj_root, query="run workflow")

            # Route query with calibrated history
            r_calibrated = route_query("run data workflow", mock_registry, project_root=proj_root)
            self.assertEqual(r_calibrated["decision"], "route")
            self.assertEqual(r_calibrated["skill"], "proven-tool")
            self.assertIn("proven_track_record (4/4 ok)", r_calibrated["evidence"])


if __name__ == "__main__":
    unittest.main()
