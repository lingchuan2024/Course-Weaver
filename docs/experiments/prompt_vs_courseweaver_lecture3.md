# CourseWeaver 与直接 Prompt 生成笔记对比实验

## 1. 实验目的

本实验用于回答一个核心问题：

> 相比“把课件全文塞进一个精心设计的 prompt 里让大模型直接生成笔记”，CourseWeaver 这种“先结构化解析，再重构笔记”的流程到底强在哪里？

结论先行：直接 prompt 可以生成一份流畅的高层总结，但它更像“好看的课堂摘要”；CourseWeaver 生成的是一个可学习、可追溯、可检查的学习包。对开源大赛展示来说，项目优势不应只强调“笔记写得更像人”，而应强调“笔记质量可以被结构化证明”。

## 2. 实验设置

| 项目 | 设置 |
|---|---|
| 测试课件 | `lecture3.pdf` |
| 主题 | Linear Regression - Statistical Viewpoints |
| 页数 | 68 个解析页 |
| 直接 Prompt 输入 | `pdftotext` 抽取的全文，约 28515 字符 |
| 直接 Prompt 模型 | DeepSeek |
| CourseWeaver 模型 | DeepSeek 改写 CourseIR 规划后的 note chunks |
| 直接 Prompt 输出 | `docs/experiments/direct_prompt_baseline_lecture3.md` |
| CourseWeaver 主笔记 | `output/lecture3-deepseek/notes/01_lecture_notes.md` |
| CourseWeaver 溯源索引 | `output/lecture3-deepseek/notes/06_source_index.md` |
| CourseWeaver 覆盖报告 | `output/lecture3-deepseek/notes/07_coverage_report.md` |

本实验给直接 Prompt 方案的提示词已经尽量公平，不是简单说“总结一下 PDF”，而是明确要求它：

- 先抽取知识点，再按适合理解的顺序讲述；
- 保留公式、例子、作业和总结；
- 对并列知识点使用表格；
- 解释公式推导；
- 合并动画重复页；
- 输出自然讲义式 Markdown。

完整提示词见：`docs/experiments/direct_prompt_baseline_prompt.md`。

## 3. 直接 Prompt 基线

直接 Prompt 生成的笔记有 8 个主章节：

```text
一、本讲知识地图
二、从线性代数到概率：为什么 MSE 是合理的？
三、频率学派 vs 贝叶斯学派：两种世界观
四、偏差与方差：理解泛化误差的钥匙
五、过拟合与欠拟合：偏差-方差的直观体现
六、岭回归：正则化的经典案例
七、总结与知识串联
八、课后作业提示
```

这份输出的优点很明显：主线紧凑，语言流畅，对 MLE、MAP、Bias-Variance、Ridge Regression 等重点内容做了较好的概括。作为“快速预习摘要”是可用的。

但它的问题也很关键：

1. 它只有 8 个主章节，明显压缩了课件中大量细分知识点。
2. 没有任何页码引用，也没有来源 block，无法知道某句话来自课件哪一页。
3. 没有覆盖报告，无法判断哪些公式、动画页、作业要求或总结页被合并、遗漏或模型补充。
4. 它会自然补充一些正确但不可追溯的解释，例如把“拉普拉斯噪声 -> L1 loss”作为总结链条写入正文。这个解释本身合理，但用户无法区分它是课件内容、作业延伸，还是模型根据背景知识补出来的。
5. 它更重视“读起来顺”，不擅长保留每个知识点的出处、边界和细节。

## 4. CourseWeaver 输出

CourseWeaver 对同一份课件先生成 CourseIR，再生成笔记和学习包。本次输出规模如下：

| 指标 | 数值 |
|---|---:|
| 解析页数 | 68 |
| 原文 blocks | 651 |
| 知识单元 | 122 |
| 知识关系 | 61 |
| note chunks | 35 |
| valid blocks | 475 |
| covered blocks | 411 |
| merged blocks | 64 |
| ignored blocks | 176 |
| missing blocks | 0 |

主笔记中每个章节保留了页码范围，例如：

```text
Random Variables and Instances/Samples [p.18-p.22]
Mean, (Co)variance, and Their Unbiased Estimation [p.23-p.24]
The Variance of Estimation [p.26, p.27, p.28, p.29, p.30, p.39, p.40, p.41]
Ridge Regression: A Bayesian Viewpoint [p.58-p.61]
Homework 1: DDL — March 16, 2025, Midnight [p.68]
```

这说明 CourseWeaver 的主笔记不是一次性摘要，而是由可追溯的结构化单元拼接和改写出来的。

## 5. 量化对比

| 维度 | 直接 Prompt | CourseWeaver |
|---|---:|---:|
| 主笔记字符数 | 7296 | 37764 |
| 二级章节数 | 8 | 35 |
| 三级章节数 | 11 | 4 |
| Markdown 表格行 | 16 | 22 |
| 页码引用数量 | 0 | 130 |
| `来源：` 行数 | 0 | 35 |
| 是否有来源索引 | 无 | 有 |
| 是否有覆盖报告 | 无 | 有 |
| 是否有知识关系图数据 | 无 | 有 |
| 是否能支持前端学习进度高亮 | 不能 | 能 |

这些数字不代表“越长越好”，但能说明两者目标不同：

- 直接 Prompt 输出的是压缩后的“总览型笔记”；
- CourseWeaver 输出的是“可复核的学习材料系统”。

