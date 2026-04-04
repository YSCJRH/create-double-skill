# create-double-skill v0.1.0

首个公开版本草稿。

## 标题

`v0.1.0 - A local-first starting point for building a private digital double`

## 一句话介绍

`create-double-skill` 是一个本地优先、可修正、可审计的数字分身起点，用来逐步沉淀一个人的表达风格、价值观、决策方式，以及不同版本的自我模型。

## 首屏开场句

`Not a life-log. Not a memory simulator. A local-first way to build and revise different versions of yourself.`

## 发布说明

`create-double-skill` 的第一版聚焦一件事：  
不用自动抓取大量隐私素材，也能通过引导式提问、自由自述和显式修正，构建一个更像“你会怎么判断”的数字分身。

这不是人生资料库，不是记忆模拟器，也不承诺“人格复制”。  
它更像一个 `local-first` 的 starter repo：用结构化档案、可回写修正和可读产物，把“自我蒸馏”变成一个可迭代的工作流。

这个项目还有一层更深的目标：  
不是只复制一个固定的“你”，而是允许你把不同层次的自我版本慢慢写出来。  
你表现出来的自己、你理想中的自己、你在压力和欲望里暴露出来的自己，未必完全相同。  
`create-double-skill` 想做的，是给这种差异一个可以继续提问、继续修正、继续对照的容器。

## 本版包含

- 混合采集：访谈提问和自由描述可随时切换
- 固定 schema：以 `profile.yaml` 作为唯一结构化真源
- 产物生成：自动渲染 `profile.md` 和运行时 `SKILL.md`
- 修正闭环：支持“我不会这么说”“我更在意 X”这类回写
- 历史快照：重渲染前自动保留上一版结果
- 仓库自检与单测：包含 `validate_repo.py`、`unittest` 和 GitHub Actions

## 适合谁

- 想做“人格 + 决策方式”型数字分身，而不是全量人生档案库的人
- 想先从一个可控、可编辑、可审计的 v1 开始的人
- 想把项目直接交给 Codex 或其他 AI 编程助手协作使用的人
- 想把“我是谁”从抽象感受变成一个可以持续整理的结构问题的人

## 当前明确不做

- 自动抓取聊天记录、社媒、照片等高隐私素材
- 伪造没说过的经历、关系、时间线或记忆
- 复杂 web app、云同步或多人协作

## 快速开始

```powershell
python -m pip install -r requirements.txt
python scripts/double_builder.py init --slug my-double --display-name "我的分身"
python scripts/double_builder.py apply-turn --slug my-double --payload-file examples/initial-freeform-payload.json
python scripts/double_builder.py render --slug my-double
```

## 公开发布前建议

- 在 GitHub 仓库设置中补上 About、topics 和正式 PNG social preview
- 确认 `Actions` 最近一次运行是绿色
- 再做一轮隐私复核，确保没有真实个人 profile、聊天记录或截图残留

## 致谢

这个项目的创作灵感来自同类 skill 仓库的探索热潮，也受到了更成熟的 memory / companion / starter-kit 项目在定位与文档上的启发。  
另外，访谈设计中的一部分想象，也来自科幻作品里关于“自我分裂、自我重构、数字人格”的问题意识。  
同时，这个仓库本身是在 Codex 协作式工作流中构建和打磨出来的。
