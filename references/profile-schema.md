# Profile Schema

`profile.yaml` is the only structured source of truth for a double.

Top-level keys are fixed:

- `meta`
- `identity`
- `voice`
- `values`
- `decision_model`
- `interaction_style`
- `anchor_examples`
- `unknowns`
- `corrections`

## Field Shapes

### Claim object

Use claim objects for scalar and list entries that describe the person.

```yaml
text: "先看长期影响"
source: "direct"
```

Valid `source` values:

- `direct`: the user explicitly said it
- `inferred`: a tentative synthesis drawn from user material
- `correction`: a later repair that should outrank previous guesses
- `unknown`: reserved for blank single-value fields at initialization

### Meta

```yaml
meta:
  slug: "my-double"
  display_name: "我的分身"
  language: "zh-CN"
  version: 3
  completeness: 0.42
  primary_use_case: "work"
```

`primary_use_case` records the main job this double was created for.

Valid values:

- `general`
- `work`
- `self-dialogue`
- `external`

### Identity

```yaml
identity:
  self_summary:
    text: "一个做决定前会先看长期影响的人"
    source: "direct"
  roles:
    - text: "产品经理"
      source: "direct"
  contexts:
    - text: "工作中偏果断，关系里更谨慎"
      source: "direct"
```

### Voice / Values / Decision Model / Interaction Style

Each list field stores claim objects.

Recommended meaning:

- `voice.tone`: stable tone descriptors
- `voice.signature_phrases`: phrases the person naturally uses
- `voice.taboo_phrases`: phrases the person rejects
- `voice.response_pattern`: structural habits such as "先问背景，再给判断"
- `values.priorities`: what they try to protect or maximize
- `values.non_negotiables`: hard boundaries
- `values.motivators`: what energizes them
- `decision_model.default_questions`: the first questions they ask before deciding
- `decision_model.tradeoff_biases`: repeated biases like "偏长期，不抢短期便宜"
- `decision_model.advice_style`: how they usually give advice
- `decision_model.failure_patterns`: recurring blind spots
- `interaction_style.support_style`: how they comfort or support others
- `interaction_style.disagreement_style`: how they disagree
- `interaction_style.boundary_style`: how they set boundaries

### Anchor examples

Use small, high-signal examples only.

```yaml
anchor_examples:
  - situation: "团队想快速上线一个判断还不稳定的功能"
    choice: "先缩小范围，再收集反馈"
    reason: "宁可慢一点，也不要让错误预期扩大"
    source: "direct"
```

### Unknowns

Keep only the most useful gaps.

```yaml
unknowns:
  - slot: "interaction_style.boundary_style"
    question: "你不舒服时会怎么设边界？"
    why: "这决定冲突场景下的表达方式。"
```

### Corrections

Record explicit repairs in chronological order.

```yaml
corrections:
  - text: "我不会说'你应该'，我更常说'如果是我我会先...'"
    applies_to: "voice.signature_phrases"
    recorded_at: "2026-04-03T15:12:00+08:00"
```

## Guidance

- Prefer short, specific claims over long essays.
- Put the user's wording into `direct` claims when it matters stylistically.
- Put open questions into `unknowns`, not into inferred claims.
- Keep the profile sparse and honest rather than comprehensive and shaky.
