"""Interview routing, payload building, and interactive flows for create-double."""

from __future__ import annotations

import json
import re
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable

from create_double.domain.profile_model import (
    SINGLE_CLAIM_FIELDS,
    SOURCE_PRIORITY,
    USE_CASE_LABELS,
    blank_profile,
    blank_session,
    compute_completeness,
    ensure_profile_defaults,
    ensure_session_defaults,
    merge_anchor_examples,
    next_question_from_profile,
    normalize_anchor_example,
    normalize_correction,
    normalize_unknown,
    now_iso,
    set_update,
)
from create_double.rendering.renderers import render_outputs
from create_double.storage.repository import (
    ensure_exists,
    generated_skill_path,
    load_yaml,
    profile_md_path,
    profile_path,
    require_yaml,
    session_path,
    write_yaml,
)
from create_double.system.health import stdout_is_utf8


VALID_ROUTES = {"answer", "freeform", "correction", "switch_mode", "finish"}
VALID_MODES = {"interview", "freeform", "correction"}
DEMO_SLUG = "demo-double"
USE_CASES = ("general", "work", "self-dialogue", "external", "custom")
INTERVIEW_DEPTHS = ("quick", "standard", "deep")
START_BANNER = "3 分钟内生成你的第一个 double，不需要写 JSON。"
START_CHOICE_PROMPT = '按回车按引导问题开始；输入 "我自己说" 改成一段自述；输入 "demo" 先看演示：'
START_CORRECTION_PROMPT = '如果有一句不对，直接输入“我不会这么说...”或“我更在意...”，回车跳过：'
FREEFORM_HINT = "请用 3-6 句描述你自己，重点写你怎么判断、怎么给建议、怎么设边界。"
USE_CASE_PROMPT = (
    "先选你要哪一种分身：\n"
    "1. general 通用分身（推荐）\n"
    "2. work 工作协作版\n"
    "3. self-dialogue 自我对话版\n"
    "4. external 对外表达版\n"
    "5. custom 自定义用途\n"
    "> "
)
DEPTH_PROMPT = (
    "这次想问到多深？\n"
    "1. quick 快速起步（推荐）\n"
    "2. standard 多问 2 个细化问题\n"
    "3. deep 更深入地问 4 个问题并补一个真实例子\n"
    "> "
)
CONTINUE_DETAIL_PROMPT = '要不要继续细化 2 个问题？输入 "y" 继续，回车跳过： '
CUSTOM_GOAL_PROMPT = "这次你最想让这个分身帮你做什么？\n> "


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def question_tracks_path() -> Path:
    return repo_root() / "assets" / "question-tracks.yaml"


@lru_cache(maxsize=1)
def load_question_tracks() -> dict[str, Any]:
    tracks_file = question_tracks_path()
    tracks_data = load_yaml(tracks_file)
    tracks = tracks_data.get("tracks", {})
    if not isinstance(tracks, dict) or not tracks:
        raise ValueError("assets/question-tracks.yaml must define a non-empty tracks mapping")
    return tracks


def question_index() -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for track in load_question_tracks().values():
        for section in ("base_questions", "follow_up_questions"):
            for question in track.get(section, []):
                indexed[str(question["id"])] = question
    return indexed


def normalize_question(question: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(question["id"]).strip(),
        "slot": str(question["slot"]).strip(),
        "prompt": str(question["prompt"]).strip(),
        "why": str(question.get("why", "")).strip(),
        "kind": str(question.get("kind", "claim")).strip(),
        "track": str(question.get("track", "")).strip(),
        "depth": str(question.get("depth", "quick")).strip(),
    }


def questions_from_ids(ids: list[str]) -> list[dict[str, Any]]:
    index = question_index()
    return [normalize_question(index[question_id]) for question_id in ids if question_id in index]


def normalize_use_case(value: str | None) -> str:
    normalized = (value or "").strip().lower()
    aliases = {
        "": "general",
        "1": "general",
        "general": "general",
        "通用": "general",
        "通用分身": "general",
        "2": "work",
        "work": "work",
        "工作": "work",
        "工作版": "work",
        "工作分身": "work",
        "工作协作": "work",
        "工作协作版": "work",
        "3": "self-dialogue",
        "self-dialogue": "self-dialogue",
        "self dialogue": "self-dialogue",
        "自我对话": "self-dialogue",
        "自我对话版": "self-dialogue",
        "4": "external",
        "external": "external",
        "对外": "external",
        "对外表达": "external",
        "对外表达版": "external",
        "5": "custom",
        "custom": "custom",
        "自定义": "custom",
        "自定义用途": "custom",
    }
    if normalized not in aliases:
        raise ValueError(f"unsupported use case '{value}'")
    return aliases[normalized]


def normalize_interview_depth(value: str | None) -> str:
    normalized = (value or "").strip().lower()
    aliases = {
        "": "quick",
        "1": "quick",
        "quick": "quick",
        "快速": "quick",
        "快速起步": "quick",
        "2": "standard",
        "standard": "standard",
        "标准": "standard",
        "标准版": "standard",
        "3": "deep",
        "deep": "deep",
        "深入": "deep",
        "深度": "deep",
    }
    if normalized not in aliases:
        raise ValueError(f"unsupported interview depth '{value}'")
    return aliases[normalized]


