# create-double-skill v0.1.0

首个公开版本草稿。

## 标题

`v0.1.0 - A local-first starting point for building a private digital double`

## 一句话介绍

`create-double-skill` 是一个本地优先、可修正、可审计的数字分身起点，用来逐步沉淀一个人的判断方式、边界感和建议风格。

## 首屏开场句

`Not a life-log. Not a memory simulator. A local-first way to build and correct a self-model.`

## 发布说明

这一版聚焦的是：

- 让陌生用户不需要手写 JSON payload
- 在几分钟内生成第一个可信 artifact
- 让分身更像“你会怎么判断”，而不只是“你会怎么说”

现在 `start` 不再默认所有人都走同一组固定问题，而是先选用途，再按用途继续深挖：

- `general`
- `work`
- `self-dialogue`
- `external`
- `custom`

同时支持三种深度：

- `quick`
- `standard`
- `deep`

## 本版包含

- 3-minute first run：`start` 命令先选用途，再提问、写入、渲染和预览
- 自适应访谈：支持 `general / work / self-dialogue / external / custom`
- 深度控制：支持 `quick / standard / deep`
- 自然语言 correction：`correct` 命令支持“我不会这么说”“我更在意 X”
- `doctor` 健康检查：依赖、仓库完整性、写权限、终端编码提示
- 混合采集：访谈提问和自由描述可随时切换
- 固定 schema：以 `profile.yaml` 作为唯一结构化真源
- 产物生成：自动渲染 `profile.md` 和运行时 `SKILL.md`

## 快速开始

```powershell
python -m pip install -r requirements.txt
python scripts/double_builder.py start --slug my-work-double --display-name "工作分身" --use-case work
```

## 当前明确不做

- 自动抓取聊天记录、社媒、照片等高隐私素材
- 伪造没说过的经历、关系、时间线或记忆
- 重型 web app、云同步或多人协作
