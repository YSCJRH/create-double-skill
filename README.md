# create-double-skill

分身.skill，一个本地私有、中文优先的数字分身构建器。  
It helps you build a private digital double from guided interviews and freeform self-description.

## 命名约定

- GitHub 仓库名：`create-double-skill`
- 内部 skill 调用名：`create-double`
- 对外中文名：`分身.skill`

## 项目目标

和很多“采集越多越好”的数字分身项目不同，`create-double-skill` 的第一版强调三件事：

- 只收集高信号信息：价值观、取舍偏好、表达风格、边界感、反复出现的决策模式
- 保持本地私有：所有产物只落在当前仓库的 `doubles/` 下
- 承认不确定性：明确区分用户直接陈述与模型推断，不伪造经历和记忆

## 当前能力

- 混合采集模式：访谈式提问和自由描述可随时切换
- 固定的 `profile.yaml` 结构，便于后续迁移或扩展
- 自动渲染 `profile.md` 和运行时分身 `SKILL.md`
- 修正闭环：像“我不会这么说”“我更在意 X”这类输入可以直接回写
- 历史快照：每次重渲染前保存上一版结果到 `history/`
- 本地校验与单测

## 仓库结构

```text
create-double-skill/
├─ README.md
├─ SKILL.md
├─ agents/openai.yaml
├─ assets/
│  └─ profile-seed.yaml
├─ prompts/
├─ references/
├─ scripts/
│  ├─ double_builder.py
│  └─ validate_repo.py
├─ tests/
├─ examples/
└─ doubles/
```

## 快速开始

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

可直接使用 [examples/initial-freeform-payload.json](examples/initial-freeform-payload.json) 作为参考：

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

## 核心工作流

### 1. 采集

使用 `route` 先判断用户当前输入属于哪一类：

- `answer`
- `freeform`
- `correction`
- `switch_mode`
- `finish`

### 2. 结构化

参考：

- [references/profile-schema.md](references/profile-schema.md)
- [references/payloads.md](references/payloads.md)

把当前输入整理成一个最小、可信的 JSON patch。

### 3. 合并

使用 `apply-turn` 把 patch 合并进 `profile.yaml`，并同步更新 `session.yaml`。

### 4. 渲染

使用 `render` 生成给人看的 `profile.md` 和给模型用的运行时 `SKILL.md`。

## 示例

- [examples/initial-freeform-payload.json](examples/initial-freeform-payload.json)
- [examples/correction-payload.json](examples/correction-payload.json)
- [examples/README.md](examples/README.md)

## 验证

运行仓库自检：

```powershell
python scripts/validate_repo.py
```

运行单测：

```powershell
python -m unittest tests/test_double_builder.py -v
```

GitHub Actions 也会自动运行相同检查。

## 隐私与边界

- 当前版本不做聊天记录、社媒、照片等自动导入
- 当前版本不依赖外部 API 或云服务
- 当前版本不会主动补编经历、关系、时间线或记忆
- 当资料不足时，运行时分身必须显式说明这是推断

## 适合谁

- 想把自己的表达风格和判断方式做成一个长期可迭代的本地分身
- 想做“人格 + 决策模型”而不是“人生资料大仓库”
- 想先做一个可控、可编辑、可审计的 v1

## 当前不做

- 自动抓取多平台历史数据
- 多人协作维护同一个分身
- 云同步
- 图形界面
- 复杂回滚 UI

## 发布前最后一步

这个仓库已经具备公开发布所需的说明、示例、测试和 CI。  
如果你准备正式公开发布，建议再补一个你愿意采用的开源许可证文件，因为许可证属于项目所有者需要亲自确认的法律选择。
