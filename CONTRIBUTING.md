# Contributing

Short version: small, concrete, repo-aligned contributions are welcome.

感谢你愿意改进 `create-double-skill`。

这个仓库更适合小而明确的改动：让第一次运行更顺、让生成结果更可信、让文档和示例更清楚、让边界更诚实。它不是一个重治理项目，所以这里不会要求复杂流程；但我们希望每次贡献都和当前仓库的方向保持一致。

## How to contribute

欢迎的贡献包括：

- README、示例和帮助文档改进
- `start` / `correct` / `doctor` 等首跑路径优化
- prompts、routing、rendering 的质量提升
- tests、校验脚本、GitHub 模板和公开面完善
- 知识库层的低风险增强

如果你的改动会明显改变项目定位、隐私边界或运行真源，请先开 issue 讨论。

## Before opening an issue or PR

在提 issue 或 PR 之前，先做这几件事：

1. 先看 [README.md](README.md) 和 [examples/README.md](examples/README.md)
2. 如果是使用问题，先运行：

```powershell
python scripts/double_builder.py doctor
python scripts/validate_repo.py
```

3. 如果是可复现问题，尽量整理出最短命令链
4. 如果是安全问题，不要开公开 issue，改看 [SECURITY.md](SECURITY.md)

## Local setup

最短本地准备流程：

```powershell
python -m pip install -r requirements.txt
python scripts/validate_repo.py
python -m unittest tests/test_double_builder.py tests/test_knowledge_base.py -v
```

如果你只是想先看项目有没有跑起来，也可以先执行：

```powershell
python scripts/double_builder.py doctor
python scripts/double_builder.py start --demo --use-case work
```

## Suggested contribution types

当前最适合的贡献类型：

- `README.md`、`examples/`、issue templates
  让陌生用户更快跑通第一次
- `scripts/double_builder.py`
  改进首跑体验、修正流程、输出质量
- `prompts/` 和 `references/`
  让访谈、修正和渲染更稳
- `tests/`
  给 CLI、知识库层和渲染行为补回归保护
- `scripts/knowledge_base.py`
  只做低风险、local-first 的增强

## Validation before submitting

提交前至少跑：

```powershell
python scripts/validate_repo.py
python -m unittest tests/test_double_builder.py tests/test_knowledge_base.py -v
```

如果你的改动影响了首跑路径、README 命令、issue 模板、examples 或知识库层，请再做一次针对性的手动检查。

## Project boundaries

请不要把项目带到这些方向：

- 高隐私自动抓取聊天记录、照片、社媒
- life-log、记忆模拟、数字永生式叙事
- 把 `profile.yaml` 变成多份并行运行真源之一
- 重型 web app、SaaS、云同步、托管平台
- 通过堆功能牺牲可编辑、可审计、可回写修正的核心体验

当前默认边界是：

- `profile.yaml` 是唯一运行时真源
- `kb/` 是长期积累层，不是第二份并行配置
- 默认 local-first
- 不伪造经历、关系、时间线或具体记忆

## Pull request checklist

提交 PR 前请自查：

- 改动范围小且目标明确
- 文案、命令、示例、测试彼此一致
- 没有提交 `doubles/*`、`.project-kb/`、`.private-docs/` 等私有材料
- 没有引入与项目定位冲突的承诺或术语
- 如果改了用户可见行为，README 或 examples 已同步
- 如果改了路由、修正、渲染或 KB 行为，测试已覆盖

谢谢你的贡献。
