# create-double-skill / 分身.skill

![create-double-skill social preview](assets/social-preview.svg)

Build a private digital double that captures how you judge, not just how you sound.

一个 `local-first`、`editable`、`auditable`、`correction-friendly` 的 self-model starter workflow。

> Not a life-log. Not a memory simulator. A local-first workflow for building and correcting a self-model.
>
> 不是“上传你的一生”。不是记忆模拟器。不是伪造一个会替你回忆过去的角色。  
> 它更像一个可持续修正的工程起点，用来捕捉你如何判断、如何设边界、如何给建议。

## 3-Minute First Success

先安装依赖：

```powershell
python -m pip install -r requirements.txt
```

然后直接开始：

```powershell
python scripts/double_builder.py start --slug my-work-double --display-name "工作分身" --use-case work
```

现在 `start` 不再只有固定 3 问。  
它会先问你**要哪一种分身**，再按用途和深度决定问题：

- `general`
  通用分身，先抓你的判断方式、给建议方式和边界感
- `work`
  工作协作版，先抓你的协作偏好、风险取舍和工作边界
- `self-dialogue`
  自我对话版，先抓你怎么把自己从混乱里拉回来
- `external`
  对外表达版，先抓你对外表达时的分寸感和边界
- `custom`
  先说你最想让这个分身帮你做什么，再映射到最接近的轨道

默认深度是 `quick`，先让你在几分钟内拿到第一个 artifact。  
如果你愿意，还可以继续走 `standard` 或 `deep`，让系统多问 2-4 个细化问题。

3 分钟内你会得到：

- `doubles/<slug>/profile.yaml`
- `doubles/<slug>/profile.md`
- `doubles/<slug>/SKILL.md`
- 一次自然发生的 correction 机会

如果你想先检查环境，再开始第一次运行：

```powershell
python scripts/double_builder.py doctor
```

如果你在 Windows PowerShell 里看到中文预览乱码，先运行 `chcp 65001`，或者直接打开生成的 `profile.md`。

## Choose Your Double

### 工作协作版

```powershell
python scripts/double_builder.py start --slug my-work-double --display-name "工作分身" --use-case work
```

适合你想做一个：

- 更像你在协作里怎么判断的分身
- 更像你在 review / 风险取舍 / 对齐预期时怎么说话的分身

### 自我对话版

```powershell
python scripts/double_builder.py start --slug my-dialogue-double --display-name "自我对话分身" --use-case self-dialogue
```

适合你想做一个：

- 在你卡住、焦虑、内耗时更像你会怎么跟自己说话的分身
- 更知道什么能把你拉回清醒、什么只是在糊弄自己的分身

### 对外表达版

```powershell
python scripts/double_builder.py start --slug my-external-double --display-name "对外表达分身" --use-case external
```

适合你想做一个：

- 更像你面向别人表达时的分寸感、边界感和节奏感的分身

### 深度控制

```powershell
python scripts/double_builder.py start --slug my-double --display-name "我的分身" --use-case general --depth deep
```

- `quick`
  3 个 base questions，先拿到 first artifact，再决定要不要继续
- `standard`
  3 个 base questions + 2 个 follow-ups
- `deep`
  3 个 base questions + 4 个 follow-ups，并补至少 1 个真实例子

## What You Get

- 一个更关注“你会怎么判断”的 double，而不是只模仿说话语气
- 一个可编辑的 `profile.yaml`，作为 canonical structured source of truth
- 一个用途感知的 first-run 流程，而不是所有人都问同样 3 个问题
- 一个可回写修正的流程：`我不会这么说`、`我更在意 X`、`这种情况下我会先问 Y`
- 一个 uncertainty-aware 的 runtime `SKILL.md`，资料不足时会明确承认未知
- 一个完全本地的工作流，默认不依赖外部 API 或高隐私自动抓取

## Quick Preview

### 工作协作版交互

```text
$ python scripts/double_builder.py start --slug my-work-double --display-name "工作分身" --use-case work
3 分钟内生成你的第一个 double，不需要写 JSON。

1/3 在工作里你最先保护什么？是质量、速度、关系、可维护性，还是别的？
> 可维护性、长期可持续、错误预期不要扩散

2/3 接到一个模糊任务时，你通常第一步会先问什么？
> 我会先问目标、成功标准和最不能出错的地方

3/3 同事或项目节奏让你不舒服时，你会怎么立边界或校正预期？
> 我会先把风险讲清楚，再给出我能接受的最小范围
```

### 产物大概长这样

```md
## Snapshot
- primary use case: `work`
- interview depth: `quick`

## Priorities
Confirmed:
- 可维护性
- 长期可持续
- 错误预期不要扩散

## Default Questions
Confirmed:
- 我会先问目标、成功标准和最不能出错的地方
```

更多真实示例在：

- [examples/start-transcript-general.md](examples/start-transcript-general.md)
- [examples/start-transcript-work.md](examples/start-transcript-work.md)
- [examples/start-transcript-self-dialogue.md](examples/start-transcript-self-dialogue.md)
- [examples/start-transcript-external.md](examples/start-transcript-external.md)
- [examples/generated-artifacts.md](examples/generated-artifacts.md)
- [examples/correction-before-after.md](examples/correction-before-after.md)

## One-Line Correction

第一次成功之后，最重要的不是“继续堆资料”，而是先做一次 correction。

```powershell
python scripts/double_builder.py correct --slug my-work-double
```

然后直接输入一句自然语言：

```text
我不会直接说“你应该”，我更常说“如果是我，我会先把风险讲清楚再决定”。
```

这个命令会：

