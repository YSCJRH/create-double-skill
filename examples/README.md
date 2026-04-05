# create-double-skill examples

如果你是第一次来到这个仓库，先不要从 payload 开始。

优先顺序建议：

1. 先用 `python scripts/double_builder.py start --slug my-double --display-name "我的分身"` 跑通第一次成功
2. 再看 [start-transcript.md](start-transcript.md)，确认交互大概长什么样
3. 再看 [generated-artifacts.md](generated-artifacts.md)，确认产物长什么样
4. 最后才看低层 payload 示例

## First-Run Assets

- [start-transcript.md](start-transcript.md)
- [generated-artifacts.md](generated-artifacts.md)
- [correction-before-after.md](correction-before-after.md)

这些示例对应的是“陌生用户第一次来到仓库，如何在 3 分钟内完成第一次成功”。

## Advanced Payload Examples

如果你在做高级用法、Codex 工作流、或自定义 patch，再看这些：

- [initial-freeform-payload.json](initial-freeform-payload.json)
- [correction-payload.json](correction-payload.json)

最短低层流程：

```powershell
python scripts/double_builder.py init --slug demo --display-name "演示分身"
python scripts/double_builder.py apply-turn --slug demo --payload-file examples/initial-freeform-payload.json
python scripts/double_builder.py render --slug demo
python scripts/double_builder.py apply-turn --slug demo --payload-file examples/correction-payload.json
python scripts/double_builder.py render --slug demo
```

## Notes

- 这些 payload 是低层接口示例，不是第一次使用者的主入口
- 最好的 payload 应该尽量小、尽量准
- 如果一句话还不能确定，就先放进 `unknowns`
- canonical truth 仍然是 `profile.yaml`，不是这些 JSON 示例本身
