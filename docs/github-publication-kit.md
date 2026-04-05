# GitHub 发布文案包

这个文件是 `create-double-skill` 对外发布时的最终复制粘贴入口。  
如果你准备把仓库切成 `Public`，优先使用这里的内容。

## About

```text
Build a private digital double that captures how you judge, set boundaries, and give advice.
```

## Topics

```text
digital-double
skill
codex
local-first
personality-modeling
prompt-engineering
```

## Release Title

```text
v0.1.0 - A local-first starting point for building a private digital double
```

## Release Body

```md
Not a life-log. Not a memory simulator. A local-first way to build and correct a self-model.

`create-double-skill` 现在最想解决的一件事是：

不用自动抓取大量隐私素材，也能在几分钟内生成一个更像“你会怎么判断”的数字分身。

这不是人生资料库，不是记忆模拟器，也不承诺“人格复制”。
它更像一个 `local-first` 的 starter repo：用结构化档案、可回写修正和可读产物，把“自我蒸馏”变成一个可迭代的工作流。

它也不只是在尝试“复制一个固定的你”。
这个项目更想做的，是给你一个可编辑的自我模型：
你表现出来的自己、你理想中的自己、你在压力和欲望里暴露出来的自己，未必完全相同。
`create-double-skill` 让这些版本先被写出来，再被比较、被修正、被继续追问。

## This release includes

- 3-minute first run：`start` 命令直接提问、写入、渲染和预览
- 自然语言 correction：`correct` 命令支持“我不会这么说”“我更在意 X”
- `doctor` 健康检查：依赖、仓库完整性、写权限、终端编码提示
- 混合采集：访谈提问和自由描述可随时切换
- 固定 schema：以 `profile.yaml` 作为唯一结构化真源
- 产物生成：自动渲染 `profile.md` 和运行时 `SKILL.md`
- 修正闭环：支持“我不会这么说”“我更在意 X”这类回写
- 历史快照：重渲染前自动保留上一版结果
- 仓库自检与单测：包含 `validate_repo.py`、`unittest` 和 GitHub Actions
- issue templates、发布前检查清单、对标文档和首版发布草稿

## Good fit for

- 想做“人格 + 决策方式”型数字分身，而不是全量人生档案库的人
- 想先从一个可控、可编辑、可审计的 v1 开始的人
- 想把“我是谁”从抽象感受变成一个可以持续整理的结构问题的人
- 想把项目直接交给 Codex 或其他 AI 编程助手协作使用的人

## Explicit boundaries

- 不自动抓取聊天记录、社媒、照片等高隐私素材
- 不伪造没说过的经历、关系、时间线或记忆
- 不提供心理诊断，也不声称找出唯一真实的“本我”
- 当前不做复杂 web app、云同步或多人协作

## Quick start

```powershell
python -m pip install -r requirements.txt
python scripts/double_builder.py start --slug my-double --display-name "我的分身"
```

Built with Codex, but not limited to Codex.
The repo can run on its own, and usually works especially smoothly in Codex-style AI coding workflows.
```

## Social Preview

推荐版本：

```text
Title: create-double-skill
Subtitle: Not just a clone of you
Footer: An editable model of your different selves
```

更稳版本：

```text
Title: create-double-skill
Subtitle: Build a private digital double
Footer: How you think, choose, and present yourself
```

## 仓库首页一句话

```text
把“我是谁”变成一个可迭代的工程问题。
```

## 使用建议

发布前最后检查顺序：

1. 先在仓库页面填写 `About` 和 `Topics`
2. 上传正式 `PNG` social preview
3. 用上面的 `Release Title` 和 `Release Body` 创建 `v0.1.0`
4. 确认 `Actions` 最近一次运行为绿色
5. 再把仓库从 `Private` 切换到 `Public`
