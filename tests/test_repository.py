import tempfile
import unittest
from pathlib import Path

from create_double.storage import repository


class RepositoryTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)

    def tearDown(self):
        self.tempdir.cleanup()

    def test_snapshot_outputs_copies_existing_artifacts(self):
        slug = "demo"
        repository.profile_path(self.root, slug).parent.mkdir(parents=True, exist_ok=True)
        repository.write_yaml(
            repository.profile_path(self.root, slug),
            {"meta": {"version": 3}, "identity": {}, "voice": {}, "values": {}, "decision_model": {}, "interaction_style": {}, "anchor_examples": [], "unknowns": [], "corrections": []},
        )
        repository.write_yaml(repository.session_path(self.root, slug), {"mode": "interview"})
        repository.profile_md_path(self.root, slug).write_text("# profile", encoding="utf-8")
        repository.generated_skill_path(self.root, slug).write_text("# skill", encoding="utf-8")

        snapshot_dir = repository.snapshot_outputs(self.root, slug)

        self.assertIsNotNone(snapshot_dir)
        self.assertTrue((snapshot_dir / "profile.yaml").exists())
        self.assertTrue((snapshot_dir / "profile.md").exists())
        self.assertTrue((snapshot_dir / "SKILL.md").exists())


if __name__ == "__main__":
    unittest.main()
