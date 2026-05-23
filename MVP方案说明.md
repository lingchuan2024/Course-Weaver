# CourseWeaver MVP 方案说明

## 1. MVP 目标

CourseWeaver 的 MVP 不应该被定义成“能把 PDF 总结成 Markdown”，因为这和直接把课件丢给大模型生成笔记没有本质区别。

本阶段真正要证明的是：

> CourseWeaver 可以把课件先解析成可追溯的结构化知识，再生成一份更完整、更可信、更适合学习的讲义式笔记。

也就是说，MVP 要证明三件事：

1. **不是普通总结**：系统不是按页压缩内容，而是抽取知识单元并跨页合并。
2. **不是黑盒生成**：每个核心知识点、公式、算法、图示解释都能回到原课件页码。
3. **不是只追求好看**：系统有覆盖报告，能说明哪些内容已覆盖、哪些被合并、哪些疑似遗漏。

比赛阶段不需要做成完整商业产品，但必须跑通一条足够有说服力的链路：

```text
PDF 课件
→ 页面与 block 解析
→ 知识单元抽取
→ 跨页合并
→ 讲义式主笔记
→ 来源索引
→ 覆盖报告
```

MVP 的核心展示效果应该是：同一份课件，直接 prompt 生成的笔记像“摘要”，CourseWeaver 生成的笔记像“助教重新讲了一遍课”，并且能检查来源和遗漏。

---

## 2. 当前阶段应该做到什么程度

为了在开源大赛中体现可行性，MVP 不需要覆盖所有课程、所有文件类型、所有交互形态。它应该聚焦一个高价值场景，把效果做扎实。

推荐目标：

> 支持上传一份 30-80 页的计算机类 PDF 课件，生成一套 Markdown 学习包，包括讲义式主笔记、概念表、公式/算法解释、来源索引和覆盖报告。

推荐优先选择以下课件类型：

| 课件类型 | 适合原因 |
|---|---|
| 算法课 | 概念、伪代码、复杂度、证明、例子都比较典型 |
| 操作系统课 | 架构图、机制解释、对比表多，适合展示图文重构 |
| 机器学习课 | 公式多，适合展示公式解释与来源追踪 |
| 数据库课 | 概念关系清晰，适合展示知识单元合并 |

不建议 MVP 一开始覆盖所有学科。比赛评审更关心项目有没有清晰问题、可验证方案和可运行原型，而不是支持范围写得很大。

---

## 3. MVP 必须交付的功能

### 3.1 PDF 输入与页面解析

MVP 只支持 PDF，暂时不支持 PPT、Word、图片压缩包和网页。

最低要求：

1. 上传或指定一个 PDF 文件。
2. 将 PDF 渲染为逐页图片。
3. 提取每页文本 block。
4. 保存页码、block id、block 类型、文本内容、bbox、reading order。

MVP 中 block 类型可以先收敛为：

```text
title
text
formula
figure
table
code_or_algorithm
noise
unknown
```

不要求第一版 block 分类完全准确，但必须保留原始证据，方便后续校正。

### 3.2 CourseIR 中间表示

CourseIR 是项目区别于普通 prompt 总结的关键。MVP 至少要生成这些结构化文件：

```text
output/
├── pages.json
├── blocks.json
├── knowledge_units.json
├── note_plan.json
├── note_chunks.json
└── coverage_items.json
```

每个 knowledge unit 至少包含：

```json
{
  "unit_id": "U_001",
  "name": "动态规划的重叠子问题",
  "type": "concept",
  "summary": "同一类子问题在递归过程中反复出现，因此可以缓存结果。",
  "source_pages": [8, 9],
  "source_blocks": ["p008_b003", "p009_b001"],
  "importance": "core",
  "confidence": 0.86
}
```

MVP 不需要做复杂知识图谱可视化，但必须保留知识单元和来源 block 的映射。

### 3.3 知识单元抽取与跨页合并

直接 prompt 总结通常是按文档顺序生成文字，容易漏掉跨页展开的知识点。MVP 必须展示 CourseWeaver 的重构能力。

最低要求：

