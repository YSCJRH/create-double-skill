#!/usr/bin/env python3
"""Local builder for create-double skill artifacts."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from create_double.interview.flow import (
    INTERVIEW_DEPTHS,
    START_BANNER,
    START_CHOICE_PROMPT,
    START_CORRECTION_PROMPT,
    USE_CASES,
    VALID_MODES,
    VALID_ROUTES,
    apply_turn,
    build_artifact_preview,
    build_correction_payload,
    build_freeform_start_payload,
    build_session_update,
    build_start_payload,
    choose_guided_questions,
    classify_turn,
    correct_double as flow_correct_double,
    default_start_slug,
    default_unknowns,
    demo_payload,
    initialize_double,
    next_question_from_state,
    normalize_interview_depth,
    normalize_question_ids,
    normalize_slug,
    normalize_use_case,
    pending_questions_for_depth,
    prompt_for_depth,
    prompt_for_use_case,
    question_to_unknown,
    questions_from_ids,
    show_state,
    start_double as flow_start_double,
)
from create_double.rendering.renderers import render_outputs
from create_double.storage.repository import (
    ensure_exists,
    load_yaml,
    profile_path,
    session_path,
    snapshot_outputs,
    write_yaml,
)
from create_double.system.health import (
    doctor_report,
    ensure_utf8_output,
    format_doctor_report,
)


@lru_cache(maxsize=1)
def load_knowledge_base_module() -> Any | None:
    module_path = REPO_ROOT / "scripts" / "knowledge_base.py"
    if not module_path.exists():
        return None

    spec = importlib.util.spec_from_file_location("knowledge_base", module_path)
    if spec is None or spec.loader is None:
        return None

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sync_double_kb_event(
    root: Path,
    slug: str,
    event_kind: str,
    *,
    summary: str,
    details: dict[str, Any] | None = None,
    candidate_paths: list[str] | None = None,
    promoted_paths: list[str] | None = None,
) -> dict[str, Any] | None:
    module = load_knowledge_base_module()
    if module is None:
        return None

    try:
        return module.record_double_event(
            root,
            slug,
            event_kind,
            summary=summary,
            details=details or {},
            candidate_paths=candidate_paths or [],
            promoted_paths=promoted_paths or [],
        )
    except Exception:
        return None


def start_double(
    root: Path,
    slug: str,
    display_name: str,
    language: str = "zh-CN",
    *,
    start_mode: str | None = None,
    use_case: str | None = None,
    depth: str | None = None,
    demo: bool = False,
    ask: Any = input,
    writer: Any = print,
) -> dict[str, Any]:
    return flow_start_double(
        root,
        slug,
        display_name,
        language,
        start_mode=start_mode,
        use_case=use_case,
        depth=depth,
        demo=demo,
        ask=ask,
        writer=writer,
        kb_sync=sync_double_kb_event,
    )


def correct_double(
    root: Path,
    slug: str,
    *,
    text: str | None = None,
    ask: Any = input,
    writer: Any = print,
) -> dict[str, Any]:
    return flow_correct_double(
        root,
        slug,
        text=text,
        ask=ask,
        writer=writer,
        kb_sync=sync_double_kb_event,
    )


def load_payload(args: argparse.Namespace) -> dict[str, Any]:
    if args.payload_file:
        with Path(args.payload_file).open("r", encoding="utf-8") as handle:
            return json.load(handle)
    if args.payload_json:
        return json.loads(args.payload_json)
    raise ValueError("provide either --payload-file or --payload-json")


def root_from_arg(raw_root: str | None) -> Path:
    if raw_root:
        return Path(raw_root).resolve()
    return REPO_ROOT


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Local builder for create-double. Use `start` for the first run, and keep the lower-level commands for advanced workflows.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    start_cmd = subparsers.add_parser("start", help="interactive first-run flow with no JSON payloads")
    start_cmd.add_argument("--slug")
    start_cmd.add_argument("--display-name")
    start_cmd.add_argument("--language", default="zh-CN")
    start_cmd.add_argument("--mode", choices=["guided", "freeform"])
    start_cmd.add_argument("--use-case", choices=list(USE_CASES))
    start_cmd.add_argument("--depth", choices=list(INTERVIEW_DEPTHS))
    start_cmd.add_argument("--demo", action="store_true", help="generate a demo double instead of asking personal questions")
    start_cmd.add_argument("--root")

    correct_cmd = subparsers.add_parser("correct", help="apply one natural-language correction and rerender")
    correct_cmd.add_argument("--slug", required=True)
    correct_cmd.add_argument("--text")
    correct_cmd.add_argument("--root")

    doctor_cmd = subparsers.add_parser("doctor", help="check dependencies, repo health, write access, and terminal encoding")
    doctor_cmd.add_argument("--root")

    init_cmd = subparsers.add_parser("init", help="initialize a new double")
    init_cmd.add_argument("--slug", required=True)
    init_cmd.add_argument("--display-name", required=True)
    init_cmd.add_argument("--language", default="zh-CN")
    init_cmd.add_argument("--root")

    route_cmd = subparsers.add_parser("route", help="heuristically classify a user turn")
    route_cmd.add_argument("--text", required=True)
    route_cmd.add_argument("--current-mode", default="interview", choices=sorted(VALID_MODES))

    apply_cmd = subparsers.add_parser("apply-turn", help="merge a structured payload into a double")
    apply_cmd.add_argument("--slug", required=True)
    apply_cmd.add_argument("--payload-file")
    apply_cmd.add_argument("--payload-json")
    apply_cmd.add_argument("--root")

    render_cmd = subparsers.add_parser("render", help="render profile.md and generated SKILL.md")
    render_cmd.add_argument("--slug", required=True)
    render_cmd.add_argument("--root")

    next_cmd = subparsers.add_parser("next-question", help="print the next recommended interview question")
    next_cmd.add_argument("--slug", required=True)
    next_cmd.add_argument("--root")

    show_cmd = subparsers.add_parser("show", help="show a compact state summary")
    show_cmd.add_argument("--slug", required=True)
    show_cmd.add_argument("--root")

    snapshot_cmd = subparsers.add_parser("snapshot", help="create a history snapshot if outputs already exist")
    snapshot_cmd.add_argument("--slug", required=True)
    snapshot_cmd.add_argument("--root")
    return parser


def emit(data: Any) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def main() -> None:
    ensure_utf8_output()
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "route":
        emit(classify_turn(args.text, current_mode=args.current_mode))
        return
    root = root_from_arg(getattr(args, "root", None))

    if args.command == "doctor":
        print(format_doctor_report(doctor_report(root)))
        return

    if args.command == "start":
        display_name = args.display_name or ("演示分身" if args.demo else "我的分身")
        slug = args.slug or default_start_slug(display_name, demo=args.demo)
        start_double(
            root,
            slug,
            display_name,
            args.language,
            start_mode=args.mode,
            use_case=args.use_case,
            depth=args.depth,
            demo=args.demo,
        )
        return

    if args.command == "correct":
        correct_double(root, args.slug, text=args.text)
        return

    if args.command == "init":
        emit(initialize_double(root, args.slug, args.display_name, args.language))
        return

    if args.command == "apply-turn":
        emit(apply_turn(root, normalize_slug(args.slug), load_payload(args)))
        return

    if args.command == "render":
        emit(render_outputs(root, normalize_slug(args.slug)))
        return

    if args.command == "next-question":
        slug = normalize_slug(args.slug)
        ensure_exists(root, slug)
        profile = load_yaml(profile_path(root, slug))
        session = load_yaml(session_path(root, slug))
        print(next_question_from_state(profile, session))
        return

    if args.command == "show":
        emit(show_state(root, normalize_slug(args.slug)))
        return

    if args.command == "snapshot":
        slug = normalize_slug(args.slug)
        ensure_exists(root, slug)
        snapshot_dir = snapshot_outputs(root, slug)
        emit({"snapshot": str(snapshot_dir) if snapshot_dir else None})
        return

    parser.error("unknown command")


if __name__ == "__main__":
    main()
