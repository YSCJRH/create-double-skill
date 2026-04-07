"""Profile and session normalization, merge, and completeness helpers."""

from __future__ import annotations

from datetime import datetime
from typing import Any


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
USE_CASE_LABELS = {
    "general": "通用分身",
    "work": "工作协作版",
    "self-dialogue": "自我对话版",
    "external": "对外表达版",
    "custom": "自定义用途",
}


def now_iso() -> str:
    return datetime.now().astimezone().replace(microsecond=0).isoformat()


def blank_profile(
    slug: str,
    display_name: str,
    language: str = "zh-CN",
    *,
    unknowns: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
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
        "unknowns": list(unknowns or []),
        "corrections": [],
    }


def blank_session(profile: dict[str, Any], *, next_question: str | None = None) -> dict[str, Any]:
    return {
        "mode": "interview",
        "last_route": "switch_mode",
        "interview_track": str(profile["meta"].get("primary_use_case", "general")),
        "interview_depth": "quick",
        "pending_questions": [],
        "asked_questions": [],
        "next_question": (next_question or next_question_from_profile(profile)),
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
