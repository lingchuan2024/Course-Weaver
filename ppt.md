## 第 1 页：标题页

标题：

```text
CourseWeaver
面向课程课件的 AI 知识重构系统
```

副标题：

```text
从课件文件到讲义笔记、知识图谱、溯源证据与复习材料
```

页面主文案：

```text
老师的课件不是完整教材，而是课堂讲解的结构化线索。

CourseWeaver 希望做的不是把课件压缩成摘要，而是将课件中的概念、公式、例子、推导和作业重新组织成学生可以学习、检查和复用的课程知识系统。
```

页面底部一句话：

```text
把课件从“展示材料”转化为“可学习的知识网络”。
```

图片建议：

- 放当前产品界面截图，但不要满屏堆 UI。
- 画面中心可以是：
  ```text
  Slides → CourseIR → Knowledge Graph → Learning Notes
  ```
- 背景用淡网格或节点线条，体现“知识网络”。

---

## 第 2 页：现有产品痛点：AI 能读文档，但还没真正理解“课程”

标题：

```text
现有 AI 文档工具很强，但大多停留在“读文档”和“问文档”
```

页面文字：

```text
现在已经有很多成熟产品可以处理 PDF 或课程材料：

ChatGPT 支持上传 PDF、Word、PPT 等文件，并可以对文档进行总结、分析和问答。它适合快速理解一份材料，但输出通常是一次性回答，缺少课程级知识结构和覆盖校验。

NotebookLM 可以把用户上传的 sources 变成带引用的问答、学习指南、音频概览和视频概览。它非常适合研究和资料理解，但它的重点是 source-grounded assistant，而不是把课件解析成可审计的 block、knowledge unit、relation 和 coverage ledger。

ChatPDF、Humata 这类 PDF Chat 工具强调“上传 PDF 后提问、总结、定位引用”。它们适合快速查找答案，但核心交互仍然是“问答”，不是系统化生成一套可复习、可跳转、可维护的课程知识库。

SciSpace / Explainpaper 等工具更偏向论文阅读辅助，能解释选中的公式、段落和论文内容，但不直接面向多份课程课件的知识合并与学习路径重构。
```

页面强调句：

```text
这些产品解决的是“我如何快速理解这份文档？”
CourseWeaver 要解决的是“这门课的知识如何被结构化、连接、追溯和复习？”
```

图片建议：

- 做一个横向竞品能力矩阵。
- 列：
  ```text
  ChatGPT / NotebookLM / ChatPDF / SciSpace / CourseWeaver
  ```
- 行：
  ```text
  文档总结
  文档问答
  引用/溯源
  课程知识点抽取
  知识图谱
  覆盖率检查
  多课件知识库
  ```

参考来源可放页脚小字：

- OpenAI 文件上传能力说明：ChatGPT 可上传并总结/分析 PDF 等文件。
- Google NotebookLM 官方博客：NotebookLM 可基于 sources 回答、生成 study guides、Audio Overview、Video Overview，并带引用。
- ChatPDF 官方页面：强调 PDF 问答、总结、引用和 side-by-side 阅读。

---

## 第 3 页：核心问题：课件不是文章，不能只做摘要

标题：

```text
课程课件的难点：内容不是线性文章，而是教学现场的压缩表示
```

页面文字：

```text
课件通常不是完整教材，而是老师课堂讲解的提示框架。

它有几个典型特点：

1. 知识点跨页分散  
   一个概念可能分布在标题页、公式页、例子页和推导页中。

2. 内容高度压缩  
   PDF 上只有公式和关键词，真正的解释通常来自课堂讲解。

3. 动画页和重复页很多  
   同一页可能因为逐步展示而在 PDF 中重复出现多次。

4. 公式和图表信息密度高  
   普通摘要容易跳过符号含义、推导步骤和适用条件。

5. 学习顺序不等于课件顺序  
   老师讲课顺序不一定是学生自学时最容易理解的顺序。

因此，CourseWeaver 的任务不是 summarize，而是 reconstruct。
```

图片建议：

- 左侧放一张课件页面截图。
- 右侧标注：
  ```text
  title
  formula
  derivation
  example
  repeated animation
  homework
  ```
- 底部写：
  ```text
  课件需要被“重构”，不是被“压缩”。
  ```

---

## 第 4 页：CourseWeaver 完整产品形态：课程知识工作台

标题：

```text
CourseWeaver 完整形态：一个课程知识工作台
```

页面文字：

