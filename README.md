# create-double-skill / 分身.skill

![create-double-skill social preview](assets/social-preview.svg)

Build a private digital double that captures how you judge, not just how you sound.

本地运行。文件可读。改错会写回去。

它不替你保存整个人生资料，也不假装记得你没说过的事。  
它做的事更窄：把你做判断、设边界、给建议的方式，整理成一份能继续修改的档案。

## 三分钟跑通第一次

先安装依赖：

```powershell
python -m pip install -r requirements.txt
```

然后直接开始：

```powershell
python scripts/double_builder.py start --slug my-work-double --display-name "工作分身" --use-case work
```

运行后会发生什么：

- 程序会问你 3 个问题
- 回答完就生成 `profile.yaml`、`profile.md`、`SKILL.md`
- 你可以立刻补一句 correction
- 如果还想继续挖细节，再选 `standard` 或 `deep`

如果你想先检查环境，再开始第一次运行：

```powershell
python scripts/double_builder.py doctor
```

如果你在 Windows PowerShell 里看到中文预览乱码，先运行 `chcp 65001`，或者直接打开生成的 `profile.md`。

## 先看结果

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

### 生成后的 `profile.md` 片段

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

这套流程的重点不是“让它学你怎么说话”，而是先抓住：

- 你先保护什么
- 你先问什么
- 你怎么立边界

## 先选哪一种分身

### 工作协作版

```powershell
python scripts/double_builder.py start --slug my-work-double --display-name "工作分身" --use-case work
```

适合拿来整理：

- 你在协作里怎么判断
- 你在 review、风险取舍、对齐预期时怎么说话

### 自我对话版

```powershell
python scripts/double_builder.py start --slug my-dialogue-double --display-name "自我对话分身" --use-case self-dialogue
```

适合拿来整理：

- 你卡住、焦虑、内耗时会怎么跟自己说话
- 什么能把你拉回清醒，什么只是在糊弄自己

### 对外表达版

```powershell
python scripts/double_builder.py start --slug my-external-double --display-name "对外表达分身" --use-case external
```

适合拿来整理：

- 你面向别人表达时的分寸感
- 你对外说话时的边界和节奏

### 想问得更深一点

```powershell
python scripts/double_builder.py start --slug my-double --display-name "我的分身" --use-case general --depth deep
```

- `quick`
  先问 3 个问题，尽快拿到第一版
- `standard`
  再多问 2 个细化问题
- `deep`
  再多问 4 个问题，并补至少 1 个真实例子

## 生成后怎么改

第一次生成完，最值得马上做的事不是继续堆资料，而是先改一句不对的话。

```powershell
python scripts/double_builder.py correct --slug my-work-double
```

然后直接输入：

```text
我不会直接说“你应该”，我更常说“如果是我，我会先把风险讲清楚再决定”。
```

这条命令会：

- 记录这句修正
- 回写到 `profile.yaml`
- 重新生成 `profile.md` 和 `SKILL.md`
- 把已经补上的待追问问题从队列里拿掉

## 也支持自由描述

如果你不想逐题回答，也可以这样开始：

```powershell
python scripts/double_builder.py start --slug my-dialogue-double --display-name "自我对话分身" --use-case self-dialogue --mode freeform
```

你先写一段自述，系统先出第一版，再从对应的用途继续追问。

## 为什么值得信

- `Local-first`
  默认只写本地 `doubles/`
- `profile.yaml`
  它是唯一结构化主档案
- `Correction-friendly`
  你改过的话会写回去，不是一次性对话泡沫
- `No fabricated memories`
  不伪造经历、关系、时间线和具体记忆
- `Auditable outputs`
  你能直接看 `profile.md`、`SKILL.md` 和 `history/`
- `资料不足会直说`
  资料不够时，会明确说这是推断

## 示例

第一次使用者建议先看：

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

## 为什么建议分开建多个分身

这个项目不再假设“所有人第一次都该被问同样 3 个问题”。

你在工作里、和自己对话时、以及对外表达时，未必是同一种判断方式。  
所以当前更推荐你分开建多个 slug，而不是把多个侧面硬塞进同一个 profile。

例如：

- `my-work-double`
- `my-dialogue-double`
- `my-external-double`

## 给 Codex 和其他 AI 编程助手

这个仓库不强依赖 Codex 才能运行。  
但它的结构很适合交给 Codex 这类 AI 编程助手继续安装、校验和修改。

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

第一次跑通不需要。  
`start` 和 `correct` 都是自然语言入口。  
只有在你想走低层工作流或自定义 patch 时，才需要碰 payload。

### 它会上传我的数据吗

默认不会。当前版本是本地优先，产物默认只留在 `doubles/`。

### 不用 Codex 能跑吗

能。这个仓库本身就是一套本地脚本和文档。

### 如果输出不对，我怎么改

直接用：

```powershell
python scripts/double_builder.py correct --slug my-double
```

### `profile.yaml` 和 `SKILL.md` 有什么关系

`profile.yaml` 是结构化主档案。  
`profile.md` 是给人看的摘要。  
`SKILL.md` 是给运行时 double 用的约束和材料。

## 检查仓库

```powershell
python scripts/validate_repo.py
python -m unittest tests/test_double_builder.py -v
```

## 更多文档

- [SKILL.md](SKILL.md)
- [prompts/interview.md](prompts/interview.md)
- [docs/github-publication-kit.md](docs/github-publication-kit.md)
- [docs/benchmark-review.md](docs/benchmark-review.md)

## License

[MIT](LICENSE)
