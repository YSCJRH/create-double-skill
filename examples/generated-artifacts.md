# generated artifacts

`start` 跑完之后，你至少会看到这三类产物：

## 1. Canonical truth: `profile.yaml`

```yaml
values:
  priorities:
    - text: 长期可持续
      source: direct
    - text: 关系里的稳定感
      source: direct
decision_model:
  default_questions:
    - text: 我会先问这件事三个月后还重要吗
      source: direct
interaction_style:
  boundary_style:
    - text: 我会把底线讲清楚，但尽量不把气氛推到最糟
      source: direct
```

## 2. Human-readable snapshot: `profile.md`

```md
## Priorities
Confirmed:
- 长期可持续
- 关系里的稳定感

## Default Questions
Confirmed:
- 我会先问这件事三个月后还重要吗

## Boundary Style
Confirmed:
- 我会把底线讲清楚，但尽量不把气氛推到最糟
```

## 3. Runtime double: `SKILL.md`

```md
## Confirmed Material

- 优先级: 长期可持续；关系里的稳定感
- 先问的问题: 我会先问这件事三个月后还重要吗
- 设边界的方式: 我会把底线讲清楚，但尽量不把气氛推到最糟
```

first success 的目标不是“字段填满”，而是先得到一个足够真实、可继续修正的第一版。