```text
CourseWeaver 的完整产品不是“上传 PDF，得到一篇笔记”。

它应该是一个围绕课程材料构建的知识工作台：

1. 输入层  
   支持课件 PDF/PPT、课堂录音、作业、教材章节、老师补充资料。

2. 知识解析层  
   将材料拆解成 page、block、formula、figure、table、algorithm、example 等可追溯证据。

3. 知识库层  
   抽取并合并知识点，形成课程级 Knowledge Base。

4. 知识关系层  
   建立前置依赖、并列关系、对比关系、例子关系、推导关系。

5. 学习输出层  
   生成讲义式笔记、知识图谱、概念卡片、公式表、错题提醒、自测题和复习路径。

6. 学习交互层  
   学生可以在笔记、原课件、知识图谱和复习材料之间跳转。
```

图片建议：

- 做一个完整产品架构图：

```text
Course Materials
PDF / PPT / Audio / Homework
        ↓
CourseIR
Page / Block / Unit / Relation / Coverage
        ↓
Course Knowledge Base
Concepts / Formulas / Examples / Dependencies
        ↓
Learning Workspace
Notes / Graph / Source / Review / Tests
```

---

## 第 5 页：完整产品核心能力：课程知识库与同知识点跳转

标题：

```text
完整形态的关键：同一个知识点只维护一次，所有材料都能跳转到它
```

页面文字：

```text
在完整产品中，CourseWeaver 会为一门课建立持续增长的课程知识库。

例如“Maximum Likelihood Estimation”可能出现在：

- 第 3 讲线性回归统计视角
- 第 5 讲逻辑回归
- 第 8 讲生成模型
- 作业题中的参数估计推导
- 教材某一章的概率建模部分

传统工具会把这些内容分别总结，学生需要自己记住它们之间的关系。

CourseWeaver 的目标是：
识别这些材料中重复或相关的知识点，并把它们合并到同一个知识库节点。

学生看到任意一处 MLE 时，可以跳转到：
1. 这个知识点的统一解释
2. 它在不同课件中的出现位置
3. 相关公式和推导
4. 前置知识，如 Gaussian Noise、Likelihood
5. 后续知识，如 MAP、Ridge Regression、Bayesian View
6. 对比知识，如 MLE vs MAP
```

图片建议：

- 中间一个大节点：
  ```text
  Maximum Likelihood Estimation
  ```
- 周围连接：
  ```text
  Lecture 3 p.6-p.13
  Lecture 5 Logistic Regression
  Homework 1
  Textbook Chapter
  MAP
  Gaussian Noise
  Ridge Regression
  ```
- 用不同颜色表示：
  - 来源
  - 前置
  - 对比
  - 应用

---

## 第 6 页：完整产品核心体验：从阅读笔记到知识图谱跳转

标题：

```text
完整形态的学习体验：读笔记时，知识图谱同步点亮
```

页面文字：

```text
CourseWeaver 的理想使用流程不是“生成后下载一篇 Markdown”，而是一个持续交互的学习过程。

学生阅读笔记时：

1. 当前阅读到的知识点会在知识图谱中高亮。
2. 已经阅读过的节点标记为完成。
3. 点击任意节点，可以查看：
   - 讲义解释
   - 原课件页码
   - 关联公式
   - 前置知识
   - 易混淆知识
   - 相关例题
4. 点击边，可以知道两个知识点为什么相关：
   - A 是 B 的前置
   - A 和 B 需要对比
   - A 是 B 的例子
   - A 推导出 B
5. 如果学生遇到忘记的前置知识，可以直接跳回对应节点复习。

最终体验是：
学生不是在读一篇孤立笔记，而是在沿着课程知识网络学习。
```

图片建议：

- 放一个产品概念图：
  ```text
  Note Reader ↔ Knowledge Graph ↔ Source PDF ↔ Review Cards
  ```
- 或放当前前端截图，并标出：
  - 中间笔记
  - 右侧知识图
  - 左侧课件来源
  - 节点高亮

---

## 第 7 页：当前 MVP 已完成的范围

标题：

```text
当前 MVP：先跑通一份课件的完整知识重构链路
```

页面文字：

