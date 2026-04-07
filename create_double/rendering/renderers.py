"""Markdown renderers for profile and runtime skill artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from create_double.domain.profile_model import (
    USE_CASE_LABELS,
    compute_completeness,
    ensure_profile_defaults,
    ensure_session_defaults,
    next_question_from_profile,
    normalize_claim,
)
from create_double.storage.repository import (
    ensure_exists,
    generated_skill_path,
    load_yaml,
    profile_md_path,
    profile_path,
    session_path,
    snapshot_outputs,
    write_yaml,
)


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
    next_question = str(session.get("next_question", "")).strip() or next_question_from_profile(profile) or "none"
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
    lines.append(f"- {next_question}")
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
