# create-double-skill

![create-double-skill social preview](assets/social-preview.svg)

Build a private digital double from guided interviews, freeform self-description, and explicit corrections.

分身.skill 是一个本地私有、中文优先的数字分身构建器。  
它不追求“把你的一切都存下来”，而是优先捕捉真正会改变表达和判断的高信号信息：价值观、取舍偏好、语气、边界感，以及反复出现的决策模式。

> Not a life-log. Not a memory simulator. A local-first way to capture how you speak, decide, and draw boundaries.

## Why this project exists

很多“数字分身”项目的默认方向，是尽可能多地收集资料。  
`create-double-skill` 走的是另一条路：

- 更少但更关键：优先沉淀高信号信息，而不是堆 biography
- 更私有：所有生成结果都留在本地 `doubles/` 下
- 更诚实：明确区分用户直接陈述与模型推断，不伪造经历和记忆

## What makes it different

- `Local-first`: 不依赖外部 API 或云服务就能工作
- `High-signal`: 重点建模 voice、values、decision model，而不是人生资料仓库
- `Correction-friendly`: 用户可以随时用“我不会这么说”“我更在意 X”这类输入把分身拉回真实自己
- `Uncertainty-aware`: 资料不足时，分身必须承认不知道，而不是补编

## What you get

- 混合采集模式：访谈式提问和自由描述可随时切换
- 固定的 `profile.yaml` 结构，便于后续迁移或扩展
- 自动渲染 `profile.md` 和运行时分身 `SKILL.md`
- 修正闭环：像“我不会这么说”“我更在意 X”这类输入可以直接回写
- 历史快照：每次重渲染前保存上一版结果到 `history/`
- 本地校验与单测

## One-minute walkthrough

### 1. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 2. Initialize a double

```powershell
python scripts/double_builder.py init --slug my-double --display-name "我的分身"
```

### 3. Route a raw user turn

```powershell
python scripts/double_builder.py route --current-mode interview --text "我做重要决定时通常先看长期影响。"
```

### 4. Apply a structured payload

Use [examples/initial-freeform-payload.json](examples/initial-freeform-payload.json) as a starting point:

```powershell
python scripts/double_builder.py apply-turn --slug my-double --payload-file examples/initial-freeform-payload.json
```

### 5. Render the current double

```powershell
python scripts/double_builder.py render --slug my-double
```

Generated outputs:

- `doubles/my-double/profile.yaml`
- `doubles/my-double/profile.md`
- `doubles/my-double/SKILL.md`

## Built with Codex

这个项目是在 Codex 协作式工作流里构建出来的：skill 结构、builder 脚本、示例 payload、README、验证脚本和 CI 都是在本地迭代完成的。  
虽然仓库本身不强依赖 Codex 才能运行，但如果你也在 Codex 里使用它，通常会更容易获得完整体验，因为这个项目天然围绕以下工作方式设计：

- 逐轮对话式采集与修正
- 基于 `SKILL.md`、`prompts/`、`references/` 的 skill 调用习惯
- 把自由描述整理为结构化 patch，再持续回写 `profile.yaml`

换句话说，它不是只能在 Codex 里工作，但在 Codex 里通常会更顺手，也更接近它最初被设计出来的使用场景。

## Project identity

- GitHub repository name: `create-double-skill`
- Internal skill name: `create-double`
- Chinese-facing name: `分身.skill`

## Repository structure

```text
create-double-skill/
├─ README.md
├─ SKILL.md
├─ agents/openai.yaml
├─ assets/
│  └─ profile-seed.yaml
├─ docs/
│  └─ launch-copy.md
├─ prompts/
├─ references/
├─ scripts/
│  ├─ double_builder.py
│  └─ validate_repo.py
├─ tests/
├─ examples/
└─ doubles/
```

## Core workflow

### 1. Collect

Use `route` to classify each incoming user turn:

- `answer`
- `freeform`
- `correction`
- `switch_mode`
- `finish`

### 2. Structure

Reference:

- [references/profile-schema.md](references/profile-schema.md)
- [references/payloads.md](references/payloads.md)

Turn the latest user input into a minimal, high-confidence JSON patch.

### 3. Merge

Use `apply-turn` to merge that patch into `profile.yaml` and update `session.yaml`.

### 4. Render

Use `render` to generate the human-readable `profile.md` and the runtime `SKILL.md`.

## Examples and launch copy

- [examples/initial-freeform-payload.json](examples/initial-freeform-payload.json)
- [examples/correction-payload.json](examples/correction-payload.json)
- [examples/README.md](examples/README.md)
- [docs/launch-copy.md](docs/launch-copy.md)
- [assets/social-preview.svg](assets/social-preview.svg)

## Validation

Run repository validation:

```powershell
python scripts/validate_repo.py
```

Run unit tests:

```powershell
python -m unittest tests/test_double_builder.py -v
```

GitHub Actions runs the same checks automatically.

## Privacy and boundaries

- 当前版本不做聊天记录、社媒、照片等自动导入
- 当前版本不依赖外部 API 或云服务
- 当前版本不会主动补编经历、关系、时间线或记忆
- 当资料不足时，运行时分身必须显式说明这是推断

## Who this is for

- 想把自己的表达风格和判断方式做成一个长期可迭代的本地分身
- 想做“人格 + 决策模型”而不是“人生资料大仓库”
- 想先做一个可控、可编辑、可审计的 v1

## Not in scope yet

- 自动抓取多平台历史数据
- 多人协作维护同一个分身
- 云同步
- 图形界面
- 复杂回滚 UI

## Roadmap

- 更细的访谈策略和问题优先级系统
- 更自然的自由描述抽取与修正合并
- 更完整的运行时分身评测
- 可选的图形界面和 social preview 视觉资源