```text
当前版本聚焦一个高价值场景：

输入一份机器学习 PDF 课件，输出一套可读、可追溯、可检查的学习材料。

已完成能力：

1. PDF 解析  
   提取 page、block、bbox、reading order。

2. AI 辅助知识点抽取  
   DeepSeek / Kimi 可用于抽取知识点、学习阶段、父主题、前置依赖和易混淆关系。

3. CourseIR 结构化表示  
   保存 pages、blocks、knowledge_units、note_plan、relations、coverage_items。

4. 讲义式笔记生成  
   按知识点组织，而不是逐页摘要。

5. 来源索引与覆盖报告  
   每个知识点保留来源页码和 block id。

6. 前端学习工作台  
   同时展示课件、笔记、知识关系图、溯源和漏洞检查。
```

图片建议：

- 放当前产品截图。
- 或放 MVP 流程图：
  ```text
  lecture3.pdf → CourseIR → Notes + Graph + Coverage
  ```

---

## 第 8 页：MVP 前端展示

标题：

```text
MVP 前端：课件、笔记、图谱、溯源在同一工作台中联动
```

页面文字：

```text
当前前端采用三栏结构：

左侧：原课件  
用户可以直接看到 PDF 页面，确认笔记对应的真实课件内容。

中间：生成笔记  
Markdown 已渲染，可以直接阅读和下载。

右侧：知识关系与可信度工具  
包括知识关系图、来源溯源和漏洞检查。

这个设计的目的不是展示中间数据，而是让用户一眼理解：
这份笔记从哪里来，讲了什么，和哪些知识点有关，有没有遗漏。
```

图片建议：

- 放完整界面截图。
- 加标注：
  ```text
  Source PDF
  Generated Note
  Knowledge Graph
  Traceability
  Coverage Review
  ```

---

## 第 9 页：实验设置：同一课件，对比直接 Prompt

标题：

```text
实验设计：同一份课件，两种生成方式
```

页面文字：

```text
测试课件：
Introduction to Machine Learning
Lecture 3 Linear Regression - Statistical Viewpoints

对比方法：

Baseline：直接 Prompt
将 lecture3.pdf 的 pdftotext 全文输入 DeepSeek，并要求它生成高质量中文讲义。

CourseWeaver：
先解析 PDF，生成 CourseIR、知识点、关系图和覆盖报告，再调用 DeepSeek 生成讲义式笔记。

实验关注：
1. 是否完整覆盖课件内容
2. 是否保留公式、例子、推导细节
3. 是否能回到原课件来源
4. 是否能形成可复用的知识结构
5. 是否适合学生真正复习
```

图片建议：

- 左右流程对比：
  ```text
  Direct Prompt: PDF Text → LLM → Markdown
  CourseWeaver: PDF → CourseIR → Units → Relations → Notes + Graph + Coverage
  ```

---

## 第 10 页：量化对比

标题：

```text
量化结果：CourseWeaver 生成的是学习包，不只是一篇文章
```

页面文字：

```text
lecture3.pdf 实验结果：

CourseWeaver 输出：
- 解析页数：68
- 原文 blocks：651
- 有效 blocks：475
- 知识单元：122
- 知识关系：61
- note chunks：35
- covered blocks：411
- merged blocks：64
- missing blocks：0

直接 Prompt 输出：
- 主章节：8 个
- 页码引用：0
- 来源 block：0
- 覆盖报告：无
- 知识关系图：无

这说明直接 Prompt 更像一份浓缩讲义，而 CourseWeaver 输出的是可检查、可跳转、可继续构建知识库的学习资产。
```

图片建议：

- 表格或柱状图。
- 推荐可视化：
  - `页码引用：0 vs 130`
  - `来源行：0 vs 35`
  - `知识关系：0 vs 61`
  - `覆盖报告：无 vs 有`

---

## 第 11 页：具体文字对比：直接 Prompt

标题：

```text
直接 Prompt：主线清楚，但细节被压缩
```

页面文字：

```text
直接 Prompt 输出示例：

“本讲从统计学的角度重新审视线性回归，核心要回答三个问题：
1. 为什么最小化均方误差（MSE）是合理的？
2. 模型的预测误差从何而来？
3. 如何防止模型过拟合？”

这段内容的问题不是“不好”，而是它的产品形态更接近高层摘要。

它的优点：
- 主线清晰
- 语言流畅
- 适合快速预习

它的不足：
- 没有页码来源
- 没有 block 证据
- 不知道是否漏掉推导细节
- 把很多基础铺垫压缩掉
- 无法进入知识库复用
```

图片建议：

- 放直接 Prompt 生成笔记截图。
- 旁边加标注：
  ```text
  readable but not auditable
  ```

---

## 第 12 页：具体文字对比：CourseWeaver

标题：

