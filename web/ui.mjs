import {
  RELATION_LABELS,
  STATUS_LABELS,
  buildKnowledgeTree,
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
for (const tab of els.toolTabs) {
  tab.addEventListener("click", () => setTool(tab.dataset.tool));
}

loadDemoProject({ silent: true });

async function loadDemoProject({ silent = false } = {}) {
  try {
    const project = await fetchFirstProject([
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
  const tree = buildKnowledgeTree(state.project).filter((node) => {
    if (!query) return true;
    return [node.title, ...node.units.map((unit) => unit.name), ...node.relations.map((relation) => relation.target_label)]
      .some((value) => String(value).toLowerCase().includes(query));
  });

  els.toolContent.innerHTML = `
    <div class="tool-summary">
      <strong>课程知识树</strong>
      <span>${tree.length} 个主干节点</span>
    </div>
    <div class="tree-map" role="tree">
      <div class="tree-root">
        <strong>Lecture</strong>
        <span>主线</span>
      </div>
      ${tree.map(renderTreeNode).join("") || emptyMarkup("没有匹配的知识节点")}
    </div>
  `;

  els.toolContent.querySelectorAll("[data-jump-title]").forEach((button) => {
    button.addEventListener("click", () => scrollToNoteSection(button.dataset.jumpTitle));
  });
}

function renderTreeNode(node) {
  const unitItems = node.units
    .slice(0, 8)
    .map((unit) => `<button class="leaf-node" title="${escapeHtml(unit.summary || unit.name)}" type="button">${escapeHtml(unit.name)}</button>`)
    .join("");
  const relationItems = node.relations
    .filter((relation) => relation.relation_type !== "next")
    .slice(0, 6)
    .map((relation) => `
      <span class="relation-edge">
        <i>${RELATION_LABELS[relation.relation_type] || relation.relation_type}</i>
        <button data-jump-title="${escapeHtml(relation.target_label)}" type="button">${escapeHtml(relation.target_label)}</button>
      </span>
    `)
    .join("");

  return `
    <section class="branch-node" role="treeitem">
      <div class="branch-stem" aria-hidden="true"></div>
      <div class="branch-card">
        <span class="branch-index">${String(node.index).padStart(2, "0")}</span>
        <button class="branch-title" data-jump-title="${escapeHtml(node.title)}" type="button">${escapeHtml(node.title)}</button>
        <div class="unit-branches">${unitItems || '<span class="leaf-node muted-leaf">暂无知识单元</span>'}</div>
        ${relationItems ? `<div class="relation-branches">${relationItems}</div>` : ""}
      </div>
    </section>
  `;
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
  if (target) target.scrollIntoView({ behavior: "smooth", block: "start" });
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
