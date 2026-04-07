import unittest

from create_double.domain import profile_model


class ProfileModelTests(unittest.TestCase):
    def test_merge_claim_lists_prefers_higher_source_priority(self):
        existing = [{"text": "长期可持续", "source": "inferred"}]
        incoming = [{"text": "长期可持续", "source": "direct"}]

        merged = profile_model.merge_claim_lists(existing, incoming)

        self.assertEqual(merged, [{"text": "长期可持续", "source": "direct"}])

    def test_blank_profile_accepts_default_unknowns(self):
        profile = profile_model.blank_profile(
            "my-double",
            "我的分身",
            unknowns=[{"slot": "values.priorities", "question": "你最先保护什么？", "why": "用于首轮判断"}],
        )

        self.assertEqual(profile["meta"]["primary_use_case"], "general")
        self.assertEqual(profile["unknowns"][0]["slot"], "values.priorities")

    def test_compute_completeness_reflects_filled_sections(self):
        profile = profile_model.blank_profile("my-double", "我的分身")
        self.assertEqual(profile_model.compute_completeness(profile), 0.0)

        profile["values"]["priorities"] = [{"text": "可维护性", "source": "direct"}]
        profile["decision_model"]["default_questions"] = [{"text": "目标是什么", "source": "direct"}]

        self.assertGreater(profile_model.compute_completeness(profile), 0.0)


if __name__ == "__main__":
    unittest.main()