1. 逐页抽取知识单元。
2. 将同名、同主题或明显连续讲解的知识点跨页合并。
3. 对每个合并后的知识点保留来源页码。
4. 区分核心知识点、补充知识点和疑似噪声。

例如，课件中可能有：

```text
p.10：BFS 的动机
p.11：BFS 伪代码
p.12：BFS 运行过程
p.13：BFS 正确性
p.14：BFS 复杂度
```

MVP 输出不应该是五页摘要，而应该合并成一个完整的 BFS 知识单元，并在主笔记中按“解决什么问题、如何运行、为什么正确、复杂度是多少”的顺序讲清楚。

### 3.4 Note Director 与讲义式主笔记

MVP 的主笔记必须避免模板化。评审和用户看到的第一印象应该是“这份笔记真的更适合学习”。

主笔记要求：

1. 先讲问题和动机，再讲定义。
2. 先讲直觉，再讲公式。
3. 算法先讲目标和核心思路，再解释伪代码。
4. 公式必须解释符号含义。
5. 图示必须解释图想表达的关系，而不是只写“图中展示了……”。
6. 每个核心小节带轻量来源标注，例如 `[p.12-p.14]`。
7. 对容易混淆的概念给出对比或提醒。

MVP 中可以先不做非常复杂的自动学习路径规划，但应该有一个明确的 `note_plan.json`，让系统先规划再生成，而不是一次性写全文。

### 3.5 结构化复习包

MVP 至少输出三个复习文件：

```text
03_concepts.md
04_formulas_and_algorithms.md
05_common_mistakes.md
```

其中：

| 文件 | 内容要求 |
|---|---|
| `03_concepts.md` | 核心概念、简明解释、来源页码 |
| `04_formulas_and_algorithms.md` | 公式符号解释、算法目标、输入输出、复杂度 |
| `05_common_mistakes.md` | 易混淆点、常见误解、复习提醒 |

自测题、Anki 卡片、考试押题版可以放到 7、8 月之后。

### 3.6 来源索引

MVP 必须生成来源索引，因为这是可信性的核心。

输出文件：

```text
06_source_index.md
```

最低要求：

```markdown
| 知识点 | 类型 | 来源页码 | 来源 block |
|---|---|---|---|
| 重叠子问题 | concept | p.8, p.9 | p008_b003, p009_b001 |
| 状态转移方程 | formula | p.12 | p012_b002 |
| BFS 队列机制 | algorithm | p.20-p.22 | p020_b004, p021_b001 |
```

如果来得及，可以在 Markdown 中支持点击页码跳转到本地 page image；如果时间紧，先用清晰的页码和 block id 即可。

### 3.7 覆盖报告

覆盖报告是 MVP 最重要的差异化交付之一。

输出文件：

```text
07_coverage_report.md
```

每个有效 block 必须有一个状态：

| 状态 | 含义 |
|---|---|
| covered | 已进入主笔记或复习包 |
| merged | 已合并进其他知识点 |
| appendix | 放入结构化复习材料 |
| ignored | 确认是页码、装饰、重复标题等噪声 |
| uncertain | 系统不确定，需要人工确认 |
| missing | 疑似遗漏 |

覆盖报告至少包含：

1. 总 block 数。
2. 有效 block 数。
3. covered / merged / appendix / ignored / uncertain / missing 数量。
4. 逐页覆盖表。
5. 疑似遗漏列表。

这一项能直接拉开和普通 prompt 生成笔记的差距：普通总结很难说明自己没有漏，CourseWeaver 可以把遗漏变成可检查对象。

---

## 4. MVP 输出目录

建议 MVP 的最终输出目录固定为：

```text
output/<project_id>/
├── ir/
│   ├── pages.json
│   ├── blocks.json
│   ├── knowledge_units.json
│   ├── note_plan.json
│   ├── note_chunks.json
│   └── coverage_items.json
├── assets/
│   ├── pages/
│   └── crops/
├── notes/
│   ├── 00_overview.md
│   ├── 01_lecture_notes.md
│   ├── 03_concepts.md
│   ├── 04_formulas_and_algorithms.md
│   ├── 05_common_mistakes.md
│   ├── 06_source_index.md
│   └── 07_coverage_report.md
└── report/
    └── comparison_with_prompt.md
```

