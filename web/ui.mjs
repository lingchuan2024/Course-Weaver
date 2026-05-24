import {
  RELATION_LABELS,
  STATUS_LABELS,
  buildKnowledgeGraph,
  buildNoteMarkdown,
  escapeHtml,
  getPageBlocks,
  getPdfUrl,
  getReviewItems,
  indexProject,
  markdownToHtml,
  relationStats,
  searchNoteChunks,
  statusDistribution,
  summarizeProject,
  findFirstLearningPage,
} from "./app.mjs";

const state = {
  project: null,
  indexes: null,
  selectedPageId: null,
  selectedBlockId: null,
  activeSectionTitle: "",
  query: "",
  tool: "tree",
};

const els = {
  subtitle: document.querySelector("#project-subtitle"),
  fileInput: document.querySelector("#file-input"),
  loadDemo: document.querySelector("#load-demo"),
  downloadNote: document.querySelector("#download-note"),
  search: document.querySelector("#global-search"),
  metricPages: document.querySelector("#metric-pages"),
  metricChunks: document.querySelector("#metric-chunks"),
  metricUnits: document.querySelector("#metric-units"),
  metricCoverage: document.querySelector("#metric-coverage"),
  selectedPageTitle: document.querySelector("#selected-page-title"),
  pageIndicator: document.querySelector("#page-indicator"),
  prevPage: document.querySelector("#prev-page"),
  nextPage: document.querySelector("#next-page"),
  pdfFrame: document.querySelector("#pdf-frame"),
  pageList: document.querySelector("#page-list"),
  blockCount: document.querySelector("#block-count"),
  blockList: document.querySelector("#block-list"),
  coverageMini: document.querySelector("#coverage-mini"),
  noteContent: document.querySelector("#note-content"),
  toolTabs: [...document.querySelectorAll(".tool-tab")],
  toolContent: document.querySelector("#tool-content"),
  emptyTemplate: document.querySelector("#empty-state-template"),
};

const STATUS_COLORS = {
  covered: "#256f4c",
  merged: "#2f5f9f",
  appendix: "#6252a2",
  ignored: "#a0a79d",
  uncertain: "#b7791f",
  missing: "#bd3154",
};

els.loadDemo.addEventListener("click", () => loadDemoProject());
els.fileInput.addEventListener("change", handleProjectFile);
els.downloadNote.addEventListener("click", downloadCurrentNote);
els.search.addEventListener("input", (event) => {
  state.query = event.target.value;
  renderNote();
  renderTool();
});
els.prevPage.addEventListener("click", () => movePage(-1));
els.nextPage.addEventListener("click", () => movePage(1));
els.noteContent.addEventListener("scroll", updateActiveSectionFromScroll, { passive: true });
for (const tab of els.toolTabs) {
  tab.addEventListener("click", () => setTool(tab.dataset.tool));
}

loadDemoProject({ silent: true });

async function loadDemoProject({ silent = false } = {}) {
  try {
    const project = await fetchFirstProject([
      "/examples/lecture3-deepseek/ir/project.json",
      "/output/lecture3-deepseek/ir/project.json",
      "/output/lecture3/ir/project.json",
    ]);
    setProject(project);
  } catch (error) {
    showEmpty(silent ? "" : `Demo unavailable: ${error.message}`);
  }
}

async function fetchFirstProject(urls) {
  const errors = [];
  for (const url of urls) {
    try {
      const response = await fetch(url, { cache: "no-store" });
      if (!response.ok) throw new Error(`${url}: HTTP ${response.status}`);
      return await response.json();
    } catch (error) {
      errors.push(error.message);
    }
  }
  throw new Error(errors.join("; "));
}

