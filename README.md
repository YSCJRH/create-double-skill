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
python scripts/double_builder.py start --slug my-double --display-name "我的分身"
```

你不需要手写 JSON。  
你不需要先理解 schema、patch、payload。  
你只需要回答 3 个高信号问题：

- 你做重要决定时，通常先保护什么
- 别人来找你要建议时，你通常会先问什么，或先看什么
- 你不舒服时会怎么设边界

3 分钟内你会得到：

- `doubles/my-double/profile.yaml`
- `doubles/my-double/profile.md`
- `doubles/my-double/SKILL.md`
- 一次自然发生的 correction 机会

如果你想先检查环境，再开始第一次运行：

```powershell
python scripts/double_builder.py doctor
```

如果你在 Windows PowerShell 里看到中文预览乱码，先运行 `chcp 65001`，或者直接打开生成的 `profile.md`。

## What You Get

- 一个更关注“你会怎么判断”的 double，而不是只模仿说话语气
- 一个可编辑的 `profile.yaml`，作为 canonical structured source of truth
- 一个可回写修正的流程：`我不会这么说`、`我更在意 X`、`这种情况下我会先问 Y`
- 一个 uncertainty-aware 的 runtime `SKILL.md`，资料不足时会明确承认未知
- 一个完全本地的工作流，默认不依赖外部 API 或高隐私自动抓取

## Quick Preview

### 交互长这样

```text
$ python scripts/double_builder.py start --slug my-double --display-name "我的分身"
3 分钟内生成你的第一个 double，不需要写 JSON。

1/3 你做重要决定时，通常先保护什么？
> 长期可持续、关系里的稳定感

2/3 别人来找你要建议时，你通常会先问什么，或先看什么？
> 我会先问这件事三个月后还重要吗

3/3 你不舒服时会怎么设边界？
> 我会把底线讲清楚，但尽量不把气氛推到最糟

已生成：
- doubles/my-double/profile.md
- doubles/my-double/SKILL.md

当前 preview：
- 优先保护：长期可持续；关系里的稳定感
- 给建议前先问：我会先问这件事三个月后还重要吗
- 设边界方式：我会把底线讲清楚，但尽量不把气氛推到最糟

如果有一句不对，直接输入“我不会这么说...”或“我更在意...”，回车跳过：
> 我更在意边界清晰
```

### 产物大概长这样

`profile.md` 会更强调你如何判断，而不是只记录你会怎么说话：

```md
## Priorities
Confirmed:
- 长期可持续
- 关系里的稳定感
- 边界清晰

## Default Questions
Confirmed:
- 我会先问这件事三个月后还重要吗

## Boundary Style
Confirmed:
- 我会把底线讲清楚，但尽量不把气氛推到最糟
```

更多真实示例在：

- [examples/start-transcript.md](examples/start-transcript.md)
- [examples/generated-artifacts.md](examples/generated-artifacts.md)
- [examples/correction-before-after.md](examples/correction-before-after.md)

## One-Line Correction

第一次成功之后，最重要的不是“继续堆资料”，而是先做一次 correction。

```powershell
python scripts/double_builder.py correct --slug my-double
```

然后直接输入一句自然语言：

```text
我不会直接说“你应该”，我更常说“如果是我，我会先把边界讲清楚”。
```

这个命令会：

- 记录 correction
- 回写到 `profile.yaml`
- 重新渲染 `profile.md` 和 `SKILL.md`

## Choose Your Path

- 我只想先生成第一个 double
  先看本页的 `3-Minute First Success`
- 我想理解 prompts / schema / rendering
  看 [references/profile-schema.md](references/profile-schema.md)、[references/payloads.md](references/payloads.md)、[prompts/](prompts)
- 我想把它接入 Codex / skill workflow / 自定义管线
  看 [SKILL.md](SKILL.md) 和 [agents/openai.yaml](agents/openai.yaml)

## Why It Feels Like “How I Judge”

这个项目刻意把 first run 的问题放在判断、建议、边界上，而不是 biography 上。

- 它先问你做重要决定时保护什么
- 再问你别人来找你要建议时先看什么
- 再问你不舒服时怎么设边界

这意味着第一版 double 更容易抓到的是：

- 你的取舍顺序
- 你的默认提问方式
- 你的边界感

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
  初始化、提问、写入、渲染、预览、一次 correction
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

- [examples/start-transcript.md](examples/start-transcript.md)
- [examples/generated-artifacts.md](examples/generated-artifacts.md)
- [examples/correction-before-after.md](examples/correction-before-after.md)

如果你想继续用低层命令或自己写 payload，再看：

- [examples/README.md](examples/README.md)
- [examples/initial-freeform-payload.json](examples/initial-freeform-payload.json)
- [examples/correction-payload.json](examples/correction-payload.json)

## Story

这个项目的一部分访谈设计灵感，来自一个反复出现的科幻问题：

如果“你”不是单一、稳定、完整的一块东西，而是由多个彼此拉扯的自我版本组成，那么数字分身到底应该复制哪一个？

`create-double-skill` 给出的回答不是“找出唯一真实答案”，而是先把不同版本的你变成可编辑的结构：

- 你表现出来的自己：平时如何说话、如何判断、如何与人相处
- 你理想中的自己：你认同什么原则，你希望自己成为什么样的人
- 你更底层的自己：你在压力、欲望、恐惧和逃避里会如何反应

这里借用了“表现自我 / 理想自我 / 更底层的自我”这样的理解框架。  
如果你愿意，也可以把它类比成“社会化的我、超我的我、本我的我”。  
但这个项目不是在替你做心理诊断，而是在给你一个可修正、可比较、可继续追问“我是谁”的工程化起点。

## For Codex And Other AI Coding Assistants

这个仓库不强依赖 Codex 才能运行。  
但它的组织方式天然贴近 Codex 这类 AI 编程助手的工作流，所以在这类环境里通常更顺手。

如果你想把安装和首跑交给 AI 助手，可以直接把下面这段发给它：

```text
请帮我安装并验证 create-double-skill：

1. 安装 requirements.txt 里的依赖
2. 运行 python scripts/validate_repo.py
3. 运行 python -m unittest tests/test_double_builder.py -v
4. 如果检查都通过，直接帮我用 start 命令走通第一次生成
5. 如果有报错，请直接修复，或者明确告诉我卡在哪里
```

## FAQ

### 我需要写 JSON 吗

第一次成功不需要。  
`start` 和 `correct` 都是自然语言入口。  
只有在你想走低层工作流或自定义 patch 时，才需要碰 payload。

### 它会上传我的数据吗

默认不会。当前版本是 local-first，产物默认只留在本地 `doubles/`。

### 它是在模仿我说话，还是在建模我怎么判断

两者都会碰到，但第一优先级是后者。  
P0 的 first run 故意先问取舍、建议和边界，而不是先问口头禅。

### 不用 Codex 能跑吗

能。这个仓库本身就是一套本地脚本和文档，不依赖 Codex 才能运行。

### 如果输出不对，我怎么改

直接用：

```powershell
python scripts/double_builder.py correct --slug my-double
```

或者继续走高级路径，用 `apply-turn` 合并你自己的 payload。

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

- [docs/github-publication-kit.md](docs/github-publication-kit.md)
- [docs/benchmark-review.md](docs/benchmark-review.md)
- [docs/pre-release-checklist.md](docs/pre-release-checklist.md)
- [docs/release-v0.1.0.md](docs/release-v0.1.0.md)

## License

[MIT](LICENSE)
