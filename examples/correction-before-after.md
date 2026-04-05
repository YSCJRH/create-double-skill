# correction before / after

`create-double-skill` 的灵魂不是“一次生成”，而是“生成后能改”。

下面是一个极简例子。

## before

```md
## Signature Phrases
Tentative:
- 你应该先冷静一下
```

## user correction

```text
我不会直接说“你应该”，我更常说“如果是我，我会先把边界讲清楚”。
```

## after

```md
## Taboo Phrases
Confirmed:
- 你应该

## Signature Phrases
Confirmed:
- 如果是我，我会先把边界讲清楚
```

这种 correction 会同时做三件事：

- 把原句记进 `corrections`
- 把更像你的表达回写到结构化字段
- 重新渲染 `profile.md` 和 `SKILL.md`