def prompt_for_use_case(ask: Callable[[str], str]) -> str:
    return normalize_use_case(str(ask(USE_CASE_PROMPT)).strip() or "general")


def prompt_for_depth(ask: Callable[[str], str]) -> str:
    return normalize_interview_depth(str(ask(DEPTH_PROMPT)).strip() or "quick")


def track_definition(use_case: str) -> dict[str, Any]:
    tracks = load_question_tracks()
    if use_case not in tracks:
        raise ValueError(f"missing question track '{use_case}'")
    return tracks[use_case]


def question_to_unknown(question: dict[str, Any]) -> dict[str, str]:
    return {
        "slot": str(question["slot"]).strip(),
        "question": str(question["prompt"]).strip(),
        "why": str(question.get("why", "")).strip(),
    }


def track_default_unknowns(use_case: str) -> list[dict[str, str]]:
    track = track_definition(use_case)
    questions = track.get("base_questions", [])[:3] + track.get("follow_up_questions", [])[:3]
    return [question_to_unknown(question) for question in questions]


def default_unknowns() -> list[dict[str, str]]:
    return track_default_unknowns("general")


def infer_use_case_from_custom_goal(text: str) -> str:
    content = text.strip().lower()
    if any(keyword in content for keyword in ("工作", "协作", "同事", "项目", "review", "代码", "沟通", "会议")):
        return "work"
    if any(keyword in content for keyword in ("内耗", "焦虑", "卡住", "自我", "情绪", "反思", "安慰", "复盘")):
        return "self-dialogue"
    if any(keyword in content for keyword in ("别人", "公开", "发言", "社交", "对外", "表达", "介绍", "回复")):
        return "external"
    return "general"


def follow_up_limit(depth: str) -> int:
    if depth == "standard":
        return 2
    if depth == "deep":
        return 4
    return 0


def pick_follow_up_questions(use_case: str, depth: str) -> list[dict[str, Any]]:
    if depth == "quick":
        return []

    picked: list[dict[str, Any]] = []
    for question in track_definition(use_case).get("follow_up_questions", []):
        picked.append(question)
        if len(picked) >= follow_up_limit(depth):
            break

    if depth == "deep" and not any(question.get("kind") == "anchor_example" for question in picked):
        for question in track_definition(use_case).get("follow_up_questions", []):
            if question.get("kind") == "anchor_example" and question not in picked:
                picked[-1:] = [question]
                break
    return picked


def pending_questions_for_depth(use_case: str, depth: str, asked_ids: set[str]) -> list[dict[str, Any]]:
    follow_ups = track_definition(use_case).get("follow_up_questions", [])
    if depth == "quick":
        candidates = follow_ups[:2]
    elif depth == "standard":
        candidates = follow_ups[2:4]
    else:
        candidates = follow_ups[4:]
    return [question for question in candidates if question["id"] not in asked_ids]


def normalize_slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower())
    slug = re.sub(r"-{2,}", "-", slug).strip("-")
    if not slug:
        raise ValueError("slug must contain at least one ASCII letter or digit")
    return slug


