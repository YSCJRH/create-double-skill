# create-double-skill

![create-double-skill social preview](assets/social-preview.svg)

一个通过引导式提问、自由自述和显式修正来构建私人数字分身的本地优先项目。

分身.skill 不追求“把你的一切都存下来”，而是优先捕捉真正会改变表达和判断的高信号信息：价值观、取舍偏好、语气、边界感，以及反复出现的决策模式。

> 不是人生流水账，不是记忆模拟器，而是一种用来捕捉你如何表达、如何判断、如何设边界的本地优先方式。

## 为什么做这个项目

很多“数字分身”项目的默认方向，是尽可能多地收集资料。  
`create-double-skill` 走的是另一条路：

- 更少但更关键：优先沉淀高信号信息，而不是堆 biography
- 更私有：所有生成结果都留在本地 `doubles/` 下
- 更诚实：明确区分用户直接陈述与模型推断，不伪造经历和记忆

## 它和常见数字分身项目有什么不同

- `Local-first`：不依赖外部 API 或云服务就能工作
- `High-signal`：重点建模 voice、values、decision model，而不是人生资料仓库
- `Correction-friendly`：用户可以随时用“我不会这么说”“我更在意 X”这类输入把分身拉回真实自己
- `Uncertainty-aware`：资料不足时，分身必须承认不知道，而不是补编

## 你会得到什么

- 混合采集模式：访谈式提问和自由描述可随时切换
- 固定的 `profile.yaml` 结构，便于后续迁移或扩展
- 自动渲染 `profile.md` 和运行时分身 `SKILL.md`
- 修正闭环：像“我不会这么说”“我更在意 X”这类输入可以直接回写
- 历史快照：每次重渲染前保存上一版结果到 `history/`
- 本地校验与单测

## 公开版快速路径

- 只想先跑通一次：安装依赖后，按 `init -> apply-turn -> render` 走一遍最短流程
- 只想先看输入格式：先看 [examples/initial-freeform-payload.json](examples/initial-freeform-payload.json) 和 [examples/correction-payload.json](examples/correction-payload.json)
- 只想先看仓库是否靠谱：先运行 `python scripts/validate_repo.py` 和 `python -m unittest tests/test_double_builder.py -v`
- 想把安装交给 AI 编程助手：直接使用下方的安装提示词，把整个仓库交给 Codex 或其他助手处理

## 为什么可信

- 本地优先：当前版本不依赖外部 API 或云服务，生成结果默认只落在本地 `doubles/`
- 事实和推断分层：用户明确说过的内容与模型补出的暂定判断不会混为一谈
- 修正优先：你可以持续说“我不会这么说”“我更在意 X”，系统会把这些修正回写到结构化档案
- 可审计：核心产物是 `profile.yaml`、`profile.md` 和运行时 `SKILL.md`，不是不可见黑箱
- 可复查：仓库自带校验脚本、单元测试和 CI，方便在公开前持续检查稳定性

## 一分钟上手

### 1. 安装依赖

```powershell
python -m pip install -r requirements.txt
```

### 2. 初始化一个分身

```powershell
python scripts/double_builder.py init --slug my-double --display-name "我的分身"
```

### 3. 路由一条原始输入

```powershell
python scripts/double_builder.py route --current-mode interview --text "我做重要决定时通常先看长期影响。"
```

### 4. 应用一个结构化 payload

可以直接使用 [examples/initial-freeform-payload.json](examples/initial-freeform-payload.json) 作为起点：

```powershell
python scripts/double_builder.py apply-turn --slug my-double --payload-file examples/initial-freeform-payload.json
```

### 5. 生成当前版本

```powershell
python scripts/double_builder.py render --slug my-double
```

生成结果会出现在：

- `doubles/my-double/profile.yaml`
- `doubles/my-double/profile.md`
- `doubles/my-double/SKILL.md`

## 典型使用场景

- 想把自己的表达风格和判断方式沉淀成一个可迭代的本地分身
- 想在做决定时，得到“更像自己会怎么想”的第二视角
- 想先用访谈和自由描述做一个轻量但可信的数字分身，而不是直接做全量人生资料库
- 想持续修正一个分身，而不是一次性生成后就无法再改

## 第一次对话示例

下面是一种很典型的起步方式：

```text
用户：我想做一个更像“会怎么判断事情的我”，而不只是会模仿语气的分身。

create-double：继续提问。你做重要决定时，通常最先保护什么？

用户：我通常先保护长期可持续，其次是关系里的稳定感。

create-double：收到。这说明你不是单纯追求短期效率的人。那如果必须在“快速推进”和“减少后患”之间选一个，你通常更偏哪边？

用户：我更偏减少后患。慢一点可以接受，但我不想让错误预期扩散。
```

这种对话会逐步沉淀进 `values.priorities`、`decision_model.tradeoff_biases` 和 `anchor_examples`，最后渲染成一个更像“你会怎么判断”的分身，而不只是一个会模仿措辞的角色。

## 让 Codex 或其他 AI 编程助手帮你安装

如果你不想手动逐步配置环境，可以把整个仓库目录直接交给 Codex 或其他 AI 编程助手处理。  
最省心的方式，是让它代你完成依赖安装、仓库校验和首次运行检查。

