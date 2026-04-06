# create-double-skill examples

如果你是第一次来到这个仓库，先不要从 payload 开始。

推荐顺序：
1. 先看 [start-transcript-work.md](start-transcript-work.md)
2. 再看 [generated-artifacts.md](generated-artifacts.md)
3. 再看 [correction-before-after.md](correction-before-after.md)
4. 最后才看低层 payload 示例

## First-Run Main Examples

- [start-transcript-work.md](start-transcript-work.md)
  默认主路径，最适合第一次跑通
- [generated-artifacts.md](generated-artifacts.md)
  生成后的 `profile.md` / `SKILL.md` 片段
- [correction-before-after.md](correction-before-after.md)
  一句 correction 如何回写并改变后续追问

如果第一次只是想确认环境，先跑：

```powershell
python scripts/double_builder.py doctor
python scripts/double_builder.py start --demo --use-case work
```

## More Examples

- [start-transcript.md](start-transcript.md)
  总入口说明
- [start-transcript-general.md](start-transcript-general.md)
  通用分身
- [start-transcript-self-dialogue.md](start-transcript-self-dialogue.md)
  自我对话版
- [start-transcript-external.md](start-transcript-external.md)
  对外表达版
- [knowledge-base.md](knowledge-base.md)
  `start` / `correct` 之后，本地会额外积累哪些私有知识页

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
- `quick / standard / deep` 是为了平衡第一次跑通和继续细化，不是为了把访谈无限拉长
- 如果一句话还不能高置信度落槽，就先放进 `unknowns`
- `profile.yaml` 是唯一结构化主档案，不是这些 JSON 示例本身
- `doubles/<slug>/kb/` 是长期积累层；`profile.yaml` 仍是运行时真源
