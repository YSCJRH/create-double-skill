# generated artifacts

`start` 跑完之后，你至少会看到这三类产物。
在用途感知版本里，产物会明确写出这次 double 的主用途和访谈深度。

## 1. Canonical truth: `profile.yaml`

```yaml
meta:
  primary_use_case: work
values:
  priorities:
    - text: 可维护性
      source: direct
    - text: 长期可持续
      source: direct
decision_model:
  default_questions:
    - text: 我会先问目标、成功标准和最不能出错的地方
      source: direct
interaction_style:
  boundary_style:
    - text: 我会先把风险讲清楚，再给出我能接受的最小范围
      source: direct
```

## 2. Human-readable snapshot: `profile.md`

```md
## Snapshot
- primary use case: `work`
- interview depth: `quick`
- remaining questions: `2`

### Priorities
Confirmed:
- 可维护性
- 长期可持续

### Default Questions
Confirmed:
- 我会先问目标、成功标准和最不能出错的地方
```

## 3. Runtime double: `SKILL.md`

```md
## Runtime Contract

- 主要用途: work
- 重点模仿判断方式、边界风格和建议结构
- 遇到资料不足时，明确说这是推断，不伪造经历或记忆
```

第一次跑通的目标不是把字段填满，而是先拿到一版：

- 看得懂
- 能继续改
- 能继续补细节

的结果文件。
