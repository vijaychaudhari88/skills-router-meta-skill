#!/usr/bin/env python3
"""
Unit and integration tests for skills_router.py
Run with: python3 -m unittest tests/test_skills_router.py
"""

import sys
import unittest
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from skills_router import (
    SkillRecord,
    ScoredCandidate,
    credit_ratio,
    phrase_matches,
    route_query,
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
        self.assertIn("Phase 1 (Guardrails)", res["pipeline"])

    def test_acronym_route(self):
        res = route_query("run strict TDD unit tests for reproduction models", self.mock_registry)
        self.assertEqual(res["decision"], "route")
        self.assertEqual(res["skill"], "test-driven-development")

    def test_ambiguous_decision_on_tie(self):
        res = route_query("redesign this landing page layout", self.mock_registry)
        self.assertEqual(res["decision"], "ambiguous")
        self.assertIn("frontend-design", res["alternatives"])
        self.assertIn("hallmark", res["alternatives"])

    def test_no_route_on_irrelevant_query(self):
        res = route_query("what is the weather in Mumbai today", self.mock_registry)
        self.assertEqual(res["decision"], "no_route")
        self.assertEqual(res["skills"], [])

    def test_multi_skill_plan_with_conjunction(self):
        res = route_query("build an offline form with Dexie persistence and Zod validation", self.mock_registry)
        self.assertEqual(res["decision"], "route")
        self.assertEqual(res["status"], "multi_skill_plan")
        self.assertIn("database-design", res["skills"])
        self.assertIn("zod-validation-expert", res["skills"])


class TestHarnessInstallation(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.test_dir = Path(tempfile.mkdtemp(prefix="harness_test_"))

    def tearDown(self):
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_install_all_harnesses(self):
        from skills_router import cmd_install_harness
        exit_code = cmd_install_harness(["all"], self.test_dir)
        self.assertEqual(exit_code, 0)
        self.assertTrue((self.test_dir / "CLAUDE.md").exists())
        self.assertTrue((self.test_dir / "AGENTS.md").exists())
        self.assertTrue((self.test_dir / ".cursor" / "rules" / "skills-router.mdc").exists())
        self.assertTrue((self.test_dir / ".windsurf" / "rules" / "skills-router.md").exists())
        self.assertTrue((self.test_dir / ".roo" / "rules" / "00-skills-router.md").exists())
        self.assertTrue((self.test_dir / "CONVENTIONS.md").exists())

    def test_idempotent_injection(self):
        from skills_router import inject_or_create
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


if __name__ == "__main__":
    unittest.main()
