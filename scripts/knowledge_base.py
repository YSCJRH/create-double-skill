#!/usr/bin/env python3
"""Private knowledge-base scaffolding and maintenance for create-double-skill."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - exercised via CLI in real environments
    yaml = None


PROJECT_WIKI_PAGES = (
    "overview.md",
    "product-principles.md",
    "use-cases.md",
    "interview-system.md",
    "runtime-contract.md",
    "known-risks.md",
    "decision-log.md",
    "public-surface.md",
)

DOUBLE_WIKI_PAGES = (
    "overview.md",
    "values-and-priorities.md",
    "decision-patterns.md",
    "boundaries.md",
    "voice-and-phrasing.md",
    "anchor-examples.md",
    "open-questions.md",
)


def require_yaml(command_name: str = "this command") -> None:
    if yaml is None:
        raise RuntimeError(
            f"PyYAML is required for {command_name}. Run `python -m pip install -r requirements.txt` first."
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


def now_iso() -> str:
    return datetime.now().astimezone().replace(microsecond=0).isoformat()


def timestamp_token() -> str:
    return datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")


def repo_root_from_arg(raw_root: str | None) -> Path:
    if raw_root:
        return Path(raw_root).resolve()
    return Path(__file__).resolve().parents[1]


def normalize_slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower())
    slug = re.sub(r"-{2,}", "-", slug).strip("-")
    if not slug:
        raise ValueError("slug must contain at least one ASCII letter or digit")
    return slug


def sanitize_name(value: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip())
    text = re.sub(r"-{2,}", "-", text).strip("-")
    return text or "entry"


def relative_to_root(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def question_tracks_path(root: Path) -> Path:
    return root / "assets" / "question-tracks.yaml"


@lru_cache(maxsize=8)
def load_question_prompt_map(root_string: str) -> dict[str, str]:
    require_yaml("question prompt lookup")
    root = Path(root_string)
    path = question_tracks_path(root)
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    prompts: dict[str, str] = {}
    for track in (data.get("tracks") or {}).values():
        for section in ("base_questions", "follow_up_questions"):
            for question in track.get(section, []):
                prompts[str(question.get("id", "")).strip()] = str(question.get("prompt", "")).strip()
    return prompts


def load_yaml(path: Path) -> dict[str, Any]:
    require_yaml(path.name)
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def frontmatter_text(metadata: dict[str, Any], body: str) -> str:
    require_yaml("frontmatter rendering")
    header = yaml.safe_dump(metadata, allow_unicode=True, sort_keys=False, width=1000).strip()
    return f"---\n{header}\n---\n\n{body.strip()}\n"


def parse_frontmatter_doc(path: Path) -> dict[str, Any]:
    text = read_text(path)
    if not text.startswith("---\n"):
        return {"metadata": {}, "body": text}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {"metadata": {}, "body": text}
    require_yaml("frontmatter parsing")
    metadata = yaml.safe_load(parts[1]) or {}
    body = parts[2].lstrip("\n")
    return {"metadata": metadata, "body": body}


def project_kb_root(root: Path) -> Path:
    return root / ".project-kb"


def double_root(root: Path, slug: str) -> Path:
    return root / "doubles" / normalize_slug(slug)


def double_kb_root(root: Path, slug: str) -> Path:
    return double_root(root, slug) / "kb"


def kb_paths(root: Path, target: str, slug: str | None = None) -> dict[str, Path]:
    if target == "project":
        base = project_kb_root(root)
    elif target == "double":
        if not slug:
            raise ValueError("double target requires --slug")
        base = double_kb_root(root, slug)
    else:
        raise ValueError(f"unsupported target '{target}'")

    return {
        "root": base,
        "raw": base / "raw",
        "wiki": base / "wiki",
        "index": base / "index.md",
        "log": base / "log.md",
        "schema": base / "SCHEMA.md",
    }


def ensure_target_context(root: Path, target: str, slug: str | None = None) -> str | None:
    if target == "double":
        if not slug:
            raise ValueError("double target requires --slug")
        normalized = normalize_slug(slug)
        if not double_root(root, normalized).exists():
            raise FileNotFoundError(f"double '{normalized}' does not exist under {root / 'doubles'}")
        return normalized
    return None


def append_log(log_path: Path, message: str) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    line = f"- {now_iso()} {message}\n"
    if log_path.exists():
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(line)
    else:
        with log_path.open("w", encoding="utf-8") as handle:
            handle.write("# Knowledge Base Log\n\n")
            handle.write(line)


def count_records(records: list[dict[str, Any]]) -> dict[str, int]:
    return dict(sorted(Counter(str(record["metadata"].get("source_kind", "unknown")) for record in records).items()))


def scan_raw_records(raw_dir: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if not raw_dir.exists():
        return records
    for path in sorted(raw_dir.rglob("*.md")):
        parsed = parse_frontmatter_doc(path)
        records.append(
            {
                "path": path,
                "metadata": parsed["metadata"],
                "body": parsed["body"],
            }
        )
    return records


def markdown_links(text: str) -> list[str]:
    return re.findall(r"\[[^\]]+\]\(([^)]+)\)", text)


def collect_broken_links(root: Path, kb_root: Path, pages: list[Path]) -> list[str]:
    errors: list[str] = []
    for page in pages:
        for link in markdown_links(read_text(page)):
            if link.startswith(("http://", "https://", "mailto:", "#")):
                continue
            target = (page.parent / link).resolve()
            if target.exists():
                continue
            repo_target = (root / link).resolve()
            if repo_target.exists():
                continue
            errors.append(f"broken link in {relative_to_root(page, kb_root)} -> {link}")
    return sorted(set(errors))


def linked_wiki_targets(index_path: Path) -> set[str]:
    if not index_path.exists():
        return set()
    targets: set[str] = set()
    for link in markdown_links(read_text(index_path)):
        if link.startswith("wiki/"):
            targets.add(Path(link).name)
    return targets


def stable_promotion_gaps(records: list[dict[str, Any]]) -> list[str]:
    warnings: list[str] = []
    for record in records:
        metadata = record["metadata"]
        if not metadata.get("stable"):
            continue
        candidate_paths = {str(item).strip() for item in metadata.get("candidate_paths", []) if str(item).strip()}
        promoted_paths = {str(item).strip() for item in metadata.get("promoted_paths", []) if str(item).strip()}
        missing = sorted(candidate_paths - promoted_paths)
        if missing:
            warnings.append(
                f"stable knowledge in {record['path'].name} is not yet promoted: {', '.join(missing)}"
            )
    return warnings


def stale_source_refs(root: Path, records: list[dict[str, Any]]) -> list[str]:
    warnings: list[str] = []
    for record in records:
        metadata = record["metadata"]
        source_ref = str(metadata.get("source_ref", "")).strip()
        if not source_ref or source_ref.startswith(("http://", "https://", "gist:", "github:")):
            continue
        candidate = (root / source_ref).resolve()
        if not candidate.exists():
            warnings.append(f"stale source_ref in {record['path'].name}: {source_ref}")
    return warnings


def format_claim_block(title: str, items: list[dict[str, Any]]) -> list[str]:
    lines = [f"## {title}"]
    if items:
        confirmed = [item["text"] for item in items if item.get("source") != "inferred" and item.get("text")]
        tentative = [item["text"] for item in items if item.get("source") == "inferred" and item.get("text")]
        if confirmed:
            lines.append("")
            lines.append("Confirmed:")
            lines.extend([f"- {item}" for item in confirmed])
        if tentative:
            lines.append("")
            lines.append("Tentative:")
            lines.extend([f"- {item}" for item in tentative])
    else:
        lines.append("")
        lines.append("- none yet")
    lines.append("")
    return lines


def render_project_schema() -> str:
    return """# Project Knowledge Base Schema