`comparison_with_prompt.md` 建议专门用于比赛展示，内容包括：

1. 直接 prompt 生成笔记的结果片段。
2. CourseWeaver 生成结果片段。
3. 对比维度：结构完整性、公式解释、来源追踪、覆盖检查、可复习性。
4. 结论：CourseWeaver 的优势来自流程和中间表示，而不是单次提示词。

---

## 5. 大赛演示闭环

比赛展示时，建议准备一份固定 demo，而不是现场随便上传未知课件。

推荐演示流程：

1. 选择一份 30-50 页的算法或机器学习 PDF。
2. 展示原课件中几个典型难点：公式、伪代码、图、跨页知识点。
3. 展示直接 prompt 生成的笔记，指出它的问题：按页总结、缺少来源、公式解释不足、无法确认是否遗漏。
4. 运行 CourseWeaver pipeline。
5. 展示 CourseIR：knowledge units、source blocks、note plan。
6. 展示生成的讲义式主笔记。
7. 点击或展示某个知识点的来源页码。
8. 展示覆盖报告，说明疑似遗漏和 uncertain 项。
9. 总结：系统不是替用户“写得更漂亮”，而是让课件学习材料变得可追溯、可检查、可迭代。

最有说服力的 demo 点可以是：

| 展示点 | 评审能看到的价值 |
|---|---|
| 跨页知识点合并 | 不是逐页摘要，而是知识重构 |
| 公式符号解释 | 适合学生自学 |
| 算法目标 + 伪代码解释 + 复杂度 | 比普通总结更像助教讲解 |
| 来源页码和 block id | 可信、可核查 |
| 覆盖报告 | 能发现遗漏，而不是假装完整 |

---

## 6. 技术实现建议

MVP 技术路线应优先稳定，不要过早引入复杂工作流系统。

推荐结构：

```text
apps/backend/
├── pipeline/
│   ├── parse_pdf.py
│   ├── build_blocks.py
│   ├── extract_units.py
│   ├── merge_units.py
│   ├── plan_notes.py
│   ├── generate_notes.py
│   ├── verify_coverage.py
│   └── export_markdown.py
├── models/
│   ├── page_ir.py
│   ├── block.py
│   ├── knowledge_unit.py
│   ├── note_plan.py
│   └── coverage.py
├── llm/
│   ├── client.py
│   ├── prompts.py
│   └── schemas.py
└── run_pipeline.py
```

第一阶段可以先做 CLI：

```bash
python run_pipeline.py examples/dp.pdf --out output/dp
```

CLI 跑通以后，再补一个简单 Web UI。不要一开始就把精力放在复杂前端上。

推荐技术选型：

| 模块 | MVP 选择 |
|---|---|
| PDF 渲染 | PyMuPDF |
| 文本与布局解析 | PyMuPDF 起步，后续接 Docling / MinerU |
| 数据模型 | Pydantic |
| 后端接口 | FastAPI，可后置 |
| 前端 | React / Next.js，可后置 |
| 存储 | 本地 JSON + 文件目录 |
| 导出 | Markdown |
| LLM 调用 | 结构化 JSON 输出 + schema 校验 |

---

## 7. 验收标准

MVP 可以按以下标准验收。

### 7.1 功能验收

1. 能处理一份 30-80 页 PDF 课件。
2. 能生成页面图片、blocks、knowledge units、note plan 和 coverage items。
3. 能生成自然讲义式主笔记。
4. 主笔记中的核心知识点带来源页码。
5. 能输出概念表、公式/算法解释、易错点。
6. 能输出来源索引。
7. 能输出覆盖报告。
8. 能标记 uncertain 和 missing。
9. 能导出完整 Markdown 学习包。

### 7.2 质量验收

