import tempfile
import unittest
from pathlib import Path

from create_double.interview import flow


class FlowTests(unittest.TestCase):
    def test_choose_guided_questions_keeps_anchor_example_for_custom_deep(self):
        questions, pending = flow.choose_guided_questions(
            "work",
            "deep",
            custom_goal="帮我处理工作里的协作分歧",
        )

        follow_ups = questions[3:]
        self.assertEqual(len(follow_ups), 4)
        self.assertTrue(any(question["id"] == "custom_success_signal" for question in follow_ups))
        self.assertTrue(any(question["kind"] == "anchor_example" for question in follow_ups))
        self.assertEqual(pending, [])

    def test_apply_turn_persists_use_case_and_session_state(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            flow.initialize_double(root, "work-double", "工作分身", "zh-CN")

            result = flow.apply_turn(
                root,
                "work-double",
                {
                    "route": "answer",
                    "mode_after": "interview",
                    "updates": {
                        "values.priorities": [{"text": "长期可维护性", "source": "direct"}],
                    },
                    "meta_updates": {"primary_use_case": "work"},
                    "session_updates": {
                        "interview_track": "work",
                        "interview_depth": "quick",
                        "pending_questions": ["work_disagreement_style"],
                        "asked_questions": ["work_priorities"],
                    },
                },
            )

            self.assertEqual(result["primary_use_case"], "work")
            state = flow.show_state(root, "work-double")
            self.assertEqual(state["primary_use_case"], "work")
            self.assertEqual(state["interview_depth"], "quick")
            self.assertEqual(state["remaining_questions"], ["work_disagreement_style"])


if __name__ == "__main__":
    unittest.main()
