import importlib.util
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
KB_MODULE_PATH = REPO_ROOT / "scripts" / "knowledge_base.py"
KB_SPEC = importlib.util.spec_from_file_location("knowledge_base", KB_MODULE_PATH)
knowledge_base = importlib.util.module_from_spec(KB_SPEC)
assert KB_SPEC.loader is not None
KB_SPEC.loader.exec_module(knowledge_base)

DOUBLE_MODULE_PATH = REPO_ROOT / "scripts" / "double_builder.py"
DOUBLE_SPEC = importlib.util.spec_from_file_location("double_builder", DOUBLE_MODULE_PATH)
double_builder = importlib.util.module_from_spec(DOUBLE_SPEC)
assert DOUBLE_SPEC.loader is not None
DOUBLE_SPEC.loader.exec_module(double_builder)


class KnowledgeBaseTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)

    def tearDown(self):
        self.tempdir.cleanup()

    def test_init_project_kb_creates_scaffold(self):
        result = knowledge_base.init_kb(self.root, "project")

        self.assertTrue(Path(result["root"]).exists())
        self.assertTrue(Path(result["raw"]).exists())
        self.assertTrue(Path(result["wiki"]).exists())
        self.assertTrue(Path(result["index"]).exists())
        self.assertTrue(Path(result["log"]).exists())
        self.assertTrue(Path(result["schema"]).exists())

    def test_ingest_project_source_updates_raw_log_and_wiki(self):
        source = self.root / "audit-note.md"
        source.write_text("# Audit\n\nrepo is healthy\n", encoding="utf-8")

        knowledge_base.init_kb(self.root, "project")
        result = knowledge_base.ingest_source(
            self.root,
            "project",
            source_file=source,
            kind="audit",
        )

        self.assertTrue(Path(result["record"]).exists())
        index_text = (self.root / ".project-kb" / "index.md").read_text(encoding="utf-8")
        log_text = (self.root / ".project-kb" / "log.md").read_text(encoding="utf-8")
        decision_log = (self.root / ".project-kb" / "wiki" / "decision-log.md").read_text(encoding="utf-8")

        self.assertIn("audit", index_text)
        self.assertIn("ingest audit from audit-note.md", log_text)
        self.assertIn("audit-note", decision_log)

    def test_project_lint_catches_broken_links(self):
        knowledge_base.init_kb(self.root, "project")
        broken_page = self.root / ".project-kb" / "wiki" / "public-surface.md"
        broken_page.write_text("# Public Surface\n\n[Missing](missing.md)\n", encoding="utf-8")

        lint = knowledge_base.lint_kb(self.root, "project")

        self.assertFalse(lint["ok"])
        self.assertTrue(any("broken link" in error for error in lint["errors"]))

    def test_start_creates_double_kb_event_and_wiki(self):
        answers = iter(
            [
                "maintainability, clear scope, no surprise spread",
                "I ask for the goal and the thing that must not fail",
                "I explain the risk, then state the smallest scope I can accept",
                "",
                "",
            ]
        )

        double_builder.start_double(
            self.root,
            "work-double",
            "工作分身",
            start_mode="guided",
            use_case="work",
            depth="quick",
            ask=lambda _prompt: next(answers),
            writer=lambda _text: None,
        )

        kb_root = self.root / "doubles" / "work-double" / "kb"
        event_dir = kb_root / "raw" / "events"
        self.assertTrue(event_dir.exists())
        self.assertGreaterEqual(len(list(event_dir.glob("*.md"))), 1)
        self.assertTrue((kb_root / "wiki" / "overview.md").exists())
        self.assertTrue((kb_root / "wiki" / "decision-patterns.md").exists())

    def test_correct_creates_correction_event_and_updates_voice_page(self):
        answers = iter(
            [
                "maintainability, clear scope, no surprise spread",
                "I ask for the goal and the thing that must not fail",
                "I explain the risk, then state the smallest scope I can accept",
                "",
                "",
            ]
        )

        double_builder.start_double(
            self.root,
            "work-double",
            "工作分身",
            start_mode="guided",
            use_case="work",
            depth="quick",
            ask=lambda _prompt: next(answers),
            writer=lambda _text: None,
        )
        double_builder.correct_double(
            self.root,
            "work-double",
            text='我不会直接说"你应该"，我更常说"如果是我，我会先把风险讲清楚再决定"',
            writer=lambda _text: None,
        )

        kb_root = self.root / "doubles" / "work-double" / "kb"
        correction_records = [path for path in (kb_root / "raw" / "events").glob("*.md") if "correction" in path.name]
        voice_page = (kb_root / "wiki" / "voice-and-phrasing.md").read_text(encoding="utf-8")

        self.assertTrue(correction_records)
        self.assertIn("我不会直接说", voice_page)


if __name__ == "__main__":
    unittest.main()
