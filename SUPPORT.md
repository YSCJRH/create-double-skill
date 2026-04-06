# Support

Short version: use README for first-run help, Issues for reproducible problems, and SECURITY for private vulnerability reports.

## Start here

如果你只是想先跑通项目，先看：

- [README.md](README.md)
- [examples/README.md](examples/README.md)

先跑这两个命令，通常能很快定位大部分环境问题：

```powershell
python scripts/double_builder.py doctor
python scripts/validate_repo.py
```

## Usage help

如果你的问题属于“怎么开始”“命令该怎么跑”“为什么结果和预期不一样”，建议按这个顺序排查：

1. 先看 [README.md](README.md) 的首跑路径
2. 再看 [examples/README.md](examples/README.md) 和相关 transcript
3. 运行：

```powershell
python scripts/double_builder.py doctor
python scripts/validate_repo.py
```

4. 如果你只是想先确认环境和输出，先试：

```powershell
python scripts/double_builder.py start --demo --use-case work
```

如果仍然没解决，可以开 GitHub issue。为了便于识别，标题可以带上 `[Support]`。

## Bug reports

如果你已经拿到了可复现的错误，请直接使用 bug report 模板。

适合走 bug report 的情况：

- 命令报错
- 文件没有生成
- correction 没有回写
- examples、README、issue templates 与真实行为不一致

## Feature requests

如果你想提出改进建议，请使用 feature request 模板。

比较有帮助的建议通常会说明：

- 你遇到的具体问题
- 为什么值得做
- 它会不会增加复杂度、隐私风险或维护成本

## Security issues

如果问题可能涉及漏洞、隐私边界失效或敏感数据暴露，请不要开公开 issue。

改看：

- [SECURITY.md](SECURITY.md)

## What to include

无论你是来求助还是报 bug，尽量一起提供：

- 你的操作系统
- Python 版本
- 你运行的完整命令
- `doctor` 或 `validate_repo.py` 的输出
- 最短复现步骤
- 你期望发生什么，实际又发生了什么

如果问题涉及真实个人资料、私有知识库或生成分身内容，请先做脱敏处理。