- 记录 correction
- 回写到 `profile.yaml`
- 重新渲染 `profile.md` 和 `SKILL.md`
- 从当前 track 的待追问队列里移除已经被纠正覆盖的问题

## Freeform Still Works

如果你不想逐题回答，仍然可以：

```powershell
python scripts/double_builder.py start --slug my-dialogue-double --display-name "自我对话分身" --use-case self-dialogue --mode freeform
```

这时你先写一段自由自述，系统会先生成第一版，再把后续追问切到对应 track，而不是退回通用问题。

## Why It Feels Like “How I Judge”

这个项目刻意把问题设计成用途感知的：

- 工作版先问协作、风险和预期管理
- 自我对话版先问如何把自己拉回清醒
- 对外版先问如何对外表达和如何设边界

所以第一版 double 更容易抓到的是：

- 你的取舍顺序
- 你的默认提问方式
- 你的边界感
- 你的具体使用场景

而不是只做一个会模仿你语气的角色。

## Why Trust It

- `Local-first`
  所有产物默认只写到本地 `doubles/`
- `Canonical truth`
  `profile.yaml` 是唯一结构化真源
- `Correction-friendly`
  correction 会被回写，不是临时对话泡沫
- `Uncertainty-aware`
  用户直接陈述和模型推断分层保存
- `No fabricated memories`
  不伪造经历、关系、时间线和具体记忆
- `Auditable outputs`
  你始终能看到 `profile.md`、`SKILL.md` 和 `history/`

## CLI Surface

面向第一次使用者的命令：

- `start`
  先选用途，再按 `quick / standard / deep` 访谈、渲染和预览
- `correct`
  用一句自然语言修正现有 double
- `doctor`
  检查依赖、仓库完整性、写权限和终端编码提示

保留给高级用户 / Codex / 自定义管线的命令：

- `init`
- `route`
- `apply-turn`
- `render`
- `next-question`
- `show`
- `snapshot`

查看帮助：

```powershell
python scripts/double_builder.py --help
```

## Examples

第一次使用者优先看：

- [examples/start-transcript-general.md](examples/start-transcript-general.md)
- [examples/start-transcript-work.md](examples/start-transcript-work.md)
- [examples/start-transcript-self-dialogue.md](examples/start-transcript-self-dialogue.md)
- [examples/start-transcript-external.md](examples/start-transcript-external.md)
- [examples/generated-artifacts.md](examples/generated-artifacts.md)
- [examples/correction-before-after.md](examples/correction-before-after.md)

如果你想继续用低层命令或自己写 payload，再看：

- [examples/README.md](examples/README.md)
- [references/profile-schema.md](references/profile-schema.md)
- [references/payloads.md](references/payloads.md)

## Story

这个项目的一部分访谈设计灵感，来自一个反复出现的科幻问题：

如果“你”不是单一、稳定、完整的一块东西，而是由多个彼此拉扯的自我版本组成，那么数字分身到底应该复制哪一个？

`create-double-skill` 给出的回答不是“找出唯一真实答案”，而是先把不同版本的你变成可编辑的结构。

现在，它还多了一层更实际的回答：

你并不总是在同一种场景里需要“自己”。

- 有时你需要一个更像你在工作里怎么判断的分身
- 有时你需要一个更像你和自己对话时怎么拉自己一把的分身
- 有时你需要一个更像你对外表达时如何拿捏分寸的分身

所以这个项目不再假设“所有人第一次都该被问同样 3 个问题”，而是允许你先定义这次最想构建的是哪一种自己。

## For Codex And Other AI Coding Assistants

这个仓库不强依赖 Codex 才能运行。  
但它的组织方式天然贴近 Codex 这类 AI 编程助手的工作流，所以在这类环境里通常更顺手。

如果你想把安装和首跑交给 AI 助手，可以直接把下面这段发给它：

```text
请帮我安装并验证 create-double-skill：

1. 安装 requirements.txt 里的依赖
2. 运行 python scripts/validate_repo.py
3. 运行 python -m unittest tests/test_double_builder.py -v
4. 如果检查都通过，直接帮我用 start 命令走通一次 work 或 self-dialogue 的第一次生成
5. 如果有报错，请直接修复，或者明确告诉我卡在哪里
```

## FAQ

### 我还需要写 JSON 吗

第一次成功不需要。  
`start` 和 `correct` 都是自然语言入口。  
只有在你想走低层工作流或自定义 patch 时，才需要碰 payload。

### 如果我想做多个用途的分身怎么办

当前推荐做多个 slug，而不是把多个侧面硬塞进同一个 profile。

例如：

- `my-work-double`
- `my-dialogue-double`
- `my-external-double`

### 它会上传我的数据吗

默认不会。当前版本是 local-first，产物默认只留在本地 `doubles/`。

### 不用 Codex 能跑吗

能。这个仓库本身就是一套本地脚本和文档，不依赖 Codex 才能运行。

### 如果输出不对，我怎么改

直接用：

```powershell
python scripts/double_builder.py correct --slug my-double
```

### `profile.yaml` 和 `SKILL.md` 有什么关系

`profile.yaml` 是 canonical structured source of truth。  
`profile.md` 是给人看的摘要。  
`SKILL.md` 是给运行时 double 用的约束和材料。

## Validate The Repo

```powershell
python scripts/validate_repo.py
python -m unittest tests/test_double_builder.py -v
```

## More Project Docs

- [SKILL.md](SKILL.md)
- [prompts/interview.md](prompts/interview.md)
- [docs/github-publication-kit.md](docs/github-publication-kit.md)
- [docs/benchmark-review.md](docs/benchmark-review.md)

## License

[MIT](LICENSE)
