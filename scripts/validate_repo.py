#!/usr/bin/env python3
"""Validate the public create-double-skill repository layout and metadata."""

from __future__ import annotations

from pathlib import Path

import yaml


REQUIRED_PATHS = [
    "LICENSE",
    "README.md",
    "SKILL.md",
    "agents/openai.yaml",
    "assets/profile-seed.yaml",
    "assets/question-tracks.yaml",
    "assets/social-preview.svg",
    ".github/ISSUE_TEMPLATE/bug_report.yml",
    ".github/ISSUE_TEMPLATE/config.yml",
    ".github/ISSUE_TEMPLATE/feature_request.yml",
    "prompts/router.md",
    "prompts/interview.md",
    "prompts/freeform.md",
    "prompts/correction.md",
    "prompts/rendering.md",
    "references/profile-schema.md",
    "references/payloads.md",
    "scripts/double_builder.py",
    "tests/test_double_builder.py",
    "examples/README.md",
    "examples/start-transcript.md",
    "examples/start-transcript-general.md",
    "examples/start-transcript-work.md",
    "examples/start-transcript-self-dialogue.md",
    "examples/start-transcript-external.md",
    "examples/generated-artifacts.md",
    "examples/correction-before-after.md",
    "examples/initial-freeform-payload.json",
    "examples/correction-payload.json",
]


def load_yaml(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"{path.name} must start with YAML frontmatter")
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"{path.name} has malformed YAML frontmatter")
    return yaml.safe_load(parts[1]) or {}


def validate(repo_root: Path) -> list[str]:
    errors: list[str] = []

    for relative_path in REQUIRED_PATHS:
        if not (repo_root / relative_path).exists():
            errors.append(f"missing required path: {relative_path}")

    if errors:
        return errors

    skill_meta = load_frontmatter(repo_root / "SKILL.md")
    if skill_meta.get("name") != "create-double":
        errors.append("SKILL.md frontmatter name must be 'create-double'")
    description = str(skill_meta.get("description", "")).strip()
    if not description:
        errors.append("SKILL.md frontmatter description must be non-empty")

    openai_yaml = load_yaml(repo_root / "agents/openai.yaml") or {}
    interface = openai_yaml.get("interface", {})
    for key in ("display_name", "short_description", "default_prompt"):
        if not str(interface.get(key, "")).strip():
            errors.append(f"agents/openai.yaml is missing interface.{key}")

    profile_seed = load_yaml(repo_root / "assets/profile-seed.yaml") or {}
    for key in (
        "meta",
        "identity",
        "voice",
        "values",
        "decision_model",
        "interaction_style",
        "anchor_examples",
        "unknowns",
        "corrections",
    ):
        if key not in profile_seed:
            errors.append(f"assets/profile-seed.yaml is missing top-level key '{key}'")

    meta = profile_seed.get("meta", {}) if isinstance(profile_seed, dict) else {}
    if meta.get("primary_use_case") != "general":
        errors.append("assets/profile-seed.yaml must default meta.primary_use_case to 'general'")

    question_tracks = load_yaml(repo_root / "assets/question-tracks.yaml") or {}
    tracks = question_tracks.get("tracks", {}) if isinstance(question_tracks, dict) else {}
    for track_name in ("general", "work", "self-dialogue", "external", "custom"):
        if track_name not in tracks:
            errors.append(f"assets/question-tracks.yaml is missing track '{track_name}'")

    return errors


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    errors = validate(repo_root)
    if errors:
        print("Repository validation failed:")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    print("Repository structure is valid.")


if __name__ == "__main__":
    main()