This private knowledge base stores maintainership knowledge for `create-double-skill`.

## ingest

- Add immutable source records under `raw/`.
- Keep one source per markdown file.
- Record `source_kind`, `source_ref` or `source_uri`, `recorded_at`, `trust_level`, and `scope` in frontmatter.

## query

- Read `index.md` first.
- Then open the relevant `wiki/*.md` page.
- Only fall back to `raw/` when the wiki page needs evidence or historical detail.

## lint

- Detect wiki pages that are not linked from `index.md`.
- Detect broken local markdown links.
- Detect stale repo references after files are deleted or moved.
- Detect maintainer notes that should be promoted into a stable wiki page.
"""


def render_double_schema() -> str:
    return """# Double Knowledge Base Schema

This private knowledge base stores high-signal knowledge events for one double.

## ingest

- Store compressed knowledge events in `raw/`.
- Do not store complete chat transcripts by default.
- Prefer durable signals such as new priorities, new boundaries, anchor examples, and explicit corrections.

## query

- Read `index.md` first.
- Then read the relevant `wiki/*.md` page.
- Use `raw/` only when the wiki needs evidence or conflict resolution.

## lint

- Detect wiki pages that are not linked from `index.md`.
- Detect broken local markdown links.
- Detect stable knowledge events that have not yet been promoted into `profile.yaml`.
- Detect stale references to removed repo materials.
"""


def project_index(records: list[dict[str, Any]]) -> str:
    counts = count_records(records)
    lines = [
        "# Project Knowledge Base",
        "",
        "## Product",
        "- [Overview](wiki/overview.md)",
        "- [Product Principles](wiki/product-principles.md)",
        "- [Use Cases](wiki/use-cases.md)",
        "",
        "## Implementation",
        "- [Interview System](wiki/interview-system.md)",
        "- [Runtime Contract](wiki/runtime-contract.md)",
        "- [Decision Log](wiki/decision-log.md)",
        "",
        "## Quality",
        "- [Known Risks](wiki/known-risks.md)",
        "",
        "## Public Surface",
        "- [Public Surface](wiki/public-surface.md)",
        "",
        "## Raw Source Summary",
        f"- total records: {len(records)}",
    ]
    for kind, count in counts.items():
        lines.append(f"- {kind}: {count}")
    return "\n".join(lines)


def project_pages(root: Path, records: list[dict[str, Any]]) -> dict[str, str]:
    repo_files = [
        "README.md",
        "SKILL.md",
        "prompts/interview.md",
        "references/profile-schema.md",
        "examples/README.md",
        "scripts/double_builder.py",
    ]
    record_counts = count_records(records)
    decision_items = []
    for record in sorted(records, key=lambda item: str(item["metadata"].get("recorded_at", "")), reverse=True):
        title = str(record["metadata"].get("title", record["path"].stem)).strip()
        source_kind = str(record["metadata"].get("source_kind", "unknown")).strip()
        recorded_at = str(record["metadata"].get("recorded_at", "")).strip()
        decision_items.append(f"- {recorded_at} [{source_kind}] {title}")
    risk_items = []
    for record in records:
        source_kind = str(record["metadata"].get("source_kind", "")).lower()
        if any(marker in source_kind for marker in ("risk", "audit", "release", "public", "maintainer-history")):
            title = str(record["metadata"].get("title", record["path"].stem)).strip()
            risk_items.append(f"- {title} ({record['metadata'].get('source_kind', 'unknown')})")
    source_breakdown = [f"- {kind}: {count}" for kind, count in record_counts.items()] or ["- none yet"]
    risk_summary = risk_items or ["- none recorded yet"]
    decision_summary = decision_items or ["- none yet"]
    public_notes = [f"- `{candidate}`" for candidate in (
        "README.md",
        "SKILL.md",
        "examples/README.md",
        ".github/workflows/ci.yml",
        ".github/ISSUE_TEMPLATE/config.yml",
    )]
    return {
        "overview.md": "\n".join(
            [
                "# Overview",
                "",
                "This private wiki tracks how the repo is supposed to work, what changed recently, and which raw notes back those conclusions.",
                "",
                "## Current Snapshot",
                f"- repo root: `{root}`",
                "- public runtime truth stays in `profile.yaml` for each double",
                "- project knowledge stays private under `.project-kb/`",
                f"- raw record count: {len(records)}",
                "",
                "## Source Breakdown",
                *source_breakdown,
                "",
                "## First Files To Open",
                *(f"- `{path}`" for path in repo_files),
            ]
        ),
        "product-principles.md": "\n".join(
            [
                "# Product Principles",
                "",
                "- Keep `profile.yaml` as the only runtime structured source of truth.",
                "- Keep the product local-first and private by default.",
                "- Prefer high-signal self-modeling over full life-logging.",
                "- Let explicit corrections override earlier guesses.",
                "- Separate direct user statements from inference.",
                "- Never fabricate memories, experiences, relationships, or timelines.",
                "- Do not rely on automatic high-privacy ingestion in P0 or P1.",
                "- Keep the public repo lightweight; keep maintainer memory private.",
            ]
        ),
        "use-cases.md": "\n".join(
            [
                "# Use Cases",
                "",
                "## Public user-facing doubles",
                "- `work`: collaboration, tradeoffs, review style, and expectation setting",
                "- `self-dialogue`: internal self-talk, clarity, and anti-self-deception",
                "- `external`: outward expression, tone, and public boundaries",
                "- `general`: a lighter all-purpose starting point",
                "",
                "## Internal maintenance",
                "- capture benchmark notes privately",
                "- track public-surface audits and release hygiene",
                "- remember product decisions without re-reading every raw note",
            ]
        ),
        "interview-system.md": "\n".join(
            [
                "# Interview System",
                "",
                "## Current entry points",
                "- `python scripts/double_builder.py start ...`",
                "- `python scripts/double_builder.py correct ...`",
                "- `python scripts/double_builder.py doctor`",
                "",
                "## Tracks",
                "- `general`",
                "- `work`",
                "- `self-dialogue`",
                "- `external`",
                "- `custom`",
                "",
                "## Runtime files",
                "- `assets/question-tracks.yaml` keeps the editable question bank",
                "- `prompts/interview.md` explains question-selection guidance",
                "- `references/profile-schema.md` defines the writable schema surface",
            ]
        ),
        "runtime-contract.md": "\n".join(
            [
                "# Runtime Contract",
                "",
                "- `profile.yaml` stays canonical for runtime behavior.",
                "- `profile.md` and generated `SKILL.md` render only from `profile.yaml`.",
                "- The knowledge base is an accumulation and evidence layer, not a second runtime truth source.",
                "- Stable knowledge can be promoted from the KB into `profile.yaml`, but uncertain or conflicting material stays in the KB or `unknowns`.",
                "- Public docs should stay user-facing; private project memory should stay under `.project-kb/`.",
            ]
        ),
        "known-risks.md": "\n".join(
            [
                "# Known Risks",
                "",
                "## Active watchpoints",
                "- Windows PowerShell may still display Chinese preview text poorly when input is piped instead of typed interactively.",
                "- GitHub HTML pages can lag behind raw file or API truth because of caching.",
                "- Private maintainer notes should never leak back into public docs or issue templates.",
                "",
                "## Risk-related source notes",
                *risk_summary,
            ]
        ),
        "decision-log.md": "\n".join(
            [
                "# Decision Log",
                "",
                "## Recent raw records",
                *decision_summary,
            ]
        ),
        "public-surface.md": "\n".join(
            [
                "# Public Surface",
                "",
                "These are the main public entry points the repo should keep coherent:",
                "",
                *(public_notes),
                "",
                "## Rules",
                "- README default path should point to `start --use-case work`.",
                "- Public pages should not link to deleted maintainer-only docs.",
                "- Release copy should match the current `start` flow.",
                "- Private project memory belongs in `.project-kb/`, not in tracked `docs/`.",
            ]
        ),
    }


def claim_texts(items: list[dict[str, Any]], *, source: str | None = None) -> list[str]:
    results: list[str] = []
    for item in items:
        text = str(item.get("text", "")).strip()
        if not text:
            continue
        if source is None or str(item.get("source", "")).strip() == source:
            results.append(text)
    return results


def section_lines(title: str, confirmed: list[str], tentative: list[str]) -> list[str]:
    lines = [f"# {title}", ""]
    if confirmed:
        lines.append("Confirmed:")
        lines.extend([f"- {item}" for item in confirmed])
        lines.append("")
    if tentative:
        lines.append("Tentative:")
        lines.extend([f"- {item}" for item in tentative])
        lines.append("")
    if not confirmed and not tentative:
        lines.append("- none yet")
        lines.append("")
    return lines


def question_prompt_lookup(root: Path, question_id: str) -> str:
    return load_question_prompt_map(str(root)).get(question_id, question_id)


def profile_for_double(root: Path, slug: str) -> dict[str, Any]:
    path = double_root(root, slug) / "profile.yaml"
    return load_yaml(path) if path.exists() else {}


def session_for_double(root: Path, slug: str) -> dict[str, Any]:
    path = double_root(root, slug) / "session.yaml"
    return load_yaml(path) if path.exists() else {}


def double_index(profile: dict[str, Any], records: list[dict[str, Any]]) -> str:
    counts = count_records(records)
    lines = [
        f"# {profile.get('meta', {}).get('display_name', 'Double')} Knowledge Base",
        "",
        "## Core Pages",
        "- [Overview](wiki/overview.md)",
        "- [Values and Priorities](wiki/values-and-priorities.md)",
        "- [Decision Patterns](wiki/decision-patterns.md)",
        "- [Boundaries](wiki/boundaries.md)",
        "- [Voice and Phrasing](wiki/voice-and-phrasing.md)",
        "- [Anchor Examples](wiki/anchor-examples.md)",
        "- [Open Questions](wiki/open-questions.md)",
        "",
        "## Raw Event Summary",
        f"- total records: {len(records)}",
    ]
    for kind, count in counts.items():
        lines.append(f"- {kind}: {count}")
    return "\n".join(lines)


def double_pages(root: Path, slug: str, records: list[dict[str, Any]]) -> dict[str, str]:
    profile = profile_for_double(root, slug)
    session = session_for_double(root, slug)
    meta = profile.get("meta", {})
    use_case = str(meta.get("primary_use_case", "general"))
    display_name = str(meta.get("display_name", slug))
    pending_ids = [str(item).strip() for item in session.get("pending_questions", []) if str(item).strip()]
    pending_prompts = [question_prompt_lookup(root, question_id) for question_id in pending_ids]
    corrected_phrases = []
    for record in records:
        if str(record["metadata"].get("source_kind", "")) == "correction":
            summary = str(record["metadata"].get("summary", "")).strip()
            if summary:
                corrected_phrases.append(summary)

    anchor_examples = profile.get("anchor_examples", [])
    anchor_lines = ["# Anchor Examples", ""]
    if anchor_examples:
        for index, example in enumerate(anchor_examples, start=1):
            anchor_lines.append(f"{index}. Situation: {example.get('situation', '')}")
            anchor_lines.append(f"   Choice: {example.get('choice', '')}")
            anchor_lines.append(f"   Reason: {example.get('reason', '')}")
            anchor_lines.append(f"   Source: {example.get('source', 'unknown')}")
    else:
        anchor_lines.append("- none yet")
    anchor_lines.append("")

    overview_lines = [
        "# Overview",
        "",
        f"- display name: `{display_name}`",
        f"- slug: `{meta.get('slug', slug)}`",
        f"- primary use case: `{use_case}`",
        f"- interview depth: `{session.get('interview_depth', 'quick')}`",
        f"- completeness: `{meta.get('completeness', 0)}`",
        f"- raw event count: `{len(records)}`",
        "",
        "## Latest pending prompts",
    ]
    if pending_prompts:
        overview_lines.extend([f"- {prompt}" for prompt in pending_prompts])
    else:
        overview_lines.append("- none")
    overview_lines.extend(
        [
            "",
            "## What this KB is for",
            "- keep high-signal evidence private",
            "- compile stable knowledge back into `profile.yaml` only when it is strong enough",
        ]
    )

    values_lines = section_lines(
        "Values and Priorities",
        claim_texts(profile.get("values", {}).get("priorities", [])),
        claim_texts(profile.get("values", {}).get("priorities", []), source="inferred"),
    )
    values_lines.extend(format_claim_block("Non-Negotiables", profile.get("values", {}).get("non_negotiables", [])))
    values_lines.extend(format_claim_block("Motivators", profile.get("values", {}).get("motivators", [])))

    decision_lines = section_lines(
        "Decision Patterns",
        claim_texts(profile.get("decision_model", {}).get("default_questions", [])),
        claim_texts(profile.get("decision_model", {}).get("default_questions", []), source="inferred"),
    )
    decision_lines.extend(format_claim_block("Tradeoff Biases", profile.get("decision_model", {}).get("tradeoff_biases", [])))
    decision_lines.extend(format_claim_block("Advice Style", profile.get("decision_model", {}).get("advice_style", [])))
    decision_lines.extend(format_claim_block("Failure Patterns", profile.get("decision_model", {}).get("failure_patterns", [])))

    boundary_lines = format_claim_block("Support Style", profile.get("interaction_style", {}).get("support_style", []))
    boundary_lines.extend(format_claim_block("Disagreement Style", profile.get("interaction_style", {}).get("disagreement_style", [])))
    boundary_lines.extend(format_claim_block("Boundary Style", profile.get("interaction_style", {}).get("boundary_style", [])))

    voice_lines = format_claim_block("Tone", profile.get("voice", {}).get("tone", []))
    voice_lines.extend(format_claim_block("Signature Phrases", profile.get("voice", {}).get("signature_phrases", [])))
    voice_lines.extend(format_claim_block("Taboo Phrases", profile.get("voice", {}).get("taboo_phrases", [])))
    voice_lines.extend(format_claim_block("Response Pattern", profile.get("voice", {}).get("response_pattern", [])))
    voice_lines.append("## Recent Corrections")
    voice_lines.append("")
    if corrected_phrases:
        voice_lines.extend([f"- {text}" for text in corrected_phrases[-5:]])
    else:
        voice_lines.append("- none yet")
    voice_lines.append("")

    open_question_lines = ["# Open Questions", "", "## Unknown slots"]
    unknowns = profile.get("unknowns", [])
    if unknowns:
        open_question_lines.extend(
            [
                f"- `{item.get('slot', '')}`: {item.get('question', '')}"
                + (f" ({item.get('why', '')})" if item.get("why") else "")
                for item in unknowns
            ]
        )
    else:
        open_question_lines.append("- none")
    open_question_lines.extend(["", "## Pending prompt ids"])
    if pending_ids:
        open_question_lines.extend(
            [f"- `{question_id}`: {question_prompt_lookup(root, question_id)}" for question_id in pending_ids]
        )
    else:
        open_question_lines.append("- none")
    open_question_lines.append("")

    return {
        "overview.md": "\n".join(overview_lines),
        "values-and-priorities.md": "\n".join(values_lines),
        "decision-patterns.md": "\n".join(decision_lines),
        "boundaries.md": "\n".join(boundary_lines),
        "voice-and-phrasing.md": "\n".join(voice_lines),
        "anchor-examples.md": "\n".join(anchor_lines),
        "open-questions.md": "\n".join(open_question_lines),
    }


def write_pages(base: Path, pages: dict[str, str]) -> None:
    for name, content in pages.items():
        write_text(base / name, content)


def init_kb(root: Path, target: str, slug: str | None = None) -> dict[str, Any]:
    normalized_slug = ensure_target_context(root, target, slug)
    paths = kb_paths(root, target, normalized_slug)
    paths["raw"].mkdir(parents=True, exist_ok=True)
    paths["wiki"].mkdir(parents=True, exist_ok=True)

    if target == "project":
        write_text(paths["schema"], render_project_schema())
        if not paths["log"].exists():
            write_text(paths["log"], "# Knowledge Base Log")
        refresh_project_kb(root)
        append_log(paths["log"], "init project knowledge base")
    else:
        write_text(paths["schema"], render_double_schema())
        if not paths["log"].exists():
            write_text(paths["log"], "# Knowledge Base Log")
        refresh_double_kb(root, normalized_slug)
        append_log(paths["log"], f"init double knowledge base for {normalized_slug}")

    return {
        "target": target,
        "slug": normalized_slug,
        "root": str(paths["root"]),
        "raw": str(paths["raw"]),
        "wiki": str(paths["wiki"]),
        "index": str(paths["index"]),
        "log": str(paths["log"]),
        "schema": str(paths["schema"]),
    }


def refresh_project_kb(root: Path) -> dict[str, Any]:
    paths = kb_paths(root, "project")
    paths["raw"].mkdir(parents=True, exist_ok=True)
    paths["wiki"].mkdir(parents=True, exist_ok=True)
    write_text(paths["schema"], render_project_schema())
    records = scan_raw_records(paths["raw"])
    write_text(paths["index"], project_index(records))
    write_pages(paths["wiki"], project_pages(root, records))
    return {"record_count": len(records), "wiki_pages": list(PROJECT_WIKI_PAGES)}


def refresh_double_kb(root: Path, slug: str) -> dict[str, Any]:
    normalized_slug = ensure_target_context(root, "double", slug)
    paths = kb_paths(root, "double", normalized_slug)
    paths["raw"].mkdir(parents=True, exist_ok=True)
    paths["wiki"].mkdir(parents=True, exist_ok=True)
    write_text(paths["schema"], render_double_schema())
    records = scan_raw_records(paths["raw"])
    profile = profile_for_double(root, normalized_slug)
    write_text(paths["index"], double_index(profile, records))
    write_pages(paths["wiki"], double_pages(root, normalized_slug, records))
    return {"record_count": len(records), "wiki_pages": list(DOUBLE_WIKI_PAGES)}


def ingest_source(
    root: Path,
    target: str,
    *,
    source_file: Path,
    kind: str,
    slug: str | None = None,
) -> dict[str, Any]:
    require_yaml("ingest")
    normalized_slug = ensure_target_context(root, target, slug)
    init_kb(root, target, normalized_slug)
    paths = kb_paths(root, target, normalized_slug)

    if not source_file.exists():
        raise FileNotFoundError(f"source file not found: {source_file}")

    timestamp = timestamp_token()
    safe_kind = sanitize_name(kind)
    target_dir = paths["raw"] / safe_kind
    target_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{timestamp}__{sanitize_name(source_file.stem)}.md"
    record_path = target_dir / filename
    scope = "project" if target == "project" else f"double/{normalized_slug}"
    metadata = {
        "source_kind": safe_kind,
        "source_ref": relative_to_root(source_file, root),
        "recorded_at": now_iso(),
        "trust_level": "imported",
        "scope": scope,
        "title": source_file.stem,
    }
    body = "\n".join(
        [
            f"# Imported Source: {source_file.name}",
            "",
            f"- original path: `{relative_to_root(source_file, root)}`",
            "",
            "```text",
            read_text(source_file).rstrip(),
            "```",
        ]
    )
    write_text(record_path, frontmatter_text(metadata, body))
    append_log(paths["log"], f"ingest {safe_kind} from {relative_to_root(source_file, root)}")

    if target == "project":
        refresh_project_kb(root)
    else:
        refresh_double_kb(root, normalized_slug)

    return {
        "target": target,
        "slug": normalized_slug,
        "record": str(record_path),
        "kind": safe_kind,
    }


def record_double_event(
    root: Path,
    slug: str,
    event_kind: str,
    *,
    summary: str,
    details: dict[str, Any] | None = None,
    candidate_paths: list[str] | None = None,
    promoted_paths: list[str] | None = None,
) -> dict[str, Any]:
    require_yaml("double knowledge event capture")
    normalized_slug = ensure_target_context(root, "double", slug)
    init_kb(root, "double", normalized_slug)
    paths = kb_paths(root, "double", normalized_slug)
    profile = profile_for_double(root, normalized_slug)
    session = session_for_double(root, normalized_slug)

    record_dir = paths["raw"] / "events"
    record_dir.mkdir(parents=True, exist_ok=True)
    record_path = record_dir / f"{timestamp_token()}__{sanitize_name(event_kind)}.md"
    details = details or {}
    candidate_paths = [path for path in (candidate_paths or []) if path]
    promoted_paths = [path for path in (promoted_paths or []) if path]
    metadata = {
        "source_kind": event_kind,
        "source_ref": f"double:{normalized_slug}:{event_kind}",
        "recorded_at": now_iso(),
        "trust_level": "direct",
        "scope": f"double/{normalized_slug}",
        "title": f"{event_kind} event",
        "summary": summary.strip(),
        "stable": True,
        "candidate_paths": candidate_paths,
        "promoted_paths": promoted_paths,
        "use_case": profile.get("meta", {}).get("primary_use_case", "general"),
        "interview_depth": session.get("interview_depth", "quick"),
    }
    body_lines = [
        f"# {event_kind.title()} Event",
        "",
        f"- slug: `{normalized_slug}`",
        f"- display name: `{profile.get('meta', {}).get('display_name', normalized_slug)}`",
        f"- primary use case: `{profile.get('meta', {}).get('primary_use_case', 'general')}`",
        f"- interview depth: `{session.get('interview_depth', 'quick')}`",
        "",
        "## Summary",
        summary.strip(),
    ]
    if details:
        body_lines.extend(
            [
                "",
                "## Details",
                "```json",
                json.dumps(details, ensure_ascii=False, indent=2, sort_keys=True),
                "```",
            ]
        )
    write_text(record_path, frontmatter_text(metadata, "\n".join(body_lines)))
    append_log(paths["log"], f"capture {event_kind} event for {normalized_slug}")
    refresh_double_kb(root, normalized_slug)
    return {"record": str(record_path), "slug": normalized_slug, "target": "double"}


def show_kb(root: Path, target: str, slug: str | None = None) -> dict[str, Any]:
    normalized_slug = ensure_target_context(root, target, slug) if target == "double" else None
    paths = kb_paths(root, target, normalized_slug)
    records = scan_raw_records(paths["raw"])
    latest_log = ""
    if paths["log"].exists():
        lines = [line.strip() for line in read_text(paths["log"]).splitlines() if line.strip() and not line.startswith("#")]
        latest_log = lines[-1] if lines else ""
    return {
        "target": target,
        "slug": normalized_slug,
        "root": str(paths["root"]),
        "record_count": len(records),
        "source_kinds": count_records(records),
        "wiki_pages": sorted([path.name for path in paths["wiki"].glob("*.md")]) if paths["wiki"].exists() else [],
        "latest_log_entry": latest_log,
        "index": str(paths["index"]),
    }


def lint_kb(root: Path, target: str, slug: str | None = None) -> dict[str, Any]:
    normalized_slug = ensure_target_context(root, target, slug) if target == "double" else None
    paths = kb_paths(root, target, normalized_slug)
    if not paths["root"].exists():
        raise FileNotFoundError(f"knowledge base does not exist at {paths['root']}")

    records = scan_raw_records(paths["raw"])
    pages = sorted(paths["wiki"].glob("*.md"))
    errors: list[str] = []
    warnings: list[str] = []

    linked_pages = linked_wiki_targets(paths["index"])
    for page in pages:
        if page.name not in linked_pages:
            errors.append(f"orphan wiki page not linked from index: {page.name}")

    errors.extend(collect_broken_links(root, paths["root"], [paths["index"], *pages] if paths["index"].exists() else pages))
    warnings.extend(stale_source_refs(root, records))
    if target == "double":
        warnings.extend(stable_promotion_gaps(records))

    return {
        "target": target,
        "slug": normalized_slug,
        "ok": not errors,
        "errors": sorted(set(errors)),
        "warnings": sorted(set(warnings)),
        "record_count": len(records),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage the private create-double knowledge bases.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_cmd = subparsers.add_parser("init", help="initialize a project or double knowledge base")
    init_cmd.add_argument("--target", required=True, choices=["project", "double"])
    init_cmd.add_argument("--slug")
    init_cmd.add_argument("--root")

    ingest_cmd = subparsers.add_parser("ingest", help="ingest a source file into a knowledge base")
    ingest_cmd.add_argument("--target", required=True, choices=["project", "double"])
    ingest_cmd.add_argument("--slug")
    ingest_cmd.add_argument("--source-file", required=True)
    ingest_cmd.add_argument("--kind", required=True)
    ingest_cmd.add_argument("--root")

    lint_cmd = subparsers.add_parser("lint", help="lint a knowledge base")
    lint_cmd.add_argument("--target", required=True, choices=["project", "double"])
    lint_cmd.add_argument("--slug")
    lint_cmd.add_argument("--root")

    show_cmd = subparsers.add_parser("show", help="show a knowledge base summary")
    show_cmd.add_argument("--target", required=True, choices=["project", "double"])
    show_cmd.add_argument("--slug")
    show_cmd.add_argument("--root")
    return parser


def emit(data: Any) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def main() -> None:
    ensure_utf8_output()
    require_yaml("knowledge-base commands")
    parser = build_parser()
    args = parser.parse_args()
    root = repo_root_from_arg(getattr(args, "root", None))

    if args.command == "init":
        emit(init_kb(root, args.target, args.slug))
        return

    if args.command == "ingest":
        emit(
            ingest_source(
                root,
                args.target,
                source_file=Path(args.source_file).resolve(),
                kind=args.kind,
                slug=args.slug,
            )
        )
        return

    if args.command == "lint":
        emit(lint_kb(root, args.target, args.slug))
        return

    if args.command == "show":
        emit(show_kb(root, args.target, args.slug))
        return

    parser.error("unknown command")


if __name__ == "__main__":
    main()
