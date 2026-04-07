import tempfile
import unittest
from pathlib import Path

from create_double.domain.profile_model import blank_profile, blank_session
from create_double.rendering import renderers
from create_double.storage import repository


class RendererTests(unittest.TestCase):
    def test_render_profile_markdown_includes_next_question(self):
        profile = blank_profile("demo", "演示分身", unknowns=[{"slot": "values.priorities", "question": "你最先保护什么？", "why": ""}])
        session = blank_session(profile)

        text = renderers.render_profile_markdown(profile, session)

        self.assertIn("## Next Question", text)
        self.assertIn("你最先保护什么？", text)

    def test_render_outputs_writes_profile_and_skill_files(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            slug = "demo"
            profile = blank_profile(slug, "演示分身", unknowns=[])
            session = blank_session(profile)
            repository.profile_path(root, slug).parent.mkdir(parents=True, exist_ok=True)
            repository.write_yaml(repository.profile_path(root, slug), profile)
            repository.write_yaml(repository.session_path(root, slug), session)

            result = renderers.render_outputs(root, slug)

            self.assertTrue(Path(result["profile_md"]).exists())
            self.assertTrue(Path(result["skill"]).exists())


if __name__ == "__main__":
    unittest.main()