如果目标只是快速知道这节课大概讲什么，直接 Prompt 足够；如果目标是给学生自学、复习、查漏和回到原课件核对，CourseWeaver 明显更适合。

## 6. 多维度质量评估

### 6.1 完整性

直接 Prompt 只保留了本讲最醒目的主线：MSE/MLE、Frequentist/Bayesian、Bias-Variance、Ridge、Homework。它基本覆盖了课程骨架，但会压缩或省略一些课件中的细粒度内容，例如：

- Random Variables 与 samples/instances 的符号区分；
- mean、variance、covariance 的基础性质；
- variance of estimation 与 bias of estimation 的多页公式推导细节；
- model misspecification 与 training process 两种 bias-variance 解释角度；
- 课件中重复动画页到底是合并、忽略还是进入正文。

CourseWeaver 的优势在于它先记录 651 个原文 block，再把 475 个 valid block 分配为 covered 或 merged。即使主笔记后续需要再压缩，它也知道压缩前有哪些原始材料。

### 6.2 便于理解性

直接 Prompt 的叙述很自然，适合第一次快速读。它把整节课组织成 8 个大主题，认知负荷较低。

CourseWeaver 的当前版本更像一份详细讲义：它把知识点拆得更细，并在开头增加“关系导读与对比总结”，列出：

- 学习主线；
- 前置与支撑关系；
- 并列与对比知识点；
- 例子如何服务概念。

这使它不只是“顺着讲”，还能告诉学生为什么要这样学。例如 Bias 和 Variance 被识别为并列视角，Ridge 的 L2 正则化解释与 Bayesian 解释被识别为并列视角，线性回归例子被识别为 MLE 的引入场景。

现阶段 CourseWeaver 的不足是部分公式碎片仍会进入主笔记，导致正文有时过长；但这属于可优化的结构清洗问题，不影响它在完整性和可追溯性上的优势。

### 6.3 知识关系表达

直接 Prompt 也能写出对比表，但这些表是模型即时生成的结果，没有结构化关系数据支撑，前端无法进一步使用。

CourseWeaver 会保存 `relations`，并在前端把 `note_plan`、`knowledge_units` 和 `relations` 组织成学习路径图。用户滚动笔记时，右侧节点可以依次高亮，表示当前学习进度。这个能力只有在系统内部先有结构化知识图谱时才能实现，单纯 Markdown 笔记做不到。

### 6.4 可信度与可校验性

这是 CourseWeaver 最重要的优势。

直接 Prompt 的问题不是“它一定会错”，而是“用户不知道它哪里可能错”。它没有办法回答：

- 这段解释来自哪一页？
- 这个公式是不是课件里有？
- 哪些页面被合并了？
- 哪些 block 被忽略了？
- 有没有疑似遗漏？
- 模型有没有补充课件外的知识？

CourseWeaver 可以用来源索引和覆盖报告回答这些问题。比如本次输出明确记录：

```text
valid_blocks = 475
covered = 411
merged = 64
ignored = 176
missing = 0
```

这使得“笔记质量”不只是主观观感，而可以被审计。

### 6.5 复习与二次利用

直接 Prompt 只产生一份主笔记。后续如果要做知识树、概念表、公式表、错题、自测题、学习进度，必须再次让模型读整篇笔记并重新抽结构。

CourseWeaver 一次生成多个产物：

```text
01_lecture_notes.md
03_concepts.md
04_formulas_and_algorithms.md
05_common_mistakes.md
06_source_index.md
07_coverage_report.md
project.json
```

这些产物共享同一个 CourseIR，因此前端可以稳定支持：

- 笔记阅读；
- PDF 原文对照；
- 知识树/图；
- 节点学习进度高亮；
- 来源追溯；
- 漏洞检查；
- Markdown 下载。

## 7. 最关键的展示结论

如果只展示“生成了一篇笔记”，CourseWeaver 和直接 Prompt 的差异会被弱化，因为大模型本身已经能写出不错的概括。

更好的展示方式是突出下面这句话：

> CourseWeaver 的目标不是让模型直接写一篇漂亮摘要，而是把课件变成一个可追溯、可校验、可交互的学习包。

在开源大赛材料中，建议把对比重点放在这四点：

1. **完整性可证明**：有 block 账本、知识单元和覆盖报告，不只是“看起来讲到了”。
2. **理解路径更清楚**：先抽知识关系，再生成学习路径和关系导读。
3. **可信度更高**：每个章节能回到页码和来源 block，用户能检查模型是否乱补。
4. **前端体验更有价值**：笔记、PDF、知识树、学习进度和溯源联动，而不是只展示一篇 Markdown。

## 8. 当前版本仍需诚实说明的不足

CourseWeaver 当前输出已经能体现项目优势，但还不是最终形态：

- 有些公式 block 仍然被当成独立章节，主笔记略显冗长；
- `The Bias of Estimation` 存在重复章节，需要进一步合并；
- 关系抽取目前仍以启发式为主，还没有让 LLM 直接参与结构化关系确认；
- 覆盖率为 0 missing 不等于语义完全无遗漏，只表示所有 valid block 都被分配到了 covered 或 merged。

这些不足反而适合放入后续计划：7、8 月重点优化“结构清洗、知识关系抽取、按关系生成图表和对比总结”。MVP 阶段要证明的是：这条路线比单纯 prompt 更有上限，也更适合做成真正的学习工具。