推荐直接把下面这段提示词发给助手：

```text
请帮我安装并验证 create-double-skill：

1. 安装 requirements.txt 里的依赖
2. 运行 python scripts/validate_repo.py
3. 运行 python -m unittest tests/test_double_builder.py -v
4. 如果检查都通过，告诉我下一步如何初始化第一个分身
5. 如果有报错，请直接修复，或者明确告诉我卡在哪里
```

如果你使用的是 Codex，这种方式通常会更顺手，因为这个项目本身就是围绕以下工作方式设计的：

- 逐轮对话式采集与修正
- 基于 `SKILL.md`、`prompts/`、`references/` 的 skill 调用习惯
- 把自由描述整理为结构化 patch，再持续回写 `profile.yaml`

换句话说，它不是只能在 Codex 里工作，但在 Codex 中使用时，通常更接近这个项目最初的设计场景，也更容易把采集、修正、渲染和后续迭代串起来。

## 基于 Codex 构建

这个项目是在 Codex 协作式工作流里构建出来的：skill 结构、builder 脚本、示例 payload、README、验证脚本和 CI 都是在本地迭代完成的。  
仓库本身不强依赖 Codex 才能运行，但它的组织方式天然贴近 Codex 这类 AI 编程助手的工作流，所以在这类环境里通常能获得更顺滑的使用体验。

## 常见问题

### 需要 Codex 才能用吗

不需要。`create-double-skill` 本质上是一个本地仓库和一套脚本，不依赖 Codex 才能运行。  
只是它的结构天然适合放进 Codex、Claude Code 或其他 AI 编程助手里协作使用，所以在这类环境中通常更省心。

### 一开始必须准备很多资料吗

不需要。第一版支持从很少的信息起步。你可以只回答几个问题，也可以先写一段自由自述，再逐轮补全。

### 可以只写自述，不走访谈吗

可以。自由描述和访谈模式不是硬切开的，随时可以在同一轮里切换。

### 它会补编我没说过的经历吗

不会。当前项目明确不把“伪造记忆”当能力，资料不足时应该承认这是推断，而不是假装知道。

## 项目命名

- GitHub 仓库名：`create-double-skill`
- 内部 skill 名：`create-double`
- 对外中文名：`分身.skill`

## 仓库结构

```text
create-double-skill/
├─ README.md
├─ SKILL.md
├─ agents/openai.yaml
├─ assets/
│  ├─ profile-seed.yaml
│  └─ social-preview.svg
├─ docs/
│  ├─ benchmark-review.md
│  ├─ launch-copy.md
│  └─ pre-release-checklist.md
├─ prompts/
├─ references/
├─ scripts/
│  ├─ double_builder.py
│  └─ validate_repo.py
├─ tests/
├─ examples/
└─ doubles/
```

## 核心工作流

### 1. 采集

使用 `route` 对每一轮输入做分类：

- `answer`
- `freeform`
- `correction`
- `switch_mode`
- `finish`

### 2. 结构化

参考：

- [references/profile-schema.md](references/profile-schema.md)
- [references/payloads.md](references/payloads.md)

把最新输入整理成一个最小、可信的 JSON patch。

### 3. 合并

使用 `apply-turn` 把 patch 合并进 `profile.yaml`，并同步更新 `session.yaml`。

### 4. 渲染

使用 `render` 生成给人看的 `profile.md` 和给模型用的运行时 `SKILL.md`。

## 示例与展示文案

- [examples/initial-freeform-payload.json](examples/initial-freeform-payload.json)
- [examples/correction-payload.json](examples/correction-payload.json)
- [examples/README.md](examples/README.md)
- [docs/launch-copy.md](docs/launch-copy.md)
- [assets/social-preview.svg](assets/social-preview.svg)

## 发布与对标参考

- [docs/pre-release-checklist.md](docs/pre-release-checklist.md)
- [docs/benchmark-review.md](docs/benchmark-review.md)
- [docs/release-v0.1.0.md](docs/release-v0.1.0.md)
- [docs/launch-copy.md](docs/launch-copy.md)

## 校验

运行仓库自检：

```powershell
python scripts/validate_repo.py
```

运行单测：

```powershell
python -m unittest tests/test_double_builder.py -v
```

GitHub Actions 也会自动运行相同检查。

## 开源许可证

本项目采用 [MIT License](LICENSE)。

## 隐私与边界

- 当前版本不做聊天记录、社媒、照片等自动导入
- 当前版本不依赖外部 API 或云服务
- 当前版本不会主动补编经历、关系、时间线或记忆
- 当资料不足时，运行时分身必须显式说明这是推断

## 适合谁

- 想把自己的表达风格和判断方式做成一个长期可迭代的本地分身
- 想做“人格 + 决策模型”而不是“人生资料大仓库”
- 想先做一个可控、可编辑、可审计的 v1

## 当前暂不覆盖

- 自动抓取多平台历史数据
- 多人协作维护同一个分身
- 云同步
- 图形界面
- 复杂回滚 UI

## 路线图

- 更细的访谈策略和问题优先级系统
- 更自然的自由描述抽取与修正合并
- 更完整的运行时分身评测
- 可选的图形界面和 social preview 视觉资源
