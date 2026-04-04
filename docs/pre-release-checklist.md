# 发布前最后检查

适用仓库：`YSCJRH/create-double-skill`  
检查时间：`2026-04-04`  
状态约定：`[x]` 已完成，`[ ]` 待手动确认，`[-]` 当前刻意不做

## 仓库门面

- [x] 仓库名与 README 标题统一为 `create-double-skill`
- [x] `README.md` 首屏包含 banner、项目定位、上手路径和安装说明
- [x] 已存在 `LICENSE`，当前采用 `MIT License`
- [x] 仓库默认分支为 `main`
- [x] 当前仓库保持 `Private`
- [ ] GitHub `About` 已设置为：`Build a private digital double from guided interviews and freeform self-description.`
- [ ] GitHub `Topics` 已设置为：`digital-double`, `skill`, `codex`, `local-first`, `personality-modeling`, `prompt-engineering`
- [ ] GitHub 设置页已上传正式 `PNG` social preview

## 隐私与泄露

- [x] `doubles/` 目录当前仅保留 `.gitkeep`
- [x] 示例 payload 仅包含虚构演示内容，不包含真实个人 profile
- [x] 已扫描常见 token / key 模式，未发现明显 secrets
- [x] 已扫描绝对本机路径、`users.noreply`、本地目录痕迹，未发现仓库内容残留
- [x] 仓库当前不自动导入聊天记录、社媒、照片等高隐私素材
- [ ] 手动复核 README、截图和 social preview 中没有误放私人信息

建议在公开前再执行一遍：

```powershell
rg -n "sk-[A-Za-z0-9_-]+|ghp_[A-Za-z0-9]+|github_pat_[A-Za-z0-9_]+|AKIA[0-9A-Z]+" .
rg -n "D:\\|remote connection|users\.noreply|@users\.noreply|file://|C:\\Users\\34793" .
```

## 安装与首次运行

- [x] `requirements.txt` 存在且安装路径清晰
- [x] README 已提供最短初始化流程
- [x] README 已提供“交给 Codex 或其他 AI 编程助手安装”的提示词
- [x] `examples/` 目录提供可直接套用的 payload 示例
- [ ] 用全新环境按 README 走一遍安装流程，确认零上下文也能跑通

推荐最小验证顺序：

```powershell
python -m pip install -r requirements.txt
python scripts/validate_repo.py
python -m unittest tests/test_double_builder.py -v
python scripts/double_builder.py init --slug smoke-double --display-name "冒烟分身"
python scripts/double_builder.py apply-turn --slug smoke-double --payload-file examples/initial-freeform-payload.json
python scripts/double_builder.py render --slug smoke-double
```

## 功能与测试

- [x] 仓库自检脚本 `python scripts/validate_repo.py`
- [x] 单元测试 `python -m unittest tests/test_double_builder.py -v`
- [x] 可通过最小 CLI smoke test 生成 `profile.yaml`、`profile.md` 和运行时 `SKILL.md`
- [x] 当前版本的边界写清楚了：不伪造记忆，不承诺完整人格复制
- [-] 本轮不补复杂 UI、自动导入器或云同步

Smoke test 期望：

- `route` 能识别基础输入类型
- `apply-turn` 能合并结构化 payload
- `render` 能产出 `doubles/<slug>/profile.yaml`
- 运行后如不需要保留样本，应手动删除临时 `slug`

## GitHub 配置

- [x] 远端仓库已创建：`https://github.com/YSCJRH/create-double-skill`
- [x] 当前默认分支是 `main`
- [ ] 最新提交的 GitHub Actions 结果为绿色
- [ ] README 首屏、About、topics、social preview 的用词已对齐
- [x] 本地已准备 issue templates
- [x] 本地已准备 `v0.1.0` 发布草稿
- [ ] 准备公开时，决定是否启用 discussion 或正式创建首个 release

说明：

- 如果当前自动化环境无法读取私有仓库的 workflow 状态，请直接在 GitHub `Actions` 页面手动确认最近一次运行是否为绿色

目前最推荐的元信息：

- About: `Build a private digital double from guided interviews and freeform self-description.`
- Topics: `digital-double`, `skill`, `codex`, `local-first`, `personality-modeling`, `prompt-engineering`

## 公开切换前确认

- [ ] 仓库已经至少私下自用或内测一轮，确认 README 没有误导
- [ ] 准备好一张正式 `PNG` social preview 图
- [ ] 决定是否发布 `v0.1.0`
- [ ] 决定是否添加 issue template，减少公开后重复提问
- [ ] 决定是否补一页更完整的安装 / 故障排查文档

公开前最后的 Go / No-Go 问题：

1. 现在的 README 是否能让第一次访问者在 3 分钟内理解项目是什么、能做什么、不能做什么？
2. 仓库里是否绝对没有真实个人资料、聊天记录、照片或路径残留？
3. 当前版本是否已经足够稳定，能承受第一批 issue 和 star 带来的关注？