```text
CourseWeaver：先补齐学习路径，再生成笔记
```

页面文字：

```text
CourseWeaver 输出示例：

“首先，我们定义一个随机变量 X。这个 X 本身是一个抽象概念，它代表一个随机过程的结果，并且会生成一个分布 P_X。接着，我们引入样本 x，它是空间 X 中的一个点，表示从分布 P_X 中抽取出来的一个具体观测值。”

这段内容来自：
Random Variables and Instances/Samples [p.18-p.22]

它的价值在于：
1. 没有直接跳到 MLE，而是先补齐统计符号基础。
2. 区分了随机变量 X、样本 x、数据矩阵 X。
3. 解释了后续 mean、variance、bias、variance estimation 的前置知识。
4. 保留了明确来源页码。
5. 可以在知识图中作为后续节点的 foundation。
```

图片建议：

- 放 CourseWeaver 笔记截图。
- 旁边放关系示意：
  ```text
  Random Variables
      ↓
  Mean / Variance
      ↓
  Bias / Variance of Estimation
      ↓
  Bias-Variance Tradeoff
  ```

---

## 第 13 页：可信度对比

标题：

```text
CourseWeaver 的优势：笔记质量可以被审计
```

页面文字：

```text
直接 Prompt 无法回答：

- 这段解释来自哪一页？
- 这个公式是不是课件原文中出现过？
- 哪些内容被合并了？
- 哪些内容被忽略了？
- 有没有疑似遗漏？
- 模型有没有补充课件外知识？

CourseWeaver 可以回答这些问题。

本次实验：
valid_blocks = 475
covered = 411
merged = 64
ignored = 176
missing = 0

这意味着每个有效原文块都有一个去向：
进入笔记、合并进知识点、被识别为噪声，或者进入复核列表。
```

图片建议：

- 放 coverage report 或前端“漏洞检查”截图。
- 页面大字：
  ```text
  从“看起来合理”到“可以被检查”
  ```

---

## 第 14 页：技术实现

标题：

```text
技术实现：AI 判断知识，结构保证可信
```

页面文字：

```text
CourseWeaver 采用“AI + 结构化校验”的设计。

AI 负责：
- 判断知识点边界
- 合并跨页内容
- 识别前置依赖和易混淆关系
- 生成自然讲义正文

结构化系统负责：
- 保存 page / block / unit / relation
- 校验 source_blocks 是否真实存在
- 生成 coverage ledger
- 构建知识关系图
- 支持前端溯源、跳转和下载

这种设计避免了两个问题：
1. 纯 Prompt 写得顺，但不可验证。
2. 纯规则可解释，但知识边界不够准确。
```

图片建议：

- 架构图：
  ```text
  Parser → CourseIR → AI Unit Extractor → Validator → Relation Builder → Note Generator → Workspace
  ```

---

## 第 15 页：下一步计划

标题：

```text
下一步：从单份课件走向课程级知识库
```

页面文字：

```text
后续重点：

1. 多课件知识库
   - 支持一门课多份课件
   - 自动合并重复知识点
   - 建立跨讲次知识图谱

2. 更强的知识关系抽取
   - LLM 参与 relation extraction
   - 支持人工修正图谱
   - 支持关系置信度

3. 更完整的学习输出
   - 自测题
   - Anki 卡片
   - 错题提醒
   - 复习路径推荐

4. 更强的可信度系统
   - 局部遗漏检测
   - 局部重生成
   - 每段笔记证据链展示
```

图片建议：

- 时间轴：
  ```text
  MVP → Multi-lecture KB → Knowledge Graph Review → Personalized Learning
  ```

---

## 第 16 页：总结

标题：

```text
CourseWeaver 的一句话价值
```

页面文字：

```text
CourseWeaver 把课程课件从静态展示材料，转化为可学习、可追溯、可复用的知识网络。

它不是替代老师，也不是简单总结 PDF。

它的目标是帮助学生把课件变成：
- 能读懂的讲义
- 能跳转的知识图谱
- 能检查来源的证据链
- 能持续积累的课程知识库
```

收尾句：

```text
From course slides to structured learning.
```

图片建议：

- 放产品全景图。
- 放 GitHub 地址。
- 可以加二维码。

---

这一版里，第 4-6 页已经统一改成 **CourseWeaver 完整产品形态**，第 7 页之后才进入当前 MVP。这样叙事会更清楚：先让评委看到你要做的是一个完整系统，再证明你现在已经跑通了核心链路。
