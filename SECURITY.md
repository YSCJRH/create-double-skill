# Security Policy

Short version: do not report security issues in public issues.

## Supported versions

当前默认只关注下面这些版本范围：

| Version | Supported |
| --- | --- |
| `main` | Yes |
| Latest public release | Yes |
| Older releases / old snapshots | No guarantee |

如果问题只影响很旧的版本、历史快照或已废弃路径，这个仓库不保证会补安全修复。

## What to report

适合作为安全问题上报的内容包括：

- 可能导致未授权访问、命令执行、路径逃逸或任意文件写入的问题
- 会让真实个人资料、生成分身或私有知识库意外暴露的漏洞
- 依赖或默认配置中的明显安全风险，且你已经能说明具体影响
- 任何会让项目默认隐私边界失效的问题

## How to report

请不要为安全问题开公开 issue。

优先顺序如下：

1. 如果仓库启用了 GitHub 私有漏洞报告，优先使用它
2. 如果没有，请通过仓库所有者 GitHub 主页私下联系维护者：
   - [YSCJRH](https://github.com/YSCJRH)

建议在报告里尽量包含：

- 受影响的版本或分支
- 最短复现步骤
- 影响范围
- 是否涉及真实敏感数据
- 你认为的临时缓解方式（如果有）

## What not to report publicly

请不要在公开 issue、PR 或评论里直接贴出：

- 漏洞细节复现步骤
- 真实 token、账号、路径、系统信息
- 私有样本、真实分身文件、私有知识库内容
- 会帮助他人立即利用问题的完整 exploit 细节

## Response expectations

这个仓库目前由个人维护，不承诺固定 SLA。

维护者会尽快：

- 确认是否收到了报告
- 判断它是否属于安全问题
- 评估影响范围
- 在可行时提供修复、缓解建议，或说明下一步处理方式

## Non-security issues

以下问题请不要按安全问题提交：

- 一般使用问题或环境问题
- 非敏感的功能 bug
- 产品建议或体验改进

这些内容请改看：

- [SUPPORT.md](SUPPORT.md)
- `.github/ISSUE_TEMPLATE/bug_report.yml`
- `.github/ISSUE_TEMPLATE/feature_request.yml`
