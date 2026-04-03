#!/usr/bin/env python3
"""Local builder for create-double skill artifacts."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

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


def now_iso() -> str:
    return datetime.now().astimezone().replace(microsecond=0).isoformat()


def normalize_slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower())
    slug = re.sub(r"-{2,}", "-", slug).strip("-")
    if not slug:
        raise ValueError("slug must contain at least one ASCII letter or digit")
    return slug


def default_unknowns() -> list[dict[str, str]]:
    return [
        {
            "slot": "values.priorities",
            "question": "你做重要决定时，通常先保护什么？",
            "why": "这决定分身的整体取舍顺序。",
        },
        {
            "slot": "decision_model.default_questions",
            "question": "你做判断前最先会问自己的问题是什么？",
            "why": "这决定分身遇事时的第一反应。",
        },
        {
            "slot": "voice.tone",
            "question": "别人会怎么形容你的语气和说话节奏？",
            "why": "这决定分身听起来像不像你。",
        },
        {
            "slot": "interaction_style.boundary_style",
            "question": "你不舒服时会怎么设边界？",
            "why": "这会影响分身在冲突和压力下的表现。",
        },
    ]


def blank_profile(slug: str, display_name: str, language: str = "zh-CN") -> dict[str, Any]:
    return {
        "meta": {
            "slug": slug,
            "display_name": display_name,
            "language": language,
            "version": 1,
            "completeness": 0.0,
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
    next_question = profile["unknowns"][0]["question"] if profile["unknowns"] else ""
    return {
        "mode": "interview",
        "last_route": "switch_mode",
        "next_question": next_question,
        "updated_at": now_iso(),
    }


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def write_yaml(path: Path, data: dict[str, Any]) -> None:
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
    unknowns = profile.get("unknowns", [])
    if unknowns:
        return str(unknowns[0].get("question", "")).strip()
    return ""


def apply_turn(root: Path, slug: str, payload: dict[str, Any]) -> dict[str, Any]:
    ensure_exists(root, slug)
    profile = load_yaml(profile_path(root, slug))
    session = load_yaml(session_path(root, slug))

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

    profile["meta"]["completeness"] = compute_completeness(profile)
    session["mode"] = mode_after
    session["last_route"] = route
    session["next_question"] = str(payload.get("next_question", "")).strip() or next_question_from_state(profile, session)
    session["updated_at"] = now_iso()

    write_yaml(profile_path(root, slug), profile)
    write_yaml(session_path(root, slug), session)
    return {
        "slug": slug,
        "route": route,
        "mode_after": mode_after,
        "completeness": profile["meta"]["completeness"],
        "next_question": session["next_question"],
    }


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
        f"- version: `{profile['meta']['version']}`",
        f"- completeness: `{profile['meta']['completeness']}`",
        f"- current mode: `{session.get('mode', 'interview')}`",
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

    profile = load_yaml(profile_path(root, slug))
    session = load_yaml(session_path(root, slug))
    profile["meta"]["version"] = int(profile["meta"].get("version", 1)) + 1
    profile["meta"]["completeness"] = compute_completeness(profile)
    write_yaml(profile_path(root, slug), profile)

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
    profile = load_yaml(profile_path(root, slug))
    session = load_yaml(session_path(root, slug))
    return {
        "slug": slug,
        "display_name": profile["meta"]["display_name"],
        "version": profile["meta"]["version"],
        "completeness": profile["meta"]["completeness"],
        "mode": session.get("mode", "interview"),
        "next_question": next_question_from_state(profile, session),
        "unknown_slots": [item["slot"] for item in profile.get("unknowns", [])],
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
    parser = argparse.ArgumentParser(description="Local builder for create-double")
    subparsers = parser.add_subparsers(dest="command", required=True)

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
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "route":
        emit(classify_turn(args.text, current_mode=args.current_mode))
        return

    root = root_from_arg(getattr(args, "root", None))

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
