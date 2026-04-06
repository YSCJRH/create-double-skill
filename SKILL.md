---
name: create-double
description: Build and maintain a local, private digital double from interview answers and freeform self-description. Use when Codex needs to ask one high-value self-modeling question at a time, accept unstructured personal description, merge explicit corrections, and generate `profile.yaml`, `profile.md`, and a runnable double `SKILL.md` inside the local `doubles/slug-name/` folder without inventing memories or overstating certainty.
---

# Create Double

## Overview

Build a Chinese-first digital double that stays local to this repository. Keep `profile.yaml` as the canonical structured source of truth, use `session.yaml` for transient interview state, and regenerate `profile.md` plus the runtime `SKILL.md` from the profile.

The repo now also has a private knowledge-base layer:

- `doubles/<slug>/kb/`
  high-signal long-term knowledge for one double
- `.project-kb/`
  private maintainer knowledge for this repo

That layer is for accumulation and evidence. It does not replace `profile.yaml` as the runtime source of truth.

## Quick Start

### Fast path for a human first run

If the user only wants the first visible artifact, prefer:

```powershell
python scripts/double_builder.py start --slug my-work-double --display-name "工作分身" --use-case work
```

`start` now has two front-door decisions:

- `--use-case`
  `general`, `work`, `self-dialogue`, `external`, or `custom`
- `--depth`
  `quick`, `standard`, or `deep`

Recommended defaults:

- `quick`
  3 base questions, render first artifact, one natural-language correction, then optionally continue with 2 more questions
- `standard`
  3 base questions + 2 follow-up questions
- `deep`
  3 base questions + 4 follow-up questions, including at least one anchor example

Use `correct` right after generation when the user says “我不会这么说” or “我更在意 X”.

```powershell
python scripts/double_builder.py correct --slug my-work-double
```

`start` and `correct` now also capture private high-signal knowledge events under `doubles/<slug>/kb/`. Keep that automatic capture lightweight and local-only.

### Low-level path for Codex and custom workflows

1. Initialize a new double:

   ```powershell
   python scripts/double_builder.py init --slug my-double --display-name "我的分身"
   ```

2. Route the latest user turn:

   ```powershell
   python scripts/double_builder.py route --current-mode interview --text "我做决定时通常先看长期影响"
   ```

3. Read only the prompt file you need:
   - `prompts/router.md` for turn classification
   - `prompts/interview.md` for use-case-aware question selection
   - `prompts/freeform.md` for extracting structured data from self-description
   - `prompts/correction.md` for handling repair turns
   - `prompts/rendering.md` before using the generated double

4. Convert the user turn into a structured payload that follows `references/payloads.md`.

5. Apply the payload and render outputs:

   ```powershell
   python scripts/double_builder.py apply-turn --slug my-double --payload-file payload.json
   python scripts/double_builder.py render --slug my-double
   ```

6. Continue interviewing or answer through the generated double in `doubles/my-double/SKILL.md`.

## Core Rules

- Treat `继续提问`, `我自己说`, `先生成看看`, and `我要改一下` as hard control phrases.
- Ask at most one question at a time. Prioritize values, decision tradeoffs, voice, and boundary style before biography details.
- Keep direct user statements and model inferences separate. Use `source: direct` only when the user explicitly said it, `source: inferred` only for tentative synthesis, and corrections to override previous guesses.
- Never fabricate memories, dates, relationships, or preferences that are not anchored in the profile.
- If the profile is sparse, say so plainly and label any advice as inference.
- Keep every artifact local to `doubles/<slug>/`. Do not depend on external services.
- Treat each double as single-use-case-first. If the user wants a work self, a self-dialogue self, and an external-facing self, prefer separate slugs over one overloaded profile.

## Workflow

### 1. Initialize or Resume

- Create a slug in lowercase hyphen-case.
- Run `python scripts/double_builder.py init --slug <slug> --display-name "<name>"`.
- Reuse the existing folder if the double already exists. Read `profile.yaml`, `profile.md`, and `session.yaml` before asking new questions.

### 2. Route Every Turn

- Use `python scripts/double_builder.py route --current-mode <mode> --text "<user-turn>"` as a first-pass classifier.
- Confirm or override the route with your own judgment.
- Map each turn to one of `answer`, `freeform`, `correction`, `switch_mode`, or `finish`.
- Prefer `correction` when the user is refining prior language or values. Prefer `freeform` when the user gives a dense self-description. Prefer `answer` when the user is clearly answering the last question.

### 3. Build a Structured Payload

- Read `references/profile-schema.md` if you need field definitions.
- Read `references/payloads.md` for the JSON shape expected by `apply-turn`.
- Fill only the supported slots and keep the update small.
- Refresh `unknowns` with the top remaining gaps and set `next_question` to the single best follow-up.
- Keep `meta.primary_use_case`, `session.interview_track`, `session.interview_depth`, `session.pending_questions`, and `session.asked_questions` aligned with the active interview track.

### 4. Apply and Render

- Apply the payload with `apply-turn`.
- Render when the user says `先生成看看`, when a meaningful amount of new information has landed, or before you want to answer as the generated double.
- Rendering must preserve a snapshot under `history/` before overwriting prior generated artifacts.

### 5. Use the Generated Double

- The generated double is for two jobs only:
  - Talk like this person would talk.
  - Give advice using this person's values and decision model.
- If asked about experiences that are not present in `anchor_examples`, state that the answer is incomplete or inferred.
- If the user later corrects the double, write the correction to `corrections`, update the relevant fields, and render again.

## Adaptive Interview Notes

- `general`
  Focus on decisions, advice style, and boundaries.
- `work`
  Focus on collaboration style, risk tradeoffs, and expectation management.
- `self-dialogue`
  Focus on self-talk, self-deception boundaries, and what helps restore clarity.
- `external`
  Focus on outward expression, impression, and public or semi-public boundaries.
- `custom`
  First ask what the user wants the double to help with, then map to the nearest track.

## Output Contract

- Canonical profile: `doubles/<slug>/profile.yaml`
- Human-readable profile: `doubles/<slug>/profile.md`
- Generated runtime skill: `doubles/<slug>/SKILL.md`
- Transient session state: `doubles/<slug>/session.yaml`
- Private long-term knowledge: `doubles/<slug>/kb/`
- Snapshot history: `doubles/<slug>/history/<timestamp>__v<version>/`

## Knowledge Base Contract

- Treat `profile.yaml` as the only runtime structured truth.
- Treat `doubles/<slug>/kb/` as a private accumulation layer for stable evidence, corrections, and longer-lived context.
- Do not store full life-log transcripts by default.
- Do not invent knowledge pages that imply certainty beyond what the user actually said.
- If a knowledge event is still unstable or conflicting, leave it in the KB or `unknowns` instead of forcing it into `profile.yaml`.

## When To Read Extra Files

- Read `prompts/router.md` only when the route is ambiguous.
- Read `prompts/interview.md` only when choosing the next question.
- Read `prompts/freeform.md` only when extracting structured data from long self-description.
- Read `prompts/correction.md` only when a turn is mainly a repair.
- Read `prompts/rendering.md` only when generating or auditing the final double behavior.
