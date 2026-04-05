# start transcript

下面是一段更接近真实 first run 的交互示例。

```text
$ python scripts/double_builder.py start --slug my-double --display-name "我的分身"
3 分钟内生成你的第一个 double，不需要写 JSON。

1/3 你做重要决定时，通常先保护什么？
> 长期可持续、关系里的稳定感

2/3 别人来找你要建议时，你通常会先问什么，或先看什么？
> 我会先问这件事三个月后还重要吗

3/3 你不舒服时会怎么设边界？
> 我会把底线讲清楚，但尽量不把气氛推到最糟

已生成：
- doubles/my-double/profile.md
- doubles/my-double/SKILL.md

当前 preview：
- 优先保护：长期可持续；关系里的稳定感
- 给建议前先问：我会先问这件事三个月后还重要吗
- 设边界方式：我会把底线讲清楚，但尽量不把气氛推到最糟
- 下一步：别人低落或混乱时，你更像是安抚、追问，还是帮对方看清取舍？

如果有一句不对，直接输入“我不会这么说...”或“我更在意...”，回车跳过：
> 我更在意边界清晰
```

这个 first run 刻意把重点放在：

- 取舍顺序
- 默认提问方式
- 边界风格

而不是先让你写一堆 biography。
