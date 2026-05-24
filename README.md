# CourseWeaver MVP

CourseWeaver MVP 是一个离线课件笔记生成原型。它不直接把 PDF 丢给大模型做一次性总结，而是先生成可追溯的 CourseIR，再导出讲义式笔记、结构化复习包、来源索引和覆盖报告。

## 当前能力

- 解析 PDF，提取带页码、bbox、reading order 的 blocks。
- 生成 `pages.json`、`blocks.json`、`knowledge_units.json`、`note_plan.json`、`note_chunks.json`、`coverage_items.json`。
- 按课件标题聚合知识单元，生成讲义式 Markdown 主笔记。
- 可选调用 DeepSeek 将结构化草稿改写成更自然的讲义正文。
- 输出概念表、公式/算法表、易错点、来源索引和覆盖报告。
- 标记 `covered`、`merged`、`ignored`、`missing` 等覆盖状态。

## 环境要求

Python 3.12 已验证。MVP 依赖：

- `pydantic`
- Poppler 命令行工具中的 `pdftotext`

macOS 可通过 Homebrew 安装 Poppler：

```bash
brew install poppler
```

## 运行

离线启发式版本：

```bash
python3 run_pipeline.py lecture3.pdf --out output/lecture3
```

使用 DeepSeek 改写主笔记：

```bash
export DEEPSEEK_API_KEY="你的 DeepSeek API Key"
python3 run_pipeline.py lecture3.pdf \
  --out output/lecture3-deepseek \
  --use-llm \
  --llm-provider deepseek
```

也可以把 key 放在项目根目录的 `.env` 中，支持两种格式：

```text
DEEPSEEK_API_KEY=你的 DeepSeek API Key
```

或只放一行 key。`.env` 已加入 `.gitignore`，不要提交到仓库。

默认模型是 `deepseek-v4-pro`。也可以切换为更快的模型：

```bash
python3 run_pipeline.py lecture3.pdf \
  --out output/lecture3-deepseek \
  --use-llm \
  --llm-provider deepseek \
  --llm-model deepseek-v4-flash
```

使用 Kimi 改写主笔记：

```bash
export MOONSHOT_API_KEY="你的 Kimi / Moonshot API Key"
python3 run_pipeline.py lecture3.pdf \
  --out output/lecture3-kimi \
  --use-llm \
  --llm-provider kimi
```

Kimi 默认模型是 `kimi-k2.6`，也可以显式指定：

```bash
python3 run_pipeline.py lecture3.pdf \
  --out output/lecture3-kimi \
  --use-llm \
  --llm-provider kimi \
  --llm-model kimi-k2.6
```

成功后会生成：

```text
output/lecture3/
├── ir/
│   ├── pages.json
│   ├── blocks.json
│   ├── knowledge_units.json
│   ├── note_plan.json
│   ├── note_chunks.json
│   ├── coverage_items.json
│   └── project.json
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

## 测试

```bash
python3 -m unittest discover -s tests -v
```

## 当前限制

- LLM 改写只影响 `note_chunks` 的正文，不改变 CourseIR、来源 block 和 coverage 账本。
- PDF 解析依赖 `pdftotext -bbox-layout`，复杂公式的文本顺序可能不完美。
- 暂不支持 PPT、图片 OCR、局部重生成，以及由 LLM 直接抽取结构化知识图谱。

当前 LLM 接入使用官方 OpenAI-compatible Chat Completions API：

- DeepSeek: `https://api.deepseek.com/chat/completions`
- Kimi: `https://api.moonshot.ai/v1/chat/completions`

## 前端工作台

生成 `output/lecture3/ir/project.json` 后，启动静态服务器：

```bash
python3 -m http.server 8787
```

打开：

```text
http://localhost:8787/web/
```

前端会优先加载随仓库提交的 DeepSeek demo：`/examples/lecture3-deepseek/ir/project.json`。如果你本地重新生成过结果，也会回退读取 `/output/lecture3-deepseek/ir/project.json` 或 `/output/lecture3/ir/project.json`。也可以点击左上角导入任意 CourseWeaver 导出的 `project.json`。

新版界面按学习者工作台组织：

- 左侧：真实 PDF 课件预览、页码切换、可折叠的解析层 block 列表。
- 中间：DeepSeek/Kimi 生成的讲义式笔记，前端会渲染 Markdown 标题、列表、行内公式和公式块，并支持一键下载 Markdown。
- 右侧：知识树、溯源、漏洞三个工具页。

主笔记会根据 `project.relations` 自动加入“关系导读与对比总结”，用表格展示前置依赖、并列/对比知识点和例子关系，例如 Bias vs Variance、频率派 vs 贝叶斯、Ridge 的正则化视角 vs 贝叶斯视角。

知识树读取 `project.note_plan`、`project.knowledge_units` 和 `project.relations`，按“Lecture 根节点 -> 章节主干 -> 知识点叶子 -> 关系边”展示。`note_plan` 会先按学习阶段重排，再生成学习路径图。用户滚动中间笔记时，右侧路径图会自动高亮当前节点，已经读过的节点会标记为完成。`next` 表示学习顺序，`foundation_for`、`contrasts_with`、`regularizes`、`example_of` 等关系挂在对应章节节点下。溯源页用于查看选中 block 的原文、页码、进入笔记的位置和关联知识点。漏洞页优先展示 missing/uncertain，再展示 merged/ignored，作为人工复核清单。

前端重设计说明见 `docs/frontend_redesign.md`。

前端无构建依赖，核心逻辑测试：

```bash
node --test tests/frontend.test.mjs
```
