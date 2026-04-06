import importlib.util
import subprocess
import sys
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

    def _reader(self, slug: str) -> tuple[dict, dict]:
        profile = double_builder.load_yaml(double_builder.profile_path(self.root, slug))
        session = double_builder.load_yaml(double_builder.session_path(self.root, slug))
        return profile, session

    def _run_cli(self, *args: str, input_text: str = "") -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(MODULE_PATH), *args],
            cwd=str(MODULE_PATH.parents[1]),
            input=input_text.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def _decode(self, data: bytes) -> str:
        return data.decode("utf-8", errors="replace")

    def test_route_recognizes_control_and_correction(self):
        routed = double_builder.classify_turn("继续提问", current_mode="freeform")
        self.assertEqual(routed["route"], "switch_mode")
        self.assertEqual(routed["mode_after"], "interview")

        correction = double_builder.classify_turn("我不会这么说，我更在意边界。", current_mode="interview")
        self.assertEqual(correction["route"], "correction")
        self.assertEqual(correction["mode_after"], "correction")

    def test_show_and_render_keep_older_doubles_compatible(self):
        profile, session = self._reader("my-double")
        profile["meta"].pop("primary_use_case", None)
        session.pop("interview_track", None)
        session.pop("interview_depth", None)
        session.pop("pending_questions", None)
        session.pop("asked_questions", None)
        double_builder.write_yaml(double_builder.profile_path(self.root, "my-double"), profile)
        double_builder.write_yaml(double_builder.session_path(self.root, "my-double"), session)

        render_result = double_builder.render_outputs(self.root, "my-double")
        state = double_builder.show_state(self.root, "my-double")

        self.assertTrue(Path(render_result["profile_md"]).exists())
        self.assertEqual(state["primary_use_case"], "general")
        self.assertEqual(state["interview_depth"], "quick")
        self.assertEqual(state["remaining_questions"], [])

    def test_start_work_quick_creates_artifact_and_pending_followups(self):
        answers = iter(
            [
                "可维护性、长期可持续、错误预期不要扩散",
                "我会先问目标、成功标准和最不能出错的地方",
                "我会先把风险讲清楚，再给出我能接受的最小范围",
                "",
                "",
            ]
        )

        result = double_builder.start_double(
            self.root,
            "work-double",
            "工作分身",
            start_mode="guided",
            use_case="work",
            depth="quick",
            ask=lambda _prompt: next(answers),
            writer=lambda _text: None,
        )

        profile, session = self._reader("work-double")
        state = double_builder.show_state(self.root, "work-double")

        self.assertEqual(result["primary_use_case"], "work")
        self.assertEqual(profile["meta"]["primary_use_case"], "work")
        self.assertEqual(session["interview_depth"], "quick")
        self.assertEqual(
            state["remaining_questions"],
            ["work_disagreement_style", "work_tradeoff_biases"],
        )
        self.assertTrue(Path(result["render"]["profile_md"]).exists())
        self.assertTrue(Path(result["render"]["skill"]).exists())
        priorities = [item["text"] for item in profile["values"]["priorities"]]
        self.assertIn("可维护性", priorities)
        self.assertIn("长期可持续", priorities)

    def test_start_self_dialogue_standard_asks_followups(self):
        answers = iter(
            [
                "清醒、诚实、不要继续自我欺骗",
                "我会先问这件事一周后还会不会让我难受",
                "我会区分恢复精力和逃避责任",
                "提醒我看清现实最有帮助",
                "当我只是想先舒服一点时，最容易说服自己做会后悔的决定",
                "",
            ]
        )

        result = double_builder.start_double(
            self.root,
            "dialogue-double",
            "自我对话分身",
            start_mode="guided",
            use_case="self-dialogue",
            depth="standard",
            ask=lambda _prompt: next(answers),
            writer=lambda _text: None,
        )

        profile, session = self._reader("dialogue-double")

        self.assertEqual(result["primary_use_case"], "self-dialogue")
        self.assertEqual(session["interview_depth"], "standard")
        self.assertEqual(
            session["pending_questions"],
            ["dialogue_taboo_phrases", "dialogue_anchor_example"],
        )
        self.assertEqual(len(session["asked_questions"]), 5)
        support_style = [item["text"] for item in profile["interaction_style"]["support_style"]]
        failure_patterns = [item["text"] for item in profile["decision_model"]["failure_patterns"]]
        self.assertIn("提醒我看清现实最有帮助", support_style)
        self.assertIn("当我只是想先舒服一点时，最容易说服自己做会后悔的决定", failure_patterns)

    def test_start_external_deep_collects_anchor_example(self):
        answers = iter(
            [
                "准确、清晰、别让别人误会我的边界",
                "我会先确认这是不是我该公开说的话，以及会被谁看到",
                "我会先把不方便公开的范围讲清楚",
                "克制、直接、留有余地",
                "我更像先给边界，再给结论",
                "过度承诺、替别人做决定、把情绪当事实",
                "朋友想让我公开评价一件争议事；我只讲了我能确认的部分；我不想制造超出事实的解读",
                "",
            ]
        )

        result = double_builder.start_double(
            self.root,
            "external-double",
            "对外表达分身",
            start_mode="guided",
            use_case="external",
            depth="deep",
            ask=lambda _prompt: next(answers),
            writer=lambda _text: None,
        )

        profile, session = self._reader("external-double")

        self.assertEqual(result["interview_depth"], "deep")
        self.assertEqual(profile["meta"]["primary_use_case"], "external")
        self.assertEqual(session["pending_questions"], [])
        self.assertGreaterEqual(len(profile["anchor_examples"]), 1)
        example = profile["anchor_examples"][0]
        self.assertEqual(example["situation"], "朋友想让我公开评价一件争议事")
        self.assertEqual(example["choice"], "我只讲了我能确认的部分")
        self.assertEqual(example["reason"], "我不想制造超出事实的解读")

    def test_custom_deep_keeps_anchor_example_in_selected_questions(self):
        questions, pending = double_builder.choose_guided_questions(
            "work",
            "deep",
            custom_goal="帮我处理工作里的协作分歧",
        )

        follow_up_questions = questions[3:]
        self.assertEqual(len(follow_up_questions), 4)
        self.assertTrue(any(question["id"] == "custom_success_signal" for question in follow_up_questions))
        self.assertTrue(any(question["kind"] == "anchor_example" for question in follow_up_questions))
        self.assertEqual(pending, [])

    def test_freeform_start_uses_track_specific_pending_questions(self):
        answers = iter(
            [
                "在工作里我更在意长期可维护性。接到模糊任务时我会先问目标和成功标准。遇到不舒服的节奏时，我会先把风险讲清楚，再给出我能接受的最小范围。",
                "",
                "",
            ]
        )

        result = double_builder.start_double(
            self.root,
            "work-freeform",
            "工作自由描述分身",
            start_mode="freeform",
            use_case="work",
            depth="quick",
            ask=lambda _prompt: next(answers),
            writer=lambda _text: None,
        )

        state = double_builder.show_state(self.root, "work-freeform")

        self.assertEqual(result["primary_use_case"], "work")
        self.assertEqual(state["remaining_questions"], ["work_disagreement_style", "work_tradeoff_biases"])
        self.assertTrue(all(question_id.startswith("work_") for question_id in state["remaining_questions"]))

    def test_correct_prunes_matching_pending_question(self):
        double_builder.apply_turn(
            self.root,
            "my-double",
            {
                "route": "answer",
                "mode_after": "interview",
                "meta_updates": {"primary_use_case": "self-dialogue"},
                "session_updates": {
                    "interview_track": "self-dialogue",
                    "interview_depth": "standard",
                    "pending_questions": ["dialogue_taboo_phrases", "dialogue_anchor_example"],
                    "asked_questions": ["dialogue_support_style", "dialogue_failure_patterns"],
                },
                "unknowns": [
                    {
                        "slot": "voice.taboo_phrases",
                        "question": "什么样的话对你来说看似安慰，实际上会让你更反感或更逃避？",
                        "why": "这决定分身应该避免哪些无效安慰。",
                    },
                    {
                        "slot": "anchor_examples",
                        "question": "给我一个你最近从混乱中把自己拉回来的例子：发生了什么；你怎么做；为什么？",
                        "why": "真实例子会让自我对话分身更有抓手。",
                    },
                ],
            },
        )
        double_builder.render_outputs(self.root, "my-double")

        double_builder.correct_double(
            self.root,
            "my-double",
            text="我不会这么说“都会好的”，这种安慰会让我更想逃避。",
            writer=lambda _text: None,
        )

        _profile, session = self._reader("my-double")
        self.assertEqual(session["pending_questions"], ["dialogue_anchor_example"])
        self.assertIn("dialogue_taboo_phrases", session["asked_questions"])

    def test_cli_start_with_explicit_use_case_skips_mode_prompt(self):
        process = self._run_cli(
            "start",
            "--root",
            str(self.root),
            "--slug",
            "cli-work-double",
            "--display-name",
            "工作分身",
            "--use-case",
            "work",
            input_text="\n".join(
                [
                    "maintainability, clear scope, no surprise spread",
                    "I ask for the goal and the thing that must not fail",
                    "I explain the risk, then state the smallest scope I can accept",
                    "",
                    "",
                ]
            )
            + "\n",
        )

        stdout = self._decode(process.stdout)
        stderr = self._decode(process.stderr)

        self.assertEqual(process.returncode, 0, msg=stderr)
        self.assertNotIn(double_builder.START_CHOICE_PROMPT, stdout)
        self.assertIn("1/3", stdout)
        self.assertIn("已生成：", stdout)

    def test_cli_start_without_explicit_use_case_keeps_mode_prompt(self):
        process = self._run_cli(
            "start",
            "--root",
            str(self.root),
            "--slug",
            "cli-guided-double",
            "--display-name",
            "工作分身",
            input_text="\n".join(
                [
                    "work",
                    "quick",
                    "",
                    "maintainability, clear scope, no surprise spread",
                    "I ask for the goal and the thing that must not fail",
                    "I explain the risk, then state the smallest scope I can accept",
                    "",
                    "",
                ]
            )
            + "\n",
        )

        stdout = self._decode(process.stdout)
        stderr = self._decode(process.stderr)

        self.assertEqual(process.returncode, 0, msg=stderr)
        self.assertIn(double_builder.START_CHOICE_PROMPT, stdout)
        self.assertIn("先选你要哪一种分身", stdout)

    def test_doctor_reports_repo_health(self):
        report = double_builder.doctor_report(MODULE_PATH.parents[1])
        checks = {item["name"]: item for item in report["checks"]}

        self.assertIn("Python", checks)
        self.assertIn("PyYAML", checks)
        self.assertIn("Repo validation", checks)
        self.assertTrue(checks["Python"]["ok"])
        self.assertTrue(checks["PyYAML"]["ok"])
        self.assertTrue(checks["Repo validation"]["ok"])


if __name__ == "__main__":
    unittest.main()
