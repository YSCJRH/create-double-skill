# GitHub 发布文案包

这个文件是 `create-double-skill` 对外发布时最适合直接复制粘贴的一组文案。

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
现在它还支持先选用途，再按用途继续细化：
工作协作版、自我对话版、对外表达版，甚至一个自定义用途入口。

这不是人生资料库，不是记忆模拟器，也不承诺“人格复制”。
它更像一个 `local-first` 的 starter repo：用结构化档案、可回写修正和可读产物，把“自我蒸馏”变成一个可迭代的工作流。

## This release includes

- 3-minute first run：`start` 命令先选用途，再提问、写入、渲染和预览
- 自适应访谈：支持 `general / work / self-dialogue / external / custom`
- 深度控制：支持 `quick / standard / deep`
- 自然语言 correction：`correct` 命令支持“我不会这么说”“我更在意 X”
- `doctor` 健康检查：依赖、仓库完整性、写权限、终端编码提示
- `profile.yaml` 继续作为唯一 canonical structured source of truth

## Quick start

```powershell
python -m pip install -r requirements.txt
python scripts/double_builder.py start --slug my-work-double --display-name "工作分身" --use-case work
```
```

## Social Preview

推荐版本：

```text
Title: create-double-skill
Subtitle: Not just how you sound
Footer: Capture how you judge, set boundaries, and give advice
```