1. 核心知识点覆盖率达到 80% 以上。
2. 公式和算法覆盖率达到 80% 以上。
3. 抽查 20 个来源标注，正确率达到 85% 以上。
4. 主笔记不是逐页摘要，而是按知识点组织。
5. 主笔记中至少包含 3 个“直觉解释 + 形式表达 + 例子/提醒”的完整讲解段落。
6. 与直接 prompt 生成结果相比，至少能指出 3 类明确优势。

### 7.3 展示验收

1. 有一份固定 demo PDF。
2. 有一份直接 prompt baseline。
3. 有 CourseWeaver 生成的完整输出。
4. 有对比报告。
5. 有 README 或文档说明如何复现。

---

## 8. 暂不纳入 MVP 的内容

以下内容可以写进路线图，但不应卡住 MVP：

1. PPT 支持。
2. Word / 图片课件支持。
3. 多人协作。
4. 用户账号系统。
5. 完整数据库与权限系统。
6. 长期个人知识库。
7. Anki 卡片自动同步。
8. 自动复习计划。
9. 知识图谱可视化。
10. 多轮聊天问答。
11. 局部手动编辑后自动重生成。
12. 移动端适配。
13. 模型微调。
14. 多课程知识融合。

这些功能都合理，但它们证明的是“产品完整度”，不是 MVP 阶段最关键的“技术路线可行性”。

---

## 9. 7、8 月可以继续做的工作

### 7 月：从可运行原型到可用产品

7 月重点是把 MVP 从脚本能力提升到可交互产品。

建议任务：

1. 做一个三栏 Web 界面：左侧 PDF，中心笔记，右侧知识单元/覆盖报告。
2. 支持点击笔记来源页码跳转到 PDF 页。
3. 支持点击覆盖报告中的 uncertain / missing 项定位到原课件。
4. 支持用户把 block 标记为 ignored、covered、appendix。
5. 支持修改单个 knowledge unit 的解释。
6. 支持重新生成某个小节，而不是整份笔记重跑。
7. 引入 SQLite 或 PostgreSQL，替代纯 JSON 文件。
8. 沉淀 5-10 份公开课件作为评测集。

7 月的目标不是增加很多新功能，而是让系统从“能跑”变成“能用、能查、能修”。

### 8 月：从单点 demo 到系统能力

8 月重点是增强泛化能力和评价体系。

建议任务：

1. 支持 PPT/PPTX 解析。
2. 接入更强的文档解析能力，如 Docling 或 MinerU。
3. 增强图表解释，尤其是流程图、架构图、曲线图。
4. 增加自测题、问答、考前速览版。
5. 增加 Anki 卡片导出。
6. 建立自动评测脚本：覆盖率、来源准确率、unsupported claim rate。
7. 增加多种笔记风格：讲义式、考试式、极简式、完整式。
8. 做公开 demo 页面或部署版本。
9. 完善开源文档：安装、运行、架构、贡献指南、示例输出。

8 月的目标是让项目不只适合比赛展示，也能吸引开源用户试用和贡献。

---

## 10. 推荐开发优先级

如果时间有限，优先级应该是：

```text
P0：PDF → blocks → knowledge_units → lecture_notes → source_index → coverage_report
P1：公式/算法解释质量、跨页合并、对比报告
P2：简单 Web 预览、来源跳转、coverage 定位
P3：人工修正、局部重生成、复习题、Anki
P4：PPT 支持、知识图谱、长期知识库、多课程融合
```

比赛前最重要的是 P0 和 P1。P2 如果能做，会明显增强观感。P3 和 P4 可以放到 7、8 月。

---

## 11. 最小成功定义

CourseWeaver MVP 成功的标准不是“生成了一份漂亮 Markdown”，而是：

> 给定一份真实课件，系统能产出一份比直接 prompt 更适合学习的讲义式笔记，并且能用来源索引和覆盖报告证明这份笔记不是黑盒生成。

如果 MVP 只能保留一个核心卖点，应该保留：

```text
结构化 CourseIR + 来源追踪 + 覆盖报告
```

如果 MVP 只能展示一个效果，应该展示：

```text
同一份课件下，CourseWeaver 相比直接 prompt 的笔记更完整、更可追溯、更适合学生复习。
```

