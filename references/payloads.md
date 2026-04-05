# Payload Schema

`python scripts/double_builder.py apply-turn` expects a JSON payload.

## Shape

```json
{
  "route": "freeform",
  "mode_after": "freeform",
  "meta_updates": {
    "primary_use_case": "work"
  },
  "updates": {
    "identity.self_summary": {
      "text": "一个做决定前会先看长期影响的人",
      "source": "direct"
    },
    "values.priorities": [
      {
        "text": "长期可持续",
        "source": "direct"
      }
    ]
  },
  "anchor_examples": [
    {
      "situation": "团队催着上线一个理解还不稳定的功能",
      "choice": "先缩小范围",
      "reason": "不要让错误预期扩大",
      "source": "direct"
    }
  ],
  "unknowns": [
    {
      "slot": "interaction_style.boundary_style",
      "question": "你不舒服时会怎么设边界？",
      "why": "这会影响冲突场景下的分身表现。"
    }
  ],
  "corrections": [
    {
      "text": "我不会说'你应该'，我更常说'如果是我我会先...'",
      "applies_to": "voice.signature_phrases"
    }
  ],
  "session_updates": {
    "interview_track": "work",
    "interview_depth": "standard",
    "pending_questions": ["work_voice_tone", "work_anchor_example"],
    "asked_questions": ["work_priorities", "work_default_questions", "work_boundary_style"]
  },
  "next_question": "你不舒服时会怎么设边界？"
}
```

## Required Keys

- `route`

Everything else is optional. Omit empty keys rather than sending empty strings everywhere.

## Optional Session / Meta Keys

- `meta_updates.primary_use_case`
  lets higher-level onboarding flows mark the main job this double is being built for
- `session_updates.interview_track`
  current question track, such as `general` or `work`
- `session_updates.interview_depth`
  current interview depth: `quick`, `standard`, or `deep`
- `session_updates.pending_questions`
  question ids that have not been asked yet
- `session_updates.asked_questions`
  question ids already covered during the current onboarding flow

## `updates` Paths

Supported field paths:

- `identity.self_summary`
- `identity.roles`
- `identity.contexts`
- `voice.tone`
- `voice.signature_phrases`
- `voice.taboo_phrases`
- `voice.response_pattern`
- `values.priorities`
- `values.non_negotiables`
- `values.motivators`
- `decision_model.default_questions`
- `decision_model.tradeoff_biases`
- `decision_model.advice_style`
- `decision_model.failure_patterns`
- `interaction_style.support_style`
- `interaction_style.disagreement_style`
- `interaction_style.boundary_style`

## Merge Rules

- Single claim fields replace the previous value when the new value is non-empty.
- Claim lists append unique items and upgrade the source if a stronger source arrives.
- `unknowns` is treated as the refreshed current shortlist.
- `corrections` append chronologically.
- Rendering snapshots the previous generated outputs before writing new ones.
