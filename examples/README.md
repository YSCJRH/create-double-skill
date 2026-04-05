# create-double-skill examples

如果你是第一次来到这个仓库，先不要从 payload 开始。

推荐顺序：
1. 先用 `python scripts/double_builder.py start --slug my-work-double --display-name "工作分身" --use-case work` 跑通第一次成功
2. 再看对应的 transcript，确认提问风格和用途差异
3. 再看 [generated-artifacts.md](generated-artifacts.md)，确认产物长什么样
4. 最后才看低层 payload 示例

## First-Run Examples

- [start-transcript.md](start-transcript.md)
  总入口说明，解释为什么现在要先选用途和深度
- [start-transcript-general.md](start-transcript-general.md)
  通用分身 first run
- [start-transcript-work.md](start-transcript-work.md)
  工作协作版 first run
- [start-transcript-self-dialogue.md](start-transcript-self-dialogue.md)
  自我对话版 first run
- [start-transcript-external.md](start-transcript-external.md)
  对外表达版 first run
- [generated-artifacts.md](generated-artifacts.md)
  生成后的 `profile.md` / `SKILL.md` 片段
- [correction-before-after.md](correction-before-after.md)
  一句 correction 如何回写并改变后续追问

这些示例对应的是“陌生用户第一次来到仓库，如何在几分钟内拿到第一个可信 artifact”。

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

- `start` 是第一次使用者的主入口；`payload` 是进阶入口
- `quick / standard / deep` 是为了平衡 first success 和深挖细节，不是为了把访谈无限拉长
- 如果一句话还不能高置信度落槽，就先放进 `unknowns`
- canonical truth 仍然是 `profile.yaml`，不是这些 JSON 示例本身