def unique_nonempty(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        value = item.strip()
        key = value.lower()
        if not value or key in seen:
            continue
        seen.add(key)
        result.append(value)
    return result


def claim_values(items: list[dict[str, str]]) -> list[str]:
    return [item.get("text", "").strip() for item in items if item.get("text", "").strip()]


def add_update_text(
    updates: dict[str, Any],
    path: str,
    text: str,
    *,
    source: str = "direct",
) -> None:
    value = text.strip()
    if not value:
        return

    if path in SINGLE_CLAIM_FIELDS:
        current = updates.get(path)
        if not current or SOURCE_PRIORITY[source] >= SOURCE_PRIORITY[current.get("source", "unknown")]:
            updates[path] = {"text": value, "source": source}
        return

    existing = updates.setdefault(path, [])
    if isinstance(existing, dict):
        existing = [existing]
        updates[path] = existing
    if all(item.get("text", "").strip().lower() != value.lower() for item in existing):
        existing.append({"text": value, "source": source})


def split_short_list(text: str) -> list[str]:
    parts = [
        part.strip(" ，、；;。")
        for part in re.split(r"[、，,；;。]", text)
        if part.strip(" ，、；;。")
    ]
    short_parts = [part for part in parts if len(part) <= 18]
    if len(short_parts) >= 2 and len(short_parts) == len(parts):
        return unique_nonempty(short_parts)
    return [text.strip()]


def split_sentences(text: str) -> list[str]:
    segments = re.split(r"[。！？?!\n]+", text)
    return unique_nonempty([segment.strip(" ，；;。") for segment in segments if segment.strip(" ，；;。")])


def extract_quoted_phrases(text: str) -> list[str]:
    return unique_nonempty(re.findall(r"[\"'“”‘’](.*?)[\"'“”‘’]", text))


def first_clause(text: str) -> str:
    return re.split(r"[，；;。！？?!\n]", text, maxsplit=1)[0].strip(" “”\"'‘’")


def text_after_marker(text: str, markers: list[str]) -> str:
    for marker in markers:
        if marker in text:
            return text.split(marker, 1)[1].strip()
    return ""


def payload_filled_slots(payload: dict[str, Any]) -> set[str]:
    slots = set(payload.get("updates", {}).keys())
    if payload.get("anchor_examples"):
        slots.add("anchor_examples")
    return slots


def format_question_prompt(question: dict[str, Any], index: int, total: int) -> str:
    return f"{index}/{total} {question['prompt']}\n> "


def custom_follow_up_question(custom_goal: str) -> dict[str, Any]:
    question = normalize_question(track_definition("custom")["follow_up_questions"][0])
    question["prompt"] = question["prompt"].replace("{custom_goal}", custom_goal)
    return question


def parse_anchor_example_answer(text: str) -> dict[str, str] | None:
    value = text.strip().strip("。")
    parts = [part.strip() for part in re.split(r"[；;]", value) if part.strip()]
    if len(parts) >= 3:
        return {
            "situation": parts[0],
            "choice": parts[1],
            "reason": parts[2],
            "source": "direct",
        }

    if "因为" in value:
        before_reason, reason = value.rsplit("因为", 1)
        clauses = [part.strip() for part in re.split(r"[，,]", before_reason) if part.strip()]
        if len(clauses) >= 2 and reason.strip():
            return {
                "situation": clauses[0],
                "choice": "，".join(clauses[1:]),
                "reason": reason.strip(),
                "source": "direct",
            }
    return None


def apply_question_answer(payload: dict[str, Any], question: dict[str, Any], answer: str) -> bool:
    text = answer.strip()
    if not text:
        return False

    kind = question.get("kind", "claim")
    slot = question["slot"]
    updates = payload.setdefault("updates", {})

    if kind == "claim":
        add_update_text(updates, slot, text)
        return True

    if kind == "list":
        for item in split_short_list(text):
            add_update_text(updates, slot, item)
        return True

    if kind == "anchor_example":
        example = parse_anchor_example_answer(text)
        if example:
            payload.setdefault("anchor_examples", []).append(example)
            return True
        return False

    raise ValueError(f"unsupported question kind '{kind}'")


def asked_question_ids(entries: list[dict[str, Any]]) -> list[str]:
    return [entry["question"]["id"] for entry in entries if entry.get("applied")]


def unresolved_questions(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [entry["question"] for entry in entries if not entry.get("applied")]


def summary_from_profile_payload(updates: dict[str, Any]) -> str:
    priorities = "、".join(
        claim["text"] for claim in updates.get("values.priorities", []) if claim.get("text")
    )
    default_questions = "、".join(
        claim["text"] for claim in updates.get("decision_model.default_questions", []) if claim.get("text")
    )
    boundary_style = "、".join(
        claim["text"] for claim in updates.get("interaction_style.boundary_style", []) if claim.get("text")
    )
    support_style = "、".join(
        claim["text"] for claim in updates.get("interaction_style.support_style", []) if claim.get("text")
    )
    parts = unique_nonempty(
        [
            f"做重要决定时先保护{priorities}" if priorities else "",
            f"给建议前会先问或先看{default_questions}" if default_questions else "",
            f"不舒服时通常会{boundary_style}" if boundary_style else "",
            f"支持别人时更像{support_style}" if support_style else "",
        ]
    )
    return "；".join(parts)


def enrich_start_payload(payload: dict[str, Any], use_case: str, custom_goal: str | None = None) -> None:
    updates = payload.setdefault("updates", {})

    default_questions = "、".join(
        claim["text"] for claim in updates.get("decision_model.default_questions", []) if claim.get("text")
    )
    if default_questions and not updates.get("decision_model.advice_style"):
        add_update_text(updates, "decision_model.advice_style", f"给建议前会先问或先看：{default_questions}", source="inferred")

    if custom_goal:
        add_update_text(updates, "identity.contexts", f"这次最想让分身帮我：{custom_goal}")

    if use_case == "work":
        add_update_text(updates, "identity.contexts", "主要用于工作协作和判断", source="inferred")
    elif use_case == "self-dialogue":
        add_update_text(updates, "identity.contexts", "主要用于自我对话和整理内在判断", source="inferred")
    elif use_case == "external":
        add_update_text(updates, "identity.contexts", "主要用于面向他人的表达和边界拿捏", source="inferred")

    summary = summary_from_profile_payload(updates)
    if summary:
        add_update_text(updates, "identity.self_summary", summary, source="inferred")


def build_session_update(track: str, depth: str, pending_questions: list[dict[str, Any]], asked_ids: list[str]) -> dict[str, Any]:
    return {
        "interview_track": track,
        "interview_depth": depth,
        "pending_questions": [question["id"] for question in pending_questions],
        "asked_questions": asked_ids,
    }


def build_start_payload(
    *,
    route: str,
    mode_after: str,
    use_case: str,
    depth: str,
    answered_entries: list[dict[str, Any]],
    pending_questions: list[dict[str, Any]],
    custom_goal: str | None = None,
    existing_asked_ids: list[str] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "route": route,
        "mode_after": mode_after,
        "updates": {},
        "meta_updates": {"primary_use_case": use_case},
    }

    for entry in answered_entries:
        if entry.get("applied"):
            apply_question_answer(payload, entry["question"], entry["answer"])

    enrich_start_payload(payload, use_case, custom_goal=custom_goal)
    unresolved = unresolved_questions(answered_entries)
    full_pending = unresolved + pending_questions
    payload["unknowns"] = [question_to_unknown(question) for question in full_pending]
    payload["next_question"] = payload["unknowns"][0]["question"] if payload["unknowns"] else ""
    asked_ids = unique_nonempty((existing_asked_ids or []) + asked_question_ids(answered_entries))
    payload["session_updates"] = build_session_update(use_case, depth, full_pending, asked_ids)
    return payload


def build_freeform_start_payload(
    text: str,
    *,
    use_case: str,
    depth: str,
    pending_questions: list[dict[str, Any]],
    custom_goal: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "route": "freeform",
        "mode_after": "freeform",
        "updates": {},
        "meta_updates": {"primary_use_case": use_case},
    }
    add_update_text(payload["updates"], "identity.self_summary", text)

    for sentence in split_sentences(text):
        if any(marker in sentence for marker in ("在意", "优先", "保护", "看重")):
            add_update_text(payload["updates"], "values.priorities", sentence)
        if any(marker in sentence for marker in ("先问", "问自己", "先看什么")):
            add_update_text(payload["updates"], "decision_model.default_questions", sentence)
        elif any(marker in sentence for marker in ("先看", "取舍", "长期", "短期", "代价", "风险")):
            add_update_text(payload["updates"], "decision_model.tradeoff_biases", sentence)
        if any(marker in sentence for marker in ("建议", "安慰", "追问", "鸡汤", "帮对方")):
            add_update_text(payload["updates"], "decision_model.advice_style", sentence)
        if any(marker in sentence for marker in ("边界", "拒绝", "不舒服", "底线")):
            add_update_text(payload["updates"], "interaction_style.boundary_style", sentence)
        if any(marker in sentence for marker in ("支持", "安抚", "陪", "梳理")):
            add_update_text(payload["updates"], "interaction_style.support_style", sentence)
        if any(marker in sentence for marker in ("不同意", "反驳", "指出", "纠正")):
            add_update_text(payload["updates"], "interaction_style.disagreement_style", sentence)

    enrich_start_payload(payload, use_case, custom_goal=custom_goal)
    payload["unknowns"] = [question_to_unknown(question) for question in pending_questions]
    payload["next_question"] = payload["unknowns"][0]["question"] if payload["unknowns"] else ""
    payload["session_updates"] = build_session_update(use_case, depth, pending_questions, [])
    return payload


def ask_questions(questions: list[dict[str, Any]], ask: Callable[[str], str]) -> list[dict[str, Any]]:
    answers: list[dict[str, Any]] = []
    total = len(questions)
    for index, question in enumerate(questions, start=1):
        answer = str(ask(format_question_prompt(question, index, total))).strip()
        answers.append(
            {
                "question": question,
                "answer": answer,
                "applied": apply_question_answer({"updates": {}, "anchor_examples": []}, question, answer),
            }
        )
    return answers


def choose_guided_questions(use_case: str, depth: str, custom_goal: str | None = None) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    selected_follow_ups = pick_follow_up_questions(use_case, depth)

    if custom_goal:
        custom_question = custom_follow_up_question(custom_goal)
        if depth == "quick":
            pending_questions = [custom_question] + pending_questions_for_depth(use_case, "quick", set())
        else:
            limit = follow_up_limit(depth)
            selected_follow_ups = [custom_question] + selected_follow_ups[: max(limit - 1, 0)]
            if depth == "deep" and not any(question.get("kind") == "anchor_example" for question in selected_follow_ups):
                anchor_question = next(
                    (
                        question
                        for question in track_definition(use_case).get("follow_up_questions", [])
                        if question.get("kind") == "anchor_example"
                    ),
                    None,
                )
                if anchor_question is not None:
                    if len(selected_follow_ups) >= limit and limit > 0:
                        selected_follow_ups[-1] = anchor_question
                    else:
                        selected_follow_ups.append(anchor_question)
            pending_questions = pending_questions_for_depth(use_case, depth, {question["id"] for question in selected_follow_ups})
    else:
        pending_questions = pending_questions_for_depth(use_case, depth, {question["id"] for question in selected_follow_ups})

    base_questions = [normalize_question(question) for question in track_definition(use_case).get("base_questions", [])[:3]]
    selected_questions = base_questions + [normalize_question(question) for question in selected_follow_ups]
    pending_questions = [normalize_question(question) for question in pending_questions]
    return selected_questions, pending_questions


def demo_payload() -> dict[str, Any]:
    with (repo_root() / "examples" / "initial-freeform-payload.json").open("r", encoding="utf-8") as handle:
        return json.load(handle)


def build_correction_payload(text: str) -> dict[str, Any]:
    updates: dict[str, Any] = {}
    quotes = extract_quoted_phrases(text)
    applies_to = "identity.self_summary"

    taboo_fragment = first_clause(text_after_marker(text, ["我不会直接说", "我不会这么说", "我不会这样说"]))
    if taboo_fragment:
        applies_to = "voice.taboo_phrases"
        add_update_text(updates, applies_to, taboo_fragment, source="correction")
    elif quotes and any(marker in text for marker in ("我不会直接说", "我不会这么说", "我不会这样说")):
        applies_to = "voice.taboo_phrases"
        add_update_text(updates, applies_to, quotes[0], source="correction")

    preferred_phrase = ""
    if "更常说" in text and quotes:
        preferred_phrase = quotes[-1]
    else:
        preferred_phrase = first_clause(text_after_marker(text, ["我更常说", "我会更常说", "我通常会说"]))
    if preferred_phrase:
        applies_to = "voice.signature_phrases"
        add_update_text(updates, applies_to, preferred_phrase, source="correction")

    priority_fragment = first_clause(text_after_marker(text, ["我更在意", "我更看重"]))
    if priority_fragment:
        applies_to = "values.priorities"
        add_update_text(updates, applies_to, priority_fragment, source="correction")

    question_fragment = first_clause(text_after_marker(text, ["这种情况下我会先问", "我通常会先问", "我会先问"]))
    if question_fragment:
        applies_to = "decision_model.default_questions"
        add_update_text(updates, applies_to, question_fragment, source="correction")

    if any(marker in text for marker in ("边界", "不舒服", "底线")):
        applies_to = "interaction_style.boundary_style"
        boundary_fragment = first_clause(text_after_marker(text, ["我会", "通常会"])) or text.strip()
        if boundary_fragment and not boundary_fragment.startswith("我"):
            boundary_fragment = f"我会{boundary_fragment}"
        add_update_text(updates, applies_to, boundary_fragment, source="correction")

    return {
        "route": "correction",
        "mode_after": "correction",
        "updates": updates,
        "corrections": [{"text": text.strip(), "applies_to": applies_to}],
    }


def build_artifact_preview(profile: dict[str, Any], session: dict[str, Any]) -> str:
    self_summary = profile["identity"]["self_summary"]
    summary_text = self_summary.get("text", "").strip()
    summary_label = "暂定自我概括" if self_summary.get("source") == "inferred" else "自我概括"
    lines = [
        "当前 preview：",
        f"- 主用途：{USE_CASE_LABELS.get(str(profile['meta'].get('primary_use_case', 'general')), '通用分身')}",
        f"- {summary_label}：{summary_text or '还没有。'}",
        f"- 优先保护：{'、'.join(claim_values(profile['values']['priorities'])[:3]) or '待补'}",
        f"- 给建议前先问：{'、'.join(claim_values(profile['decision_model']['default_questions'])[:2]) or '待补'}",
        f"- 设边界方式：{'、'.join(claim_values(profile['interaction_style']['boundary_style'])[:2]) or '待补'}",
        f"- 剩余细化问题：{len(normalize_question_ids(session.get('pending_questions', [])))}",
        f"- 下一步：{next_question_from_state(profile, session) or '可以继续补充案例或修正。'}",
    ]
    return "\n".join(lines)


def classify_turn(text: str, current_mode: str = "interview") -> dict[str, str]:
    content = text.strip()
    if not content:
        return {"route": "answer", "mode_after": current_mode, "reason": "empty input defaults to answer"}

    hard_controls = {
        "继续提问": ("switch_mode", "interview"),
        "我自己说": ("switch_mode", "freeform"),
        "我要改一句": ("switch_mode", "correction"),
        "先生成看看": ("finish", current_mode),
    }
    if content in hard_controls:
        route, mode_after = hard_controls[content]
        return {"route": route, "mode_after": mode_after, "reason": "matched control phrase"}

    correction_markers = ["我不会这么说", "我不会这样说", "我更在意", "这种情况下我会先问", "不是这个意思"]
    if any(marker in content for marker in correction_markers):
        return {"route": "correction", "mode_after": "correction", "reason": "matched correction language"}

    if current_mode == "correction":
        return {"route": "correction", "mode_after": "correction", "reason": "stayed in correction mode"}

    if current_mode == "freeform":
        return {"route": "freeform", "mode_after": "freeform", "reason": "stayed in freeform mode"}

    sentence_like = len(re.findall(r"[。！？?!;\n]", content))
    if len(content) > 60 or sentence_like >= 2:
        return {"route": "freeform", "mode_after": "freeform", "reason": "dense self-description"}

    return {"route": "answer", "mode_after": "interview", "reason": "treated as answer to current question"}


def initialize_double(root: Path, slug: str, display_name: str, language: str) -> dict[str, Any]:
    slug = normalize_slug(slug)
    profile_file = profile_path(root, slug)
    if profile_file.exists():
        raise FileExistsError(f"double '{slug}' already exists")

    profile = blank_profile(slug, display_name=display_name, language=language, unknowns=default_unknowns())
    profile["meta"]["completeness"] = compute_completeness(profile)
    session = blank_session(profile)
    write_yaml(profile_file, profile)
    write_yaml(session_path(root, slug), session)
    return {"slug": slug, "profile": str(profile_file), "session": str(session_path(root, slug))}


def next_question_from_state(profile: dict[str, Any], session: dict[str, Any]) -> str:
    profile = ensure_profile_defaults(profile)
    session = ensure_session_defaults(session, profile)
    if session.get("next_question"):
        return str(session["next_question"]).strip()
    return next_question_from_profile(profile)


def normalize_question_ids(values: Any) -> list[str]:
    if values is None:
        return []
    if not isinstance(values, list):
        raise ValueError("pending_questions and asked_questions must be lists")
    return [str(value).strip() for value in values if str(value).strip()]


def apply_turn(root: Path, slug: str, payload: dict[str, Any]) -> dict[str, Any]:
    ensure_exists(root, slug)
    profile = ensure_profile_defaults(load_yaml(profile_path(root, slug)))
    session = ensure_session_defaults(load_yaml(session_path(root, slug)), profile)

    route = str(payload.get("route", "")).strip()
    if route not in VALID_ROUTES:
        raise ValueError(f"payload route must be one of {sorted(VALID_ROUTES)}")

    mode_after = str(payload.get("mode_after", session.get("mode", "interview"))).strip()
    if mode_after not in VALID_MODES:
        raise ValueError(f"mode_after must be one of {sorted(VALID_MODES)}")

    for path, value in payload.get("updates", {}).items():
        set_update(profile, path, value)

    anchor_examples = [normalize_anchor_example(item) for item in payload.get("anchor_examples", [])]
    profile["anchor_examples"] = merge_anchor_examples(profile["anchor_examples"], anchor_examples)

    if "unknowns" in payload:
        profile["unknowns"] = [normalize_unknown(item) for item in payload.get("unknowns", [])]

    corrections = [normalize_correction(item) for item in payload.get("corrections", [])]
    profile["corrections"].extend(corrections)

    meta_updates = payload.get("meta_updates", {})
    if meta_updates:
        primary_use_case = normalize_use_case(meta_updates.get("primary_use_case", profile["meta"].get("primary_use_case", "general")))
        profile["meta"]["primary_use_case"] = primary_use_case

    profile["meta"]["completeness"] = compute_completeness(profile)
    session["mode"] = mode_after
    session["last_route"] = route
    session_updates = payload.get("session_updates", {})
    if session_updates:
        session["interview_track"] = normalize_use_case(session_updates.get("interview_track", session.get("interview_track", "general")))
        session["interview_depth"] = normalize_interview_depth(session_updates.get("interview_depth", session.get("interview_depth", "quick")))
        session["pending_questions"] = normalize_question_ids(session_updates.get("pending_questions", session.get("pending_questions", [])))
        session["asked_questions"] = normalize_question_ids(session_updates.get("asked_questions", session.get("asked_questions", [])))
    session["next_question"] = str(payload.get("next_question", "")).strip() or next_question_from_profile(profile)
    session["updated_at"] = now_iso()

    write_yaml(profile_path(root, slug), profile)
    write_yaml(session_path(root, slug), session)
    return {
        "slug": slug,
        "route": route,
        "mode_after": mode_after,
        "completeness": profile["meta"]["completeness"],
        "next_question": session["next_question"],
        "primary_use_case": profile["meta"]["primary_use_case"],
    }


def default_start_slug(display_name: str, *, demo: bool = False) -> str:
    if demo:
        return DEMO_SLUG
    try:
        return normalize_slug(display_name)
    except ValueError:
        stamp = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
        return f"double-{stamp}"


def prune_pending_questions(pending_ids: list[str], filled_slots: set[str]) -> tuple[list[dict[str, Any]], list[str]]:
    remaining: list[dict[str, Any]] = []
    removed_ids: list[str] = []
    for question in questions_from_ids(pending_ids):
        if question["slot"] in filled_slots:
            removed_ids.append(question["id"])
            continue
        remaining.append(question)
    return remaining, removed_ids


def correct_double(
    root: Path,
    slug: str,
    *,
    text: str | None = None,
    ask: Callable[[str], str] = input,
    writer: Callable[[str], None] | None = print,
    kb_sync: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    require_yaml("correct")
    slug = normalize_slug(slug)
    ensure_exists(root, slug)
    correction_text = (text or str(ask("输入一句 correction：\n> "))).strip()
    if not correction_text:
        raise ValueError("correction text cannot be empty")

    profile_before = ensure_profile_defaults(load_yaml(profile_path(root, slug)))
    session_before = ensure_session_defaults(load_yaml(session_path(root, slug)), profile_before)
    payload = build_correction_payload(correction_text)
    filled_slots = payload_filled_slots(payload)
    remaining_pending_questions, removed_ids = prune_pending_questions(
        normalize_question_ids(session_before.get("pending_questions", [])),
        filled_slots,
    )
    payload["unknowns"] = [question_to_unknown(question) for question in remaining_pending_questions]
    payload["next_question"] = payload["unknowns"][0]["question"] if payload["unknowns"] else ""
    payload["meta_updates"] = {"primary_use_case": profile_before["meta"].get("primary_use_case", "general")}
    payload["session_updates"] = build_session_update(
        str(session_before.get("interview_track", profile_before["meta"].get("primary_use_case", "general"))),
        str(session_before.get("interview_depth", "quick")),
        remaining_pending_questions,
        unique_nonempty(normalize_question_ids(session_before.get("asked_questions", [])) + removed_ids),
    )
    apply_turn(root, slug, payload)
    render_result = render_outputs(root, slug)
    profile = ensure_profile_defaults(load_yaml(profile_path(root, slug)))
    session = ensure_session_defaults(load_yaml(session_path(root, slug)), profile)
    preview = build_artifact_preview(profile, session)

    if writer:
        writer("")
        writer("已应用 correction。")
        writer(preview)
        writer("")

    if kb_sync is not None:
        kb_sync(
            root,
            slug,
            "correction",
            summary=correction_text,
            details={
                "next_question": next_question_from_state(profile, session),
                "pruned_pending_question_ids": removed_ids,
                "remaining_pending_question_ids": normalize_question_ids(session.get("pending_questions", [])),
            },
            candidate_paths=sorted(filled_slots),
            promoted_paths=sorted(filled_slots),
        )

    return {
        "slug": slug,
        "text": correction_text,
        "preview": preview,
        "render": render_result,
        "next_question": next_question_from_state(profile, session),
    }


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
    ask: Callable[[str], str] = input,
    writer: Callable[[str], None] | None = print,
    kb_sync: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    require_yaml("start")
    slug = normalize_slug(slug)
    initialize_double(root, slug, display_name, language)

    if writer:
        writer(START_BANNER)

    explicit_start_config = demo or start_mode is not None or use_case is not None or depth is not None
    if explicit_start_config:
        selected_use_case = normalize_use_case(use_case or "general")
        selected_depth = normalize_interview_depth(depth or "quick")
        selected_mode = "demo" if demo else (start_mode or "guided")
    else:
        selected_use_case = prompt_for_use_case(ask)
        selected_depth = prompt_for_depth(ask)
        selected_mode = None
    resolved_use_case = selected_use_case
    custom_goal: str | None = None
    kb_candidate_paths: set[str] = set()

    if not explicit_start_config and selected_mode is None:
        choice = str(ask(START_CHOICE_PROMPT)).strip()
        if choice.lower() == "demo":
            selected_mode = "demo"
        elif choice == "我自己说":
            selected_mode = "freeform"
        else:
            selected_mode = "guided"

    if selected_use_case == "custom" and selected_mode != "demo":
        custom_goal = str(ask(CUSTOM_GOAL_PROMPT)).strip()
        resolved_use_case = infer_use_case_from_custom_goal(custom_goal)
        if writer:
            writer(f"已按最接近的用途继续：{USE_CASE_LABELS[resolved_use_case]}")
            writer("")

    if selected_mode == "demo":
        payload = demo_payload()
        payload["meta_updates"] = {"primary_use_case": resolved_use_case if resolved_use_case != "custom" else "general"}
        pending_questions = pending_questions_for_depth(
            resolved_use_case if resolved_use_case != "custom" else "general",
            "quick",
            set(),
        )
        payload["unknowns"] = [question_to_unknown(question) for question in pending_questions]
        payload["next_question"] = payload["unknowns"][0]["question"] if payload["unknowns"] else ""
        payload["session_updates"] = build_session_update(
            resolved_use_case if resolved_use_case != "custom" else "general",
            "quick",
            pending_questions,
            [],
        )
        selected_depth = "quick"
        kb_candidate_paths.update(payload_filled_slots(payload))
    elif selected_mode == "freeform":
        freeform_text = str(ask(f"{FREEFORM_HINT}\n> ")).strip()
        if not freeform_text:
            raise ValueError("freeform start needs at least one non-empty self-description")
        pending_questions = pending_questions_for_depth(resolved_use_case, selected_depth, set())
        if custom_goal:
            pending_questions = [custom_follow_up_question(custom_goal)] + pending_questions
        payload = build_freeform_start_payload(
            freeform_text,
            use_case=resolved_use_case,
            depth=selected_depth,
            pending_questions=pending_questions,
            custom_goal=custom_goal,
        )
        kb_candidate_paths.update(payload_filled_slots(payload))
    else:
        selected_questions, pending_questions = choose_guided_questions(
            resolved_use_case,
            selected_depth,
            custom_goal=custom_goal,
        )
        answers = ask_questions(selected_questions, ask)
        payload = build_start_payload(
            route="answer",
            mode_after="interview",
            use_case=resolved_use_case,
            depth=selected_depth,
            answered_entries=answers,
            pending_questions=pending_questions,
            custom_goal=custom_goal,
        )
        selected_mode = "guided"
        kb_candidate_paths.update(payload_filled_slots(payload))

    apply_turn(root, slug, payload)
    render_result = render_outputs(root, slug)
    profile = ensure_profile_defaults(load_yaml(profile_path(root, slug)))
    session = ensure_session_defaults(load_yaml(session_path(root, slug)), profile)
    preview = build_artifact_preview(profile, session)
    correction_applied = False

    if writer:
        writer("")
        writer("已生成：")
        writer(f"- profile.md: {render_result['profile_md']}")
        writer(f"- SKILL.md: {render_result['skill']}")
        writer("")
        writer(preview)
        writer("")

    if not demo:
        correction_text = str(ask(START_CORRECTION_PROMPT)).strip()
        if correction_text:
            correction_result = correct_double(root, slug, text=correction_text, ask=ask, writer=writer, kb_sync=kb_sync)
            render_result = correction_result["render"]
            profile = ensure_profile_defaults(load_yaml(profile_path(root, slug)))
            session = ensure_session_defaults(load_yaml(session_path(root, slug)), profile)
            preview = correction_result["preview"]
            correction_applied = True

        if selected_depth == "quick":
            continue_answer = str(ask(CONTINUE_DETAIL_PROMPT)).strip().lower()
            if continue_answer in {"y", "yes", "继续", "好", "1"}:
                profile = ensure_profile_defaults(load_yaml(profile_path(root, slug)))
                session = ensure_session_defaults(load_yaml(session_path(root, slug)), profile)
                pending_ids = session.get("pending_questions", [])[:2]
                follow_up_questions = questions_from_ids(pending_ids)
                if follow_up_questions:
                    follow_up_answers = ask_questions(follow_up_questions, ask)
                    remaining_ids = normalize_question_ids(session.get("pending_questions", []))[len(follow_up_questions):]
                    follow_up_payload = build_start_payload(
                        route="answer",
                        mode_after="interview",
                        use_case=resolved_use_case,
                        depth="standard",
                        answered_entries=follow_up_answers,
                        pending_questions=questions_from_ids(remaining_ids),
                        custom_goal=custom_goal,
                        existing_asked_ids=normalize_question_ids(session.get("asked_questions", [])),
                    )
                    apply_turn(root, slug, follow_up_payload)
                    render_result = render_outputs(root, slug)
                    profile = ensure_profile_defaults(load_yaml(profile_path(root, slug)))
                    session = ensure_session_defaults(load_yaml(session_path(root, slug)), profile)
                    preview = build_artifact_preview(profile, session)
                    selected_depth = "standard"
                    kb_candidate_paths.update(payload_filled_slots(follow_up_payload))
                    if writer:
                        writer("")
                        writer("已继续细化。")
                        writer(preview)
                        writer("")

    if writer and not stdout_is_utf8():
        writer("提示：如果终端中文预览乱码，请先运行 `chcp 65001`，或直接打开生成的 profile.md。")
        writer("")

    if writer:
        writer(f"继续补充：python scripts/double_builder.py correct --slug {slug}")

    if not demo and kb_sync is not None:
        kb_sync(
            root,
            slug,
            "start",
            summary=preview,
            details={
                "correction_applied": correction_applied,
                "custom_goal": custom_goal,
                "interview_depth": selected_depth,
                "next_question": next_question_from_state(profile, session),
                "primary_use_case": resolved_use_case,
                "start_mode": selected_mode,
            },
            candidate_paths=sorted(kb_candidate_paths),
            promoted_paths=sorted(kb_candidate_paths),
        )

    return {
        "slug": slug,
        "display_name": display_name,
        "start_mode": selected_mode,
        "primary_use_case": resolved_use_case,
        "interview_depth": selected_depth,
        "correction_applied": correction_applied,
        "preview": preview,
        "next_question": next_question_from_state(profile, session),
        "render": render_result,
    }


def show_state(root: Path, slug: str) -> dict[str, Any]:
    ensure_exists(root, slug)
    profile = ensure_profile_defaults(load_yaml(profile_path(root, slug)))
    session = ensure_session_defaults(load_yaml(session_path(root, slug)), profile)
    return {
        "slug": slug,
        "display_name": profile["meta"]["display_name"],
        "primary_use_case": profile["meta"].get("primary_use_case", "general"),
        "version": profile["meta"]["version"],
        "completeness": profile["meta"]["completeness"],
        "mode": session.get("mode", "interview"),
        "interview_depth": session.get("interview_depth", "quick"),
        "next_question": next_question_from_state(profile, session),
        "unknown_slots": [item["slot"] for item in profile.get("unknowns", [])],
        "remaining_questions": normalize_question_ids(session.get("pending_questions", [])),
        "files": {
            "profile": str(profile_path(root, slug)),
            "profile_md": str(profile_md_path(root, slug)),
            "skill": str(generated_skill_path(root, slug)),
        },
    }