function handleProjectFile(event) {
  const file = event.target.files?.[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = () => {
    try {
      setProject(JSON.parse(reader.result));
    } catch (error) {
      showEmpty(`Invalid project.json: ${error.message}`);
    }
  };
  reader.readAsText(file, "utf-8");
}

function setProject(project) {
  state.project = project;
  state.indexes = indexProject(project);
  state.selectedPageId = findFirstLearningPage(project);
  state.selectedBlockId = null;
  state.activeSectionTitle = "";
  state.query = "";
  state.tool = "tree";
  els.search.value = "";
  renderAll();
}

function renderAll() {
  renderMetrics();
  renderSource();
  renderNote();
  renderTool();
  updateToolTabs();
}

function renderMetrics() {
  const summary = summarizeProject(state.project);
  const rels = relationStats(state.project);
  els.subtitle.textContent = `${summary.title} · ${rels.total} 条知识关系`;
  els.metricPages.textContent = summary.pages;
  els.metricChunks.textContent = summary.chunks;
  els.metricUnits.textContent = summary.units;
  els.metricCoverage.textContent = `${summary.coverageRate}%`;

  const distribution = statusDistribution(state.project);
  const total = Object.values(distribution).reduce((sum, value) => sum + value, 0) || 1;
  els.coverageMini.innerHTML = `
    <div class="coverage-line">
      ${Object.entries(distribution)
        .filter(([, count]) => count > 0)
        .map(([status, count]) => {
          const width = (count / total) * 100;
          return `<i title="${STATUS_LABELS[status]} ${count}" style="width:${width}%;background:${STATUS_COLORS[status]}"></i>`;
        })
        .join("")}
    </div>
    <span>${summary.covered + summary.merged}/${summary.validBlocks} 已进入笔记</span>
  `;
}

function renderSource() {
  const page = currentPage();
  if (!page) return;
  const pages = state.project.pages;
  const blocks = getPageBlocks(state.project, page.page_id, state.indexes);

  els.selectedPageTitle.textContent = `课件原文 · 第 ${page.page_number} 页`;
  els.pageIndicator.textContent = `${page.page_number} / ${pages.length}`;
  els.prevPage.disabled = page.page_number <= 1;
  els.nextPage.disabled = page.page_number >= pages.length;
  els.pdfFrame.src = getPdfUrl(state.project, page.page_number);
  els.blockCount.textContent = `${blocks.length} blocks`;

  els.pageList.innerHTML = pages
    .map((item) => `
      <button class="page-dot ${item.page_id === page.page_id ? "active" : ""}" data-page-id="${item.page_id}" type="button">
        ${item.page_number}
      </button>
    `)
    .join("");
  els.pageList.querySelectorAll(".page-dot").forEach((button) => {
    button.addEventListener("click", () => {
      state.selectedPageId = button.dataset.pageId;
      state.selectedBlockId = null;
      renderSource();
      renderTool();
    });
  });

  els.blockList.innerHTML = blocks
    .map((block) => {
      const coverage = state.indexes.coverageByBlock.get(block.block_id);
      return `
        <button class="source-block ${block.block_id === state.selectedBlockId ? "active" : ""}" data-block-id="${block.block_id}" type="button">
          <span>${escapeHtml(block.block_id)}</span>
          <strong>${escapeHtml(block.text || "(empty)")}</strong>
          <em>${escapeHtml(block.block_type)} · ${STATUS_LABELS[coverage?.status] || "未检查"}</em>
        </button>
      `;
    })
    .join("");
  els.blockList.querySelectorAll(".source-block").forEach((button) => {
    button.addEventListener("click", () => selectBlock(button.dataset.blockId));
  });
}

function renderNote() {
  if (!state.project) return;
  const chunks = searchNoteChunks(state.project, state.query);
  els.noteContent.innerHTML = chunks
    .map((chunk) => {
      const chips = (chunk.source_blocks || [])
        .slice(0, 12)
        .map((blockId) => `<button class="source-chip" data-block-id="${blockId}" type="button">${escapeHtml(blockId)}</button>`)
        .join("");
      return `
        <section id="note-${escapeHtml(chunk.chunk_id)}" class="note-section" data-section-title="${escapeHtml(chunk.section_title)}">
          <div class="markdown">${markdownToHtml(chunk.content)}</div>
          <div class="source-row">${chips}</div>
        </section>
      `;
    })
    .join("") || emptyMarkup("没有匹配的笔记");

  els.noteContent.querySelectorAll(".source-chip").forEach((chip) => {
    chip.addEventListener("click", () => selectBlock(chip.dataset.blockId));
  });
  updateActiveSectionFromScroll();
}

function renderTool() {
  if (!state.project) return;
  if (state.tool === "trace") {
    renderTrace();
  } else if (state.tool === "review") {
    renderReview();
  } else {
    renderKnowledgeTree();
  }
}

function renderKnowledgeTree() {
  const query = state.query.trim().toLowerCase();
  const graph = buildKnowledgeGraph(state.project);
  const visibleNodes = graph.nodes.filter((node) => {
    if (!query) return true;
    return [node.title, ...node.units.map((unit) => unit.name), ...node.relations.map((relation) => relation.target_label)]
      .some((value) => String(value).toLowerCase().includes(query));
  });
  const visibleIds = new Set(visibleNodes.map((node) => node.id));
  const visibleEdges = graph.edges.filter((edge) => visibleIds.has(edge.source_id) && visibleIds.has(edge.target_id));
  const viewWidth = graph.width;
  const viewHeight = graph.height;

  els.toolContent.innerHTML = `
    <div class="tool-summary">
      <strong>知识关系图</strong>
      <span id="learning-progress-text">${learningProgressText(visibleNodes)}</span>
    </div>
    <div class="graph-legend" aria-label="关系颜色图例">
      ${renderGraphLegend()}
    </div>
    <div class="graph-viewport" role="group" aria-label="知识关系图">
      <div class="knowledge-graph-canvas" style="width:${viewWidth}px;height:${viewHeight}px">
        <svg class="graph-edge-svg" viewBox="0 0 ${viewWidth} ${viewHeight}" aria-hidden="true">
          ${visibleEdges.map(renderGraphEdge).join("")}
        </svg>
        ${visibleEdges.map(renderGraphEdgeLabel).join("")}
        ${visibleNodes.map(renderGraphNode).join("") || emptyMarkup("没有匹配的知识节点")}
      </div>
    </div>
  `;

  els.toolContent.querySelectorAll("[data-jump-title]").forEach((button) => {
    button.addEventListener("click", () => scrollToNoteSection(button.dataset.jumpTitle));
  });
  updateGraphProgressClasses();
}

function renderGraphNode(node) {
  const topicItems = [
    ...node.parentTopics.slice(0, 2).map((topic) => `<span class="topic-chip">${escapeHtml(topic)}</span>`),
    ...node.learningStages.slice(0, 1).map((stage) => `<span class="stage-chip">${escapeHtml(stageLabel(stage))}</span>`),
  ].join("");

  return `
    <button
      class="graph-node"
      style="left:${node.x}px;top:${node.y}px;width:${node.width}px;height:${node.height}px"
      data-jump-title="${escapeHtml(node.title)}"
      data-section-title="${escapeHtml(node.title)}"
      data-section-index="${node.index}"
      title="${escapeHtml(node.title)}"
      type="button"
    >
      <span class="graph-node-index">${String(node.index).padStart(2, "0")}</span>
      <strong>${escapeHtml(shortGraphTitle(node.title))}</strong>
      ${topicItems ? `<em>${topicItems}</em>` : ""}
    </button>
  `;
}

function renderGraphEdge(edge) {
  return `<path class="graph-edge edge-${edge.relation_type}" d="${edge.path}" />`;
}

function renderGraphEdgeLabel(edge) {
  if (edge.relation_type === "next") return "";
  return `
    <button
      class="graph-edge-label edge-${edge.relation_type}"
      style="left:${edge.labelX}px;top:${edge.labelY}px"
      data-jump-title="${escapeHtml(edge.target_label)}"
      title="${escapeHtml(edge.reason || edge.relation_type)}"
      type="button"
    >${escapeHtml(RELATION_LABELS[edge.relation_type] || edge.relation_type)}</button>
  `;
}

function renderGraphLegend() {
  return ["next", "foundation_for", "contrasts_with", "parallel_with", "example_of", "regularizes", "supports"]
    .map((type) => `<span class="legend-item edge-${type}"><i></i>${escapeHtml(RELATION_LABELS[type] || type)}</span>`)
    .join("");
}

function shortGraphTitle(title) {
  const clean = String(title || "");
  return clean.length > 48 ? `${clean.slice(0, 47)}…` : clean;
}

function stageLabel(stage) {
  const labels = {
    orientation: "导览",
    foundation: "基础",
    modeling: "建模",
    estimation: "估计",
    analysis: "分析",
    diagnosis: "诊断",
    regularization: "正则化",
    statistical_view: "统计视角",
    review: "复习",
    exercise: "练习",
  };
  return labels[stage] || stage;
}

function renderTrace() {
  const block = state.selectedBlockId ? state.indexes.blocksById.get(state.selectedBlockId) : null;
  if (!block) {
    els.toolContent.innerHTML = emptyMarkup("点击笔记来源或解析层 block 查看溯源");
    return;
  }
  const coverage = state.indexes.coverageByBlock.get(block.block_id);
  const units = state.indexes.unitsByBlock.get(block.block_id) || [];
  els.toolContent.innerHTML = `
    <div class="trace-card">
      <div class="trace-head">
        <strong>${escapeHtml(block.block_id)}</strong>
        <span class="status-pill status-${coverage?.status || "ignored"}">${STATUS_LABELS[coverage?.status] || "未检查"}</span>
      </div>
      <p class="trace-meta">第 ${block.page_number} 页 · ${escapeHtml(block.block_type)}</p>
      <blockquote>${escapeHtml(block.text || "")}</blockquote>
      <div class="trace-field">
        <span>进入笔记</span>
        <strong>${escapeHtml(coverage?.note_location || coverage?.comment || "暂无")}</strong>
      </div>
      <div class="trace-field">
        <span>关联知识点</span>
        <div>${units.map((unit) => `<em>${escapeHtml(unit.name)}</em>`).join("") || "暂无"}</div>
      </div>
    </div>
  `;
}

function renderReview() {
  const items = getReviewItems(state.project, { query: state.query }).slice(0, 120);
  const urgent = items.filter((item) => item.status === "missing" || item.status === "uncertain").length;
  els.toolContent.innerHTML = `
    <div class="tool-summary">
      <strong>漏洞检查</strong>
      <span>${urgent} 条需要优先复核</span>
    </div>
    <div class="review-list">
      ${items.map(renderReviewItem).join("") || emptyMarkup("没有匹配的检查项")}
    </div>
  `;
  els.toolContent.querySelectorAll(".review-item").forEach((button) => {
    button.addEventListener("click", () => selectBlock(button.dataset.blockId));
  });
}

function renderReviewItem(item) {
  return `
    <button class="review-item ${item.block_id === state.selectedBlockId ? "active" : ""}" data-block-id="${item.block_id}" type="button">
      <span class="status-pill status-${item.status}">${STATUS_LABELS[item.status] || item.status}</span>
      <strong>${escapeHtml(item.block_id)}</strong>
      <p>第 ${item.page_number} 页 · ${escapeHtml(item.comment || item.block_type)}</p>
    </button>
  `;
}

function selectBlock(blockId) {
  const block = state.indexes.blocksById.get(blockId);
  if (!block) return;
  state.selectedBlockId = blockId;
  state.selectedPageId = block.page_id;
  state.tool = "trace";
  renderSource();
  renderTool();
  updateToolTabs();
}

function movePage(delta) {
  const pages = state.project?.pages || [];
  const currentIndex = pages.findIndex((page) => page.page_id === state.selectedPageId);
  const next = pages[currentIndex + delta];
  if (!next) return;
  state.selectedPageId = next.page_id;
  state.selectedBlockId = null;
  renderSource();
  renderTool();
}

function currentPage() {
  return state.project?.pages.find((page) => page.page_id === state.selectedPageId) || state.project?.pages[0] || null;
}

function setTool(tool) {
  state.tool = tool;
  updateToolTabs();
  renderTool();
}

function updateToolTabs() {
  els.toolTabs.forEach((tab) => tab.classList.toggle("active", tab.dataset.tool === state.tool));
}

function scrollToNoteSection(title) {
  const target = [...els.noteContent.querySelectorAll(".note-section")]
    .find((section) => section.dataset.sectionTitle === title);
  if (target) {
    target.scrollIntoView({ behavior: "smooth", block: "start" });
    state.activeSectionTitle = title;
    updateGraphProgressClasses();
  }
}

function updateActiveSectionFromScroll() {
  if (!state.project) return;
  const sections = [...els.noteContent.querySelectorAll(".note-section")];
  if (!sections.length) return;
  const containerTop = els.noteContent.getBoundingClientRect().top;
  let active = sections[0];
  for (const section of sections) {
    const offset = section.getBoundingClientRect().top - containerTop;
    if (offset <= 120) active = section;
  }
  const title = active.dataset.sectionTitle || "";
  if (title === state.activeSectionTitle) return;
  state.activeSectionTitle = title;
  updateGraphProgressClasses();
}

function updateGraphProgressClasses() {
  const nodes = [...els.toolContent.querySelectorAll(".graph-node")];
  if (!nodes.length) return;
  const activeIndex = nodes.findIndex((node) => node.dataset.sectionTitle === state.activeSectionTitle);
  nodes.forEach((node, index) => {
    node.classList.toggle("active", index === activeIndex);
    node.classList.toggle("completed", activeIndex >= 0 && index < activeIndex);
    node.classList.toggle("upcoming", activeIndex < 0 || index > activeIndex);
  });
  const progressText = els.toolContent.querySelector("#learning-progress-text");
  if (progressText) progressText.textContent = learningProgressText(nodes);
}

function learningProgressText(treeOrNodes) {
  const total = treeOrNodes.length;
  const titles = (state.project?.note_plan || []).map((section) => section.section_title);
  const activeIndex = titles.indexOf(state.activeSectionTitle);
  if (activeIndex < 0) return `${total} 个节点`;
  return `${Math.min(activeIndex + 1, total)} / ${total} 正在学习`;
}

function downloadCurrentNote() {
  if (!state.project) return;
  const markdown = buildNoteMarkdown(state.project);
  const blob = new Blob([markdown], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `${state.project.project_id || "courseweaver"}-notes.md`;
  document.body.append(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function showEmpty(message = "") {
  els.pdfFrame.removeAttribute("src");
  els.pageList.innerHTML = "";
  els.blockList.innerHTML = "";
  els.noteContent.innerHTML = message ? emptyMarkup(message) : els.emptyTemplate.innerHTML;
  els.toolContent.innerHTML = els.emptyTemplate.innerHTML;
}

function emptyMarkup(text) {
  return `<div class="empty-state"><div class="empty-glyph" aria-hidden="true">◇</div><h2>${escapeHtml(text)}</h2></div>`;
}
