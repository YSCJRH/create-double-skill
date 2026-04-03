import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "double_builder.py"
SPEC = importlib.util.spec_from_file_location("double_builder", MODULE_PATH)
double_builder = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(double_builder)


class DoubleBuilderTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        double_builder.initialize_double(self.root, "my-double", "我的分身", "zh-CN")

    def tearDown(self):
        self.tempdir.cleanup()

    def test_route_recognizes_control_and_correction(self):
        routed = double_builder.classify_turn("继续提问", current_mode="freeform")
        self.assertEqual(routed["route"], "switch_mode")
        self.assertEqual(routed["mode_after"], "interview")

        correction = double_builder.classify_turn("我不会这样说，我更在意边界。", current_mode="interview")
        self.assertEqual(correction["route"], "correction")
        self.assertEqual(correction["mode_after"], "correction")

    def test_apply_turn_merges_profile_and_unknowns(self):
        payload = {
            "route": "freeform",
            "mode_after": "freeform",
            "updates": {
                "identity.self_summary": {
                    "text": "一个做决定前会先看长期影响的人",
                    "source": "direct",
                },
                "values.priorities": [
                    {"text": "长期可持续", "source": "direct"},
                    {"text": "关系稳定", "source": "inferred"},
                ],
                "decision_model.default_questions": [
                    {"text": "这件事三个月后还重要吗？", "source": "direct"}
                ],
                "voice.tone": [{"text": "冷静但不冷淡", "source": "direct"}],
            },
            "anchor_examples": [
                {
                    "situation": "团队想快速上线一个判断还不稳定的功能",
                    "choice": "先缩小范围",
                    "reason": "不要让错误预期扩大",
                    "source": "direct",
                }
            ],
            "unknowns": [
                {
                    "slot": "interaction_style.boundary_style",
                    "question": "你不舒服时会怎么设边界？",
                    "why": "这会影响冲突场景下的表达方式。",
                }
            ],
            "next_question": "你不舒服时会怎么设边界？",
        }

        result = double_builder.apply_turn(self.root, "my-double", payload)
        self.assertEqual(result["mode_after"], "freeform")
        self.assertGreater(result["completeness"], 0)

        profile = double_builder.load_yaml(double_builder.profile_path(self.root, "my-double"))
        self.assertEqual(profile["identity"]["self_summary"]["source"], "direct")
        self.assertEqual(profile["unknowns"][0]["slot"], "interaction_style.boundary_style")
        self.assertEqual(len(profile["anchor_examples"]), 1)

    def test_render_creates_outputs_and_history_on_second_render(self):
        first_payload = {
            "route": "answer",
            "mode_after": "interview",
            "updates": {
                "values.priorities": [{"text": "长期可持续", "source": "direct"}],
                "voice.response_pattern": [{"text": "先问背景，再给判断", "source": "direct"}],
            },
        }
        second_payload = {
            "route": "correction",
            "mode_after": "correction",
            "updates": {
                "voice.taboo_phrases": [{"text": "你应该", "source": "correction"}]
            },
            "corrections": [
                {
                    "text": "我不会直接说'你应该'。",
                    "applies_to": "voice.taboo_phrases",
                }
            ],
        }

        double_builder.apply_turn(self.root, "my-double", first_payload)
        first_render = double_builder.render_outputs(self.root, "my-double")
        self.assertTrue(Path(first_render["profile_md"]).exists())
        self.assertTrue(Path(first_render["skill"]).exists())
        self.assertIsNone(first_render["snapshot"])

        double_builder.apply_turn(self.root, "my-double", second_payload)
        second_render = double_builder.render_outputs(self.root, "my-double")
        self.assertIsNotNone(second_render["snapshot"])

        history_path = Path(second_render["snapshot"])
        self.assertTrue((history_path / "profile.yaml").exists())
        self.assertTrue((history_path / "SKILL.md").exists())


if __name__ == "__main__":
    unittest.main()
