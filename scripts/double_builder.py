#!/usr/bin/env python3
"""Local builder for create-double skill artifacts."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import shutil
import sys
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - exercised through doctor in real environments
    yaml = None

VALID_ROUTES = {"answer", "freeform", "correction", "switch_mode", "finish"}
VALID_MODES = {"interview", "freeform", "correction"}
VALID_SOURCES = {"direct", "inferred", "correction", "unknown"}
SINGLE_CLAIM_FIELDS = {"identity.self_summary"}
LIST_CLAIM_FIELDS = {
    "identity.roles",
    "identity.contexts",
    "voice.tone",
    "voice.signature_phrases",
    "voice.taboo_phrases",
    "voice.response_pattern",
    "values.priorities",
    "values.non_negotiables",
    "values.motivators",
    "decision_model.default_questions",
    "decision_model.tradeoff_biases",
    "decision_model.advice_style",
    "decision_model.failure_patterns",
    "interaction_style.support_style",
    "interaction_style.disagreement_style",
    "interaction_style.boundary_style",
}
ALLOWED_UPDATE_PATHS = SINGLE_CLAIM_FIELDS | LIST_CLAIM_FIELDS
SOURCE_PRIORITY = {"unknown": 0, "inferred": 1, "direct": 2, "correction": 3}
START_BANNER = "3 分钟内生成你的第一个 double，不需要写 JSON。"
START_CHOICE_PROMPT = '按回车按引导问题开始；输入 "我自己说" 改成一段自述；输入 "demo" 先看演示： '
START_CORRECTION_PROMPT = '如果有一句不对，直接输入“我不会这么说...”或“我更在意...”，回车跳过： '
FREEFORM_HINT = (
    "请用 3-6 句描述你自己，重点写你怎么判断、怎么给建议、怎么设边界。"
)
DEMO_SLUG = "demo-double"
USE_CASES = ("general", "work", "self-dialogue", "external", "custom")
INTERVIEW_DEPTHS = ("quick", "standard", "deep")
USE_CASE_LABELS = {
    "general": "通用分身",
    "work": "工作协作版",
    "self-dialogue": "自我对话版",
    "external": "对外表达版",
    "custom": "自定义用途",
}
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


def now_iso() -> str:
    return datetime.now().astimezone().replace(microsecond=0).isoformat()


def require_yaml(command_name: str = "this command") -> None:
    if yaml is None:
        raise RuntimeError(
            f"PyYAML 未安装，无法运行 {command_name}。先执行 `python -m pip install -r requirements.txt`。"
        )


def ensure_utf8_output() -> None:
    for stream_name in ("stdin", "stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except OSError:
                pass


def stdout_is_utf8() -> bool:
    encoding = (getattr(sys.stdout, "encoding", None) or "").lower()
    return "utf" in encoding


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


@lru_cache(maxsize=1)
def load_knowledge_base_module() -> Any | None:
    module_path = repo_root() / "scripts" / "knowledge_base.py"
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


def question_tracks_path() -> Path:
    return repo_root() / "assets" / "question-tracks.yaml"


@lru_cache(maxsize=1)
def load_question_tracks() -> dict[str, Any]:
    require_yaml("question tracks")
    path = question_tracks_path()
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    tracks = data.get("tracks", {})
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


def prompt_for_use_case(ask: Any) -> str:
    return normalize_use_case(str(ask(USE_CASE_PROMPT)).strip() or "general")


def prompt_for_depth(ask: Any) -> str:
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


def default_unknowns() -> list[dict[str, str]]:
    return track_default_unknowns("general")


def blank_profile(slug: str, display_name: str, language: str = "zh-CN") -> dict[str, Any]:
    return {
        "meta": {
            "slug": slug,
            "display_name": display_name,
            "language": language,
            "version": 1,
            "completeness": 0.0,
            "primary_use_case": "general",
        },
        "identity": {
            "self_summary": {"text": "", "source": "unknown"},
            "roles": [],
            "contexts": [],
        },
        "voice": {
            "tone": [],
            "signature_phrases": [],
            "taboo_phrases": [],
            "response_pattern": [],
        },
        "values": {
            "priorities": [],
            "non_negotiables": [],
            "motivators": [],
        },
        "decision_model": {
            "default_questions": [],
            "tradeoff_biases": [],
            "advice_style": [],
            "failure_patterns": [],
        },
        "interaction_style": {
            "support_style": [],
            "disagreement_style": [],
            "boundary_style": [],
        },
        "anchor_examples": [],
        "unknowns": default_unknowns(),
        "corrections": [],
    }


def blank_session(profile: dict[str, Any]) -> dict[str, Any]:
    next_question = next_question_from_profile(profile)
    return {
        "mode": "interview",
        "last_route": "switch_mode",
        "interview_track": str(profile["meta"].get("primary_use_case", "general")),
        "interview_depth": "quick",
        "pending_questions": [],
        "asked_questions": [],
        "next_question": next_question,
        "updated_at": now_iso(),
    }


def ensure_profile_defaults(profile: dict[str, Any]) -> dict[str, Any]:
    profile.setdefault("meta", {})
    profile["meta"].setdefault("primary_use_case", "general")
    return profile


def ensure_session_defaults(session: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
    session.setdefault("mode", "interview")
    session.setdefault("last_route", "switch_mode")
    session.setdefault("interview_track", str(profile.get("meta", {}).get("primary_use_case", "general")))
    session.setdefault("interview_depth", "quick")
    session.setdefault("pending_questions", [])
    session.setdefault("asked_questions", [])
    session.setdefault("next_question", next_question_from_profile(profile))
    session.setdefault("updated_at", now_iso())
    return session


def load_yaml(path: Path) -> dict[str, Any]:
    require_yaml(path.name)
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def write_yaml(path: Path, data: dict[str, Any]) -> None:
    require_yaml(path.name)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(
            data,
            handle,
            allow_unicode=True,
            sort_keys=False,
            width=1000,
        )


def double_dir(root: Path, slug: str) -> Path:
    return root / "doubles" / slug


def profile_path(root: Path, slug: str) -> Path:
    return double_dir(root, slug) / "profile.yaml"


def profile_md_path(root: Path, slug: str) -> Path:
    return double_dir(root, slug) / "profile.md"


def generated_skill_path(root: Path, slug: str) -> Path:
    return double_dir(root, slug) / "SKILL.md"


def session_path(root: Path, slug: str) -> Path:
    return double_dir(root, slug) / "session.yaml"


def history_dir(root: Path, slug: str) -> Path:
    return double_dir(root, slug) / "history"


def ensure_exists(root: Path, slug: str) -> None:
    if not profile_path(root, slug).exists():
        raise FileNotFoundError(f"double '{slug}' does not exist under {root / 'doubles'}")


def normalize_claim(value: Any, default_source: str = "direct") -> dict[str, str]:
    if isinstance(value, str):
        text = value.strip()
        source = default_source
    elif isinstance(value, dict):
        text = str(value.get("text", "")).strip()
        source = str(value.get("source", default_source)).strip() or default_source
    else:
        raise TypeError(f"claim must be str or dict, got {type(value)!r}")

    if not text:
        return {"text": "", "source": "unknown"}
    if source not in VALID_SOURCES:
        raise ValueError(f"invalid source '{source}'")
    return {"text": text, "source": source}


def normalize_claim_list(values: Any, default_source: str = "direct") -> list[dict[str, str]]:
    if values is None:
        return []
    if isinstance(values, (str, dict)):
        values = [values]
    claims = []
    for value in values:
        claim = normalize_claim(value, default_source=default_source)
        if claim["text"]:
            claims.append(claim)
    return claims


def merge_claim_lists(existing: list[dict[str, str]], incoming: list[dict[str, str]]) -> list[dict[str, str]]:
    merged: dict[str, dict[str, str]] = {}
    for claim in existing + incoming:
        key = claim["text"].strip().lower()
        if not key:
            continue
        current = merged.get(key)
        if current is None or SOURCE_PRIORITY[claim["source"]] >= SOURCE_PRIORITY[current["source"]]:
            merged[key] = {"text": claim["text"].strip(), "source": claim["source"]}
    return list(merged.values())


def normalize_anchor_example(example: dict[str, Any]) -> dict[str, str]:
    situation = str(example.get("situation", "")).strip()
    choice = str(example.get("choice", "")).strip()
    reason = str(example.get("reason", "")).strip()
    source = str(example.get("source", "direct")).strip() or "direct"
    if not situation or not choice or not reason:
        raise ValueError("anchor_examples entries need situation, choice, and reason")
    if source not in VALID_SOURCES:
        raise ValueError(f"invalid source '{source}'")
    return {
        "situation": situation,
        "choice": choice,
        "reason": reason,
        "source": source,
    }


def merge_anchor_examples(existing: list[dict[str, str]], incoming: list[dict[str, str]]) -> list[dict[str, str]]:
    merged: dict[tuple[str, str], dict[str, str]] = {}
    for example in existing + incoming:
        key = (example["situation"].strip().lower(), example["choice"].strip().lower())
        current = merged.get(key)
        if current is None or SOURCE_PRIORITY[example["source"]] >= SOURCE_PRIORITY[current["source"]]:
            merged[key] = example
    return list(merged.values())


def normalize_unknown(value: dict[str, Any]) -> dict[str, str]:
    slot = str(value.get("slot", "")).strip()
    question = str(value.get("question", "")).strip()
    why = str(value.get("why", "")).strip()
    if not slot or not question:
        raise ValueError("unknowns entries need slot and question")
    return {"slot": slot, "question": question, "why": why}


def normalize_correction(value: dict[str, Any]) -> dict[str, str]:
    text = str(value.get("text", "")).strip()
    applies_to = str(value.get("applies_to", "")).strip()
    recorded_at = str(value.get("recorded_at", "")).strip() or now_iso()
    if not text or not applies_to:
        raise ValueError("corrections entries need text and applies_to")
    return {
        "text": text,
        "applies_to": applies_to,
        "recorded_at": recorded_at,
    }


def compute_completeness(profile: dict[str, Any]) -> float:
    checks = [
        bool(profile["identity"]["self_summary"].get("text")),
        bool(profile["identity"]["roles"]),
        bool(profile["identity"]["contexts"]),
        bool(profile["voice"]["tone"]),
        bool(profile["voice"]["signature_phrases"]),
        bool(profile["voice"]["taboo_phrases"]),
        bool(profile["voice"]["response_pattern"]),
        bool(profile["values"]["priorities"]),
        bool(profile["values"]["non_negotiables"]),
        bool(profile["values"]["motivators"]),
        bool(profile["decision_model"]["default_questions"]),
        bool(profile["decision_model"]["tradeoff_biases"]),
        bool(profile["decision_model"]["advice_style"]),
        bool(profile["decision_model"]["failure_patterns"]),
        bool(profile["interaction_style"]["support_style"]),
        bool(profile["interaction_style"]["disagreement_style"]),
        bool(profile["interaction_style"]["boundary_style"]),
        bool(profile["anchor_examples"]),
    ]
    return round(sum(checks) / len(checks), 2)


def set_update(profile: dict[str, Any], path: str, value: Any) -> None:
    if path not in ALLOWED_UPDATE_PATHS:
        raise ValueError(f"unsupported update path '{path}'")

    section, field = path.split(".", 1)
    if path in SINGLE_CLAIM_FIELDS:
        claim = normalize_claim(value)
        if claim["text"]:
            profile[section][field] = claim
        return

    incoming = normalize_claim_list(value)
    profile[section][field] = merge_claim_lists(profile[section][field], incoming)


def next_question_from_profile(profile: dict[str, Any]) -> str:
    unknowns = profile.get("unknowns", [])
    if unknowns:
        return str(unknowns[0].get("question", "")).strip()
    return ""


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
    parts = [part.strip(" ，,、；;。") for part in re.split(r"[、，,；;]", text) if part.strip(" ，,、；;。")]
    short_parts = [part for part in parts if len(part) <= 18]
    if len(short_parts) >= 2 and len(short_parts) == len(parts):
        return unique_nonempty(short_parts)
    return [text.strip()]


def split_sentences(text: str) -> list[str]:
    segments = re.split(r"[。！？!?\n]+", text)
    return unique_nonempty([segment.strip(" ，,；;") for segment in segments if segment.strip(" ，,；;")])


def extract_quoted_phrases(text: str) -> list[str]:
    return unique_nonempty(re.findall(r"[\"'“”‘’](.*?)[\"'“”‘’]", text))


def first_clause(text: str) -> str:
    return re.split(r"[，,；;。！？!?\n]", text, maxsplit=1)[0].strip(" ：:\"'“”‘’")


def text_after_marker(text: str, markers: list[str]) -> str:
    for marker in markers:
        if marker in text:
            return text.split(marker, 1)[1].strip()
    return ""


def filter_unknowns(unknowns: list[dict[str, str]], filled_slots: set[str]) -> list[dict[str, str]]:
    filtered: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in unknowns:
        normalized = normalize_unknown(item)
        slot = normalized["slot"]
        if slot in filled_slots or slot in seen:
            continue
        seen.add(slot)
        filtered.append(normalized)
    return filtered


def payload_filled_slots(payload: dict[str, Any]) -> set[str]:
    slots = set(payload.get("updates", {}).keys())
    if payload.get("anchor_examples"):
        slots.add("anchor_examples")
    return slots


def format_question_prompt(question: dict[str, Any], index: int, total: int) -> str:
    return f"{index}/{total} {question['prompt']}\n> "


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
    priorities = "；".join(
        claim["text"] for claim in updates.get("values.priorities", []) if claim.get("text")
    )
    default_questions = "；".join(
        claim["text"] for claim in updates.get("decision_model.default_questions", []) if claim.get("text")
    )
    boundary_style = "；".join(
        claim["text"] for claim in updates.get("interaction_style.boundary_style", []) if claim.get("text")
    )
    support_style = "；".join(
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

    default_questions = "；".join(
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
    payload["session_updates"] = build_session_update(
        use_case,
        depth,
        full_pending,
        asked_ids,
    )
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
        if any(marker in sentence for marker in ("建议", "安慰", "追问", "灌鸡汤", "帮对方")):
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


def ask_questions(questions: list[dict[str, Any]], ask: Any) -> list[dict[str, Any]]:
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
    track_use_case = use_case
    selected_follow_ups = pick_follow_up_questions(track_use_case, depth)

    if custom_goal:
        custom_question = custom_follow_up_question(custom_goal)
        if depth == "quick":
            pending_questions = [custom_question] + pending_questions_for_depth(track_use_case, "quick", set())
        else:
            limit = follow_up_limit(depth)
            selected_follow_ups = [custom_question] + selected_follow_ups[: max(limit - 1, 0)]
            if depth == "deep" and not any(question.get("kind") == "anchor_example" for question in selected_follow_ups):
                anchor_question = next(
                    (
                        question
                        for question in track_definition(track_use_case).get("follow_up_questions", [])
                        if question.get("kind") == "anchor_example"
                    ),
                    None,
                )
                if anchor_question is not None:
                    if len(selected_follow_ups) >= limit and limit > 0:
                        selected_follow_ups[-1] = anchor_question
                    else:
                        selected_follow_ups.append(anchor_question)
            pending_questions = pending_questions_for_depth(track_use_case, depth, {question["id"] for question in selected_follow_ups})
    else:
        pending_questions = pending_questions_for_depth(track_use_case, depth, {question["id"] for question in selected_follow_ups})

    base_questions = [normalize_question(question) for question in track_definition(track_use_case).get("base_questions", [])[:3]]
    selected_questions = base_questions + [normalize_question(question) for question in selected_follow_ups]
    pending_questions = [normalize_question(question) for question in pending_questions]
    return selected_questions, pending_questions


def demo_payload() -> dict[str, Any]:
    repo_root = Path(__file__).resolve().parents[1]
    with (repo_root / "examples" / "initial-freeform-payload.json").open("r", encoding="utf-8") as handle:
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

    payload: dict[str, Any] = {
        "route": "correction",
        "mode_after": "correction",
        "updates": updates,
        "corrections": [{"text": text.strip(), "applies_to": applies_to}],
    }
    return payload


def build_artifact_preview(profile: dict[str, Any], session: dict[str, Any]) -> str:
    self_summary = normalize_claim(profile["identity"]["self_summary"], default_source="unknown")
    summary_label = "暂定自我概括" if self_summary["source"] == "inferred" else "自我概括"
    lines = [
        "当前 preview：",
        f"- 主用途：{USE_CASE_LABELS.get(str(profile['meta'].get('primary_use_case', 'general')), '通用分身')}",
        f"- {summary_label}：{self_summary['text'] or '还没有。'}",
        f"- 优先保护：{'；'.join(claim_values(profile['values']['priorities'])[:3]) or '待补'}",
        f"- 给建议前先问：{'；'.join(claim_values(profile['decision_model']['default_questions'])[:2]) or '待补'}",
        f"- 设边界方式：{'；'.join(claim_values(profile['interaction_style']['boundary_style'])[:2]) or '待补'}",
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
        "我要改一下": ("switch_mode", "correction"),
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

    sentence_like = len(re.findall(r"[。！？!?;\n]", content))
    if len(content) > 60 or sentence_like >= 2:
        return {"route": "freeform", "mode_after": "freeform", "reason": "dense self-description"}

    return {"route": "answer", "mode_after": "interview", "reason": "treated as answer to current question"}


def load_payload(args: argparse.Namespace) -> dict[str, Any]:
    if args.payload_file:
        with Path(args.payload_file).open("r", encoding="utf-8") as handle:
            return json.load(handle)
    if args.payload_json:
        return json.loads(args.payload_json)
    raise ValueError("provide either --payload-file or --payload-json")


def initialize_double(root: Path, slug: str, display_name: str, language: str) -> dict[str, Any]:
    slug = normalize_slug(slug)
    profile_file = profile_path(root, slug)
    if profile_file.exists():
        raise FileExistsError(f"double '{slug}' already exists")

    profile = blank_profile(slug, display_name=display_name, language=language)
    profile["meta"]["completeness"] = compute_completeness(profile)
    session = blank_session(profile)
    write_yaml(profile_file, profile)
    write_yaml(session_path(root, slug), session)
    return {"slug": slug, "profile": str(profile_file), "session": str(session_path(root, slug))}


def next_question_from_state(profile: dict[str, Any], session: dict[str, Any]) -> str:
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
        pending_questions = pending_questions_for_depth(resolved_use_case if resolved_use_case != "custom" else "general", "quick", set())
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
            correction_result = correct_double(root, slug, text=correction_text, ask=ask, writer=writer)
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

    if not demo:
        sync_double_kb_event(
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
    ask: Any = input,
    writer: Any = print,
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

    sync_double_kb_event(
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


def repo_validation_errors(root: Path) -> list[str]:
    validator_path = root / "scripts" / "validate_repo.py"
    if not validator_path.exists():
        return ["缺少 scripts/validate_repo.py。"]
    if yaml is None:
        return ["PyYAML 未安装，暂时无法运行完整仓库校验。"]

    spec = importlib.util.spec_from_file_location("validate_repo", validator_path)
    if spec is None or spec.loader is None:
        return ["无法加载 scripts/validate_repo.py。"]

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return list(module.validate(root))


def write_access_ok(root: Path) -> tuple[bool, str]:
    doubles_root = root / "doubles"
    doubles_root.mkdir(parents=True, exist_ok=True)
    probe = doubles_root / ".doctor-write-check"
    try:
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
    except OSError as exc:
        return False, str(exc)
    return True, str(doubles_root)


def doctor_report(root: Path) -> dict[str, Any]:
    python_ok = sys.version_info >= (3, 9)
    write_ok, write_detail = write_access_ok(root)
    validation_errors = repo_validation_errors(root)
    terminal_ok = stdout_is_utf8()

    checks = [
        {
            "name": "Python",
            "ok": python_ok,
            "detail": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        },
        {
            "name": "PyYAML",
            "ok": yaml is not None,
            "detail": "已安装" if yaml is not None else "缺少 PyYAML，请先安装 requirements.txt",
        },
        {
            "name": "Repo validation",
            "ok": not validation_errors,
            "detail": "通过" if not validation_errors else "；".join(validation_errors),
        },
        {
            "name": "Write access",
            "ok": write_ok,
            "detail": write_detail if write_ok else f"无法写入 doubles/：{write_detail}",
        },
        {
            "name": "UTF-8 terminal",
            "ok": terminal_ok,
            "detail": (
                "终端编码看起来正常。"
                if terminal_ok
                else "当前终端可能不是 UTF-8；若出现乱码，请先运行 `chcp 65001`。"
            ),
        },
    ]
    ok = all(item["ok"] for item in checks[:-1]) and checks[-1]["ok"]
    return {
        "ok": ok,
        "checks": checks,
        "next_steps": [
            "python -m pip install -r requirements.txt",
            'python scripts/double_builder.py start --slug my-double --display-name "我的分身"',
        ],
    }


def format_doctor_report(report: dict[str, Any]) -> str:
    lines = ["create-double doctor", ""]
    for check in report["checks"]:
        label = "OK" if check["ok"] else "WARN"
        lines.append(f"[{label}] {check['name']}: {check['detail']}")
    lines.extend(["", "下一步："])
    lines.extend([f"- {step}" for step in report["next_steps"]])
    return "\n".join(lines)


def snapshot_outputs(root: Path, slug: str) -> Path | None:
    targets = [
        profile_path(root, slug),
        profile_md_path(root, slug),
        generated_skill_path(root, slug),
        session_path(root, slug),
    ]
    existing = [path for path in targets if path.exists()]
    if len(existing) < 3:
        return None

    profile = load_yaml(profile_path(root, slug))
    version = profile["meta"]["version"]
    stamp = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
    snapshot_dir = history_dir(root, slug) / f"{stamp}__v{version}"
    snapshot_dir.mkdir(parents=True, exist_ok=False)
    for source in existing:
        shutil.copy2(source, snapshot_dir / source.name)
    return snapshot_dir


def split_claims(items: list[dict[str, str]]) -> tuple[list[str], list[str]]:
    confirmed: list[str] = []
    inferred: list[str] = []
    for item in items:
        text = item.get("text", "").strip()
        if not text:
            continue
        if item.get("source") == "inferred":
            inferred.append(text)
        else:
            confirmed.append(text)
    return confirmed, inferred


def section_lines(title: str, confirmed: list[str], inferred: list[str]) -> list[str]:
    lines = [f"### {title}"]
    if confirmed:
        lines.append("Confirmed:")
        lines.extend([f"- {item}" for item in confirmed])
    if inferred:
        lines.append("Tentative:")
        lines.extend([f"- {item}" for item in inferred])
    if not confirmed and not inferred:
        lines.append("- none yet")
    lines.append("")
    return lines


def render_profile_markdown(profile: dict[str, Any], session: dict[str, Any]) -> str:
    lines = [
        f"# {profile['meta']['display_name']} Profile",
        "",
        "## Snapshot",
        f"- slug: `{profile['meta']['slug']}`",
        f"- language: `{profile['meta']['language']}`",
        f"- primary use case: `{profile['meta'].get('primary_use_case', 'general')}`",
        f"- version: `{profile['meta']['version']}`",
        f"- completeness: `{profile['meta']['completeness']}`",
        f"- current mode: `{session.get('mode', 'interview')}`",
        f"- interview depth: `{session.get('interview_depth', 'quick')}`",
        f"- remaining questions: `{len(session.get('pending_questions', []))}`",
        "",
    ]

    self_summary = profile["identity"]["self_summary"]
    confirmed_summary = []
    inferred_summary = []
    if self_summary.get("text"):
        if self_summary.get("source") == "inferred":
            inferred_summary.append(self_summary["text"])
        else:
            confirmed_summary.append(self_summary["text"])
    lines.extend(section_lines("Self Summary", confirmed_summary, inferred_summary))

    field_map = [
        ("Roles", profile["identity"]["roles"]),
        ("Contexts", profile["identity"]["contexts"]),
        ("Voice Tone", profile["voice"]["tone"]),
        ("Signature Phrases", profile["voice"]["signature_phrases"]),
        ("Taboo Phrases", profile["voice"]["taboo_phrases"]),
        ("Response Pattern", profile["voice"]["response_pattern"]),
        ("Priorities", profile["values"]["priorities"]),
        ("Non-Negotiables", profile["values"]["non_negotiables"]),
        ("Motivators", profile["values"]["motivators"]),
        ("Default Questions", profile["decision_model"]["default_questions"]),
        ("Tradeoff Biases", profile["decision_model"]["tradeoff_biases"]),
        ("Advice Style", profile["decision_model"]["advice_style"]),
        ("Failure Patterns", profile["decision_model"]["failure_patterns"]),
        ("Support Style", profile["interaction_style"]["support_style"]),
        ("Disagreement Style", profile["interaction_style"]["disagreement_style"]),
        ("Boundary Style", profile["interaction_style"]["boundary_style"]),
    ]
    for title, items in field_map:
        confirmed, inferred = split_claims(items)
        lines.extend(section_lines(title, confirmed, inferred))

    lines.append("## Anchor Examples")
    if profile["anchor_examples"]:
        for index, example in enumerate(profile["anchor_examples"], start=1):
            lines.append(f"{index}. Situation: {example['situation']}")
            lines.append(f"   Choice: {example['choice']}")
            lines.append(f"   Reason: {example['reason']}")
            lines.append(f"   Source: {example['source']}")
    else:
        lines.append("- none yet")
    lines.append("")

    lines.append("## Unknowns")
    if profile["unknowns"]:
        for item in profile["unknowns"]:
            why = f" ({item['why']})" if item.get("why") else ""
            lines.append(f"- `{item['slot']}`: {item['question']}{why}")
    else:
        lines.append("- none")
    lines.append("")

    lines.append("## Corrections")
    if profile["corrections"]:
        for item in profile["corrections"]:
            lines.append(f"- [{item['recorded_at']}] {item['applies_to']}: {item['text']}")
    else:
        lines.append("- none yet")
    lines.append("")

    lines.append("## Next Question")
    lines.append(f"- {next_question_from_state(profile, session) or 'none'}")
    lines.append("")
    return "\n".join(lines)


def render_runtime_skill(profile: dict[str, Any]) -> str:
    slug = profile["meta"]["slug"]
    display_name = profile["meta"]["display_name"]
    primary_use_case = str(profile["meta"].get("primary_use_case", "general"))
    summary = normalize_claim(profile["identity"]["self_summary"], default_source="unknown")

    def collect_confirmed(items: list[dict[str, str]]) -> list[str]:
        return [item["text"] for item in items if item.get("source") != "inferred" and item.get("text")]

    def collect_inferred(items: list[dict[str, str]]) -> list[str]:
        return [item["text"] for item in items if item.get("source") == "inferred" and item.get("text")]

    confirmed_lines: list[str] = []
    tentative_lines: list[str] = []

    if summary["text"]:
        target = tentative_lines if summary["source"] == "inferred" else confirmed_lines
        target.append(f"- 自我概括: {summary['text']}")

    runtime_groups = [
        ("角色", profile["identity"]["roles"]),
        ("语气", profile["voice"]["tone"]),
        ("口头表达", profile["voice"]["signature_phrases"]),
        ("避免表达", profile["voice"]["taboo_phrases"]),
        ("回应结构", profile["voice"]["response_pattern"]),
        ("优先级", profile["values"]["priorities"]),
        ("不可妥协", profile["values"]["non_negotiables"]),
        ("驱动力", profile["values"]["motivators"]),
        ("先问的问题", profile["decision_model"]["default_questions"]),
        ("取舍偏向", profile["decision_model"]["tradeoff_biases"]),
        ("给建议的方式", profile["decision_model"]["advice_style"]),
        ("常见盲点", profile["decision_model"]["failure_patterns"]),
        ("支持方式", profile["interaction_style"]["support_style"]),
        ("反对方式", profile["interaction_style"]["disagreement_style"]),
        ("设边界的方式", profile["interaction_style"]["boundary_style"]),
    ]

    for label, items in runtime_groups:
        confirmed = collect_confirmed(items)
        inferred = collect_inferred(items)
        if confirmed:
            confirmed_lines.append(f"- {label}: {'；'.join(confirmed)}")
        if inferred:
            tentative_lines.append(f"- {label}: {'；'.join(inferred)}")

    anchor_lines = []
    for example in profile["anchor_examples"]:
        prefix = "暂定" if example["source"] == "inferred" else "确认"
        anchor_lines.append(f"- {prefix}案例: {example['situation']} -> {example['choice']}；原因：{example['reason']}")

    description = (
        "Reply like this user's private digital double for conversation, self-reflection, and decision "
        "support. Use when the user wants answers aligned with this person's voice, values, and decision "
        "model. Never invent memories and label inference clearly."
    )

    lines = [
        "---",
        f"name: {slug}",
        f"description: {description}",
        "---",
        "",
        f"# {display_name}",
        "",
        "## Runtime Contract",
        "",
        f"- 主用途：{USE_CASE_LABELS.get(primary_use_case, primary_use_case)}。",
        "- 默认使用简体中文，除非用户明确要求其他语言。",
        "- 只做两件事：像这个人一样交流；按这个人的取舍方式给建议。",
        "- 不编造经历、时间、地点、关系或具体记忆。",
        "- 当资料不足时，直接说“这是基于现有资料的推断”或“我还不知道”。",
        "- 如果用户显式纠正你，优先服从用户的纠正。",
        "",
        "## Confirmed Material",
        "",
    ]
    lines.extend(confirmed_lines or ["- 资料仍然很少，请先说明你掌握的信息有限。"])
    lines.extend(["", "## Tentative Working Inferences", ""])
    lines.extend(tentative_lines or ["- 暂无。不要主动补编。"])
    lines.extend(["", "## Anchor Examples", ""])
    lines.extend(anchor_lines or ["- 暂无高信号案例，回答时必须保守。"])
    lines.extend(
        [
            "",
            "## Response Style",
            "",
            "- 先判断问题是日常对话、自我分析、还是求建议。",
            "- 日常对话时优先体现语气和表达习惯。",
            "- 自我分析时优先引用价值观、盲点、和反复出现的选择模式。",
            "- 给建议时先按既有默认问题澄清，再给符合该人格的建议。",
            "- 如果问题触达未知区域，先承认未知，再给条件化判断。",
            "",
        ]
    )
    return "\n".join(lines)


def render_outputs(root: Path, slug: str) -> dict[str, Any]:
    ensure_exists(root, slug)
    snapshot_dir = snapshot_outputs(root, slug)

    profile = ensure_profile_defaults(load_yaml(profile_path(root, slug)))
    session = ensure_session_defaults(load_yaml(session_path(root, slug)), profile)
    profile["meta"]["version"] = int(profile["meta"].get("version", 1)) + 1
    profile["meta"]["completeness"] = compute_completeness(profile)
    write_yaml(profile_path(root, slug), profile)
    write_yaml(session_path(root, slug), session)

    profile_md_path(root, slug).write_text(render_profile_markdown(profile, session), encoding="utf-8")
    generated_skill_path(root, slug).write_text(render_runtime_skill(profile), encoding="utf-8")
    return {
        "slug": slug,
        "profile": str(profile_path(root, slug)),
        "profile_md": str(profile_md_path(root, slug)),
        "skill": str(generated_skill_path(root, slug)),
        "snapshot": str(snapshot_dir) if snapshot_dir else None,
        "version": profile["meta"]["version"],
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


def root_from_arg(raw_root: str | None) -> Path:
    if raw_root:
        return Path(raw_root).resolve()
    return Path(__file__).resolve().parents[1]


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
