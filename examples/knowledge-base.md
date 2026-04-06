# private knowledge base

从这版开始，`create-double-skill` 不只会生成：

- `profile.yaml`
- `profile.md`
- `SKILL.md`

它还会在本地私有目录里积累一层更适合长期维护的知识页。

## 1. 每个分身自己的知识库

当你运行：

```powershell
python scripts/double_builder.py start --slug my-work-double --display-name "工作分身" --use-case work
```

或者：

```powershell
python scripts/double_builder.py correct --slug my-work-double
```

除了回写 `profile.yaml`，还会自动维护：

```text
doubles/my-work-double/kb/
├─ raw/
│  └─ events/
│     ├─ 20260406-161900__start.md
│     └─ 20260406-162100__correction.md
├─ wiki/
│  ├─ overview.md
│  ├─ values-and-priorities.md
│  ├─ decision-patterns.md
│  ├─ boundaries.md
│  ├─ voice-and-phrasing.md
│  ├─ anchor-examples.md
│  └─ open-questions.md
├─ index.md
├─ log.md
└─ SCHEMA.md
```

这一层的作用是：

- 记录高信号知识事件，而不是完整聊天流水
- 把长期稳定的偏好、边界和例子整理成可继续维护的 wiki
- 给后续回写 `profile.yaml` 提供背景和证据

它不做的事：

- 不替代 `profile.yaml`
- 不默认保存整段原始对话
- 不自动抓取聊天记录、照片、社媒等高隐私材料

## 2. 仓库自己的私有知识库

你也可以手动初始化这个仓库本身的私有维护知识库：

```powershell
python scripts/knowledge_base.py init --target project
```

它会在本地创建：

```text
.project-kb/
├─ raw/
├─ wiki/
├─ index.md
├─ log.md
└─ SCHEMA.md
```

这套知识库适合放：

- benchmark 观察
- 发布审计结论
- 对 README / examples / public surface 的维护结论
- 维护者自己的历史材料

默认它被 `.gitignore` 忽略，不会进入公开仓库。

## 3. 常用命令

初始化项目知识库：

```powershell
python scripts/knowledge_base.py init --target project
```

查看项目知识库摘要：

```powershell
python scripts/knowledge_base.py show --target project
```

检查项目知识库结构：

```powershell
python scripts/knowledge_base.py lint --target project
```

把一份本地资料导入项目知识库：

```powershell
python scripts/knowledge_base.py ingest --target project --source-file .private-docs/benchmark-review.md --kind maintainer-history
```

查看某个分身的知识库摘要：

```powershell
python scripts/knowledge_base.py show --target double --slug my-work-double
```

检查某个分身的知识库：

```powershell
python scripts/knowledge_base.py lint --target double --slug my-work-double
```

## 4. 现在的边界

- 第一阶段重点是“自动积累 + 受控编译”
- `profile.yaml` 仍是唯一运行时真源
- `kb/` 是长期知识层，不是第二套并行配置
- 如果知识还不稳定，就留在 `kb/wiki` 或 `unknowns`，不会强行污染 `profile.yaml`
