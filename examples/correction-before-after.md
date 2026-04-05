# correction before / after

`create-double-skill` 的灵魂不是“一次生成”，而是“生成后能改”。
在用途感知版本里，correction 还会顺手影响后续追问队列。

## before

```md
## Snapshot
- primary use case: `self-dialogue`
- interview depth: `standard`
- remaining questions: `2`

### Taboo Phrases
- none yet
```

## user correction

```text
我不会这么说“都会好的”，这种安慰会让我更想逃避。
```

## after

```md
## Taboo Phrases
Confirmed:
- 都会好的

## Corrections
- [timestamp] voice.taboo_phrases: 我不会这么说“都会好的”，这种安慰会让我更想逃避。
```

这种 correction 会同时做四件事：

- 把原句记进 `corrections`
- 把更像你的表达或禁用表达回写到结构化字段
- 重新渲染 `profile.md` 和 `SKILL.md`
- 如果这句修正已经覆盖了某个待追问的问题，就把它从 `pending_questions` 里移走
