# create-double-skill examples

这个目录放的是“可直接拿来参考”的结构化 payload。

推荐顺序：

1. 先看 `initial-freeform-payload.json`
2. 再看 `correction-payload.json`
3. 用你自己的原始回答替换其中的文本
4. 通过 `apply-turn` 合并，再运行 `render`

## 最短演示流程

```powershell
python scripts/double_builder.py init --slug demo --display-name "演示分身"
python scripts/double_builder.py apply-turn --slug demo --payload-file examples/initial-freeform-payload.json
python scripts/double_builder.py render --slug demo
python scripts/double_builder.py apply-turn --slug demo --payload-file examples/correction-payload.json
python scripts/double_builder.py render --slug demo
```

## 说明

- 这些 payload 是演示格式，不是“唯一正确答案”
- 最好的 payload 应该尽量小、尽量准
- 如果一句话还不能确定，就先放进 `unknowns`
