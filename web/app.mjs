export const STATUS_LABELS = {
  covered: "已写入",
  merged: "已合并",
  appendix: "附录",
  ignored: "已忽略",
  uncertain: "待复核",
  missing: "疑似遗漏",
};

export const RELATION_LABELS = {
  next: "下一节",
  parallel_with: "并列",
  foundation_for: "支撑",
  contrasts_with: "对比",
  regularizes: "约束",
  example_of: "例子",
  supports: "归属",
};

export function indexProject(project) {
  const blocksById = new Map(project.blocks.map((block) => [block.block_id, block]));
  const unitsById = new Map(project.knowledge_units.map((unit) => [unit.unit_id, unit]));
  const coverageByBlock = new Map(project.coverage_items.map((item) => [item.block_id, item]));
  const unitsByBlock = new Map();

  for (const unit of project.knowledge_units) {
    for (const blockId of unit.source_blocks || []) {
      if (!unitsByBlock.has(blockId)) unitsByBlock.set(blockId, []);
      unitsByBlock.get(blockId).push(unit);
    }
  }

  return { blocksById, unitsById, coverageByBlock, unitsByBlock };
}

export function getProjectTitle(project) {
  const firstTitle = project.blocks.find((block) => block.block_type === "title" && block.text);
  if (firstTitle) return firstTitle.text;
  return project.project_id || "CourseWeaver Project";
}

export function summarizeProject(project) {
  const summary = project.coverage_summary || {};
  const validBlocks = summary.valid_blocks ?? project.coverage_items.filter((item) => item.status !== "ignored").length;
  const covered = summary.covered ?? 0;
  const merged = summary.merged ?? 0;
  const missing = summary.missing ?? 0;
  const coverageRate = validBlocks === 0 ? 0 : Math.round(((covered + merged) / validBlocks) * 100);
  return {
    title: getProjectTitle(project),
    pages: project.pages.length,
    blocks: project.blocks.length,
    units: project.knowledge_units.length,
    chunks: project.note_chunks.length,
    validBlocks,
    covered,
    merged,
    missing,
    coverageRate,
  };
}

export function buildNoteMarkdown(project) {
  const title = getProjectTitle(project);
  const sections = project.note_chunks
    .map((chunk) => chunk.content.trim())
    .filter(Boolean);
  return [`# ${title} 讲义式笔记`, ...sections].join("\n\n").trim() + "\n";
}

export function getPdfUrl(project, pageNumber = 1) {
  const sourceFile = project.source_file || `${project.project_id || "lecture3"}.pdf`;
  const filename = String(sourceFile).split(/[\\/]/).pop();
  return `/${encodeURIComponent(filename)}#page=${pageNumber}&toolbar=0&navpanes=0`;
}

export function findFirstLearningPage(project) {
  const titleByPage = new Map();
  for (const block of project.blocks) {
    if (block.block_type === "title" && block.text) {
      if (!titleByPage.has(block.page_id)) titleByPage.set(block.page_id, []);
      titleByPage.get(block.page_id).push(block.text.toLowerCase());
    }
  }

  const page = project.pages.find((item) => {
    if (item.page_number <= 1) return false;
    const titles = titleByPage.get(item.page_id) || [];
    if (titles.some((title) => title === "outline" || title.includes("homework"))) return false;
    const blocks = item.blocks
      .map((blockId) => project.blocks.find((block) => block.block_id === blockId))
      .filter(Boolean);
    return blocks.some((block) => block.block_type !== "noise" && block.text && block.text.length > 16);
  });
  return page?.page_id || project.pages[0]?.page_id || null;
}

export function getPageBlocks(project, pageId, indexes = indexProject(project)) {
  const page = project.pages.find((item) => item.page_id === pageId);
  if (!page) return [];
  return page.blocks.map((blockId) => indexes.blocksById.get(blockId)).filter(Boolean);
}

export function statusDistribution(project) {
  const counts = {};
  for (const key of Object.keys(STATUS_LABELS)) counts[key] = 0;
  for (const item of project.coverage_items) {
    counts[item.status] = (counts[item.status] || 0) + 1;
  }
  return counts;
}

export function relationStats(project) {
  const relations = project.relations || [];
  const byType = {};
  for (const relation of relations) {
    byType[relation.relation_type] = (byType[relation.relation_type] || 0) + 1;
  }
  return { total: relations.length, byType };
}

export function buildKnowledgeTree(project) {
  const relationsBySource = new Map();
  for (const relation of project.relations || []) {
    if (!relationsBySource.has(relation.source_id)) relationsBySource.set(relation.source_id, []);
    relationsBySource.get(relation.source_id).push(relation);
  }

  const unitsById = new Map(project.knowledge_units.map((unit) => [unit.unit_id, unit]));
  return (project.note_plan || []).map((section, index) => {
    const sectionUnits = (section.units || []).map((unitId) => unitsById.get(unitId)).filter(Boolean);
    const learningStages = [...new Set(sectionUnits.map((unit) => unit.learning_stage).filter(Boolean))];
    return {
      id: section.section_id,
      index: index + 1,
      title: section.section_title,
      units: sectionUnits,
      parentTopics: [...new Set(sectionUnits.map((unit) => unit.parent_topic).filter(Boolean))],
      learningStages: learningStages.length ? learningStages : [inferLearningStage(section.section_title)],
      relations: relationsBySource.get(section.section_id) || [],
    };
  });
}

function inferLearningStage(title) {
  const text = String(title || "").toLowerCase();
  if (text.includes("homework")) return "exercise";
  if (text.includes("summary") || text.includes("next")) return "review";
  if (text.includes("random") || text.includes("mean") || text.includes("variance of estimation")) return "foundation";
  if (text.includes("linear regression") || text.includes("statistical modeling")) return "modeling";
  if (text.includes("likelihood") || text.includes("mle") || text.includes("estimation")) return "estimation";
  if (text.includes("bias-variance") || text.includes("trade-off")) return "analysis";
  if (text.includes("overfitting") || text.includes("underfitting")) return "diagnosis";
  if (text.includes("ridge") || text.includes("regularization")) return "regularization";
  if (text.includes("frequentist") || text.includes("bayesian")) return "statistical_view";
  return "foundation";
}

export function getReviewItems(project, { query = "" } = {}) {
  const q = query.trim().toLowerCase();
  const priority = { missing: 0, uncertain: 1, merged: 2, ignored: 3, covered: 4, appendix: 5 };
  return [...project.coverage_items]
    .filter((item) => {
      if (!q) return true;
      return [item.block_id, item.block_type, item.comment, item.note_location]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(q));
    })
    .sort((a, b) => (priority[a.status] ?? 9) - (priority[b.status] ?? 9));
}

export function filterCoverageItems(project, { status = "all", query = "" } = {}) {
  const q = query.trim().toLowerCase();
  return project.coverage_items.filter((item) => {
    if (status !== "all" && item.status !== status) return false;
    if (!q) return true;
    return [item.block_id, item.block_type, item.comment, item.note_location]
      .filter(Boolean)
      .some((value) => String(value).toLowerCase().includes(q));
  });
}

export function searchNoteChunks(project, query = "") {
  const q = query.trim().toLowerCase();
  if (!q) return project.note_chunks;
  return project.note_chunks.filter((chunk) =>
    [chunk.section_title, chunk.content].some((value) => String(value).toLowerCase().includes(q)),
  );
}

export function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

export function markdownToHtml(markdown) {
  const lines = markdown.split(/\r?\n/);
  const html = [];
  let listType = "";
  let inMath = false;
  let mathLines = [];
  let tableRows = [];

  const closeList = (nextType = "") => {
    if (listType && listType !== nextType) {
      html.push(`</${listType}>`);
      listType = "";
    }
  };

  const openList = (nextType) => {
    if (listType !== nextType) {
      closeList();
      html.push(`<${nextType}>`);
      listType = nextType;
    }
  };

  const closeMath = () => {
    html.push(`<div class="math-block">${escapeHtml(mathLines.join("\n").trim())}</div>`);
    inMath = false;
    mathLines = [];
  };

  const closeTable = () => {
    if (!tableRows.length) return;
    const [header, separator, ...body] = tableRows;
    if (!isTableSeparator(separator || "")) {
      for (const row of tableRows) html.push(`<p>${inlineMarkdown(row)}</p>`);
      tableRows = [];
      return;
    }
    html.push("<table>");
    html.push(`<thead><tr>${tableCells(header).map((cell) => `<th>${inlineMarkdown(cell)}</th>`).join("")}</tr></thead>`);
    html.push("<tbody>");
    for (const row of body) {
      html.push(`<tr>${tableCells(row).map((cell) => `<td>${inlineMarkdown(cell)}</td>`).join("")}</tr>`);
    }
    html.push("</tbody></table>");
    tableRows = [];
  };

  for (const line of lines) {
    const trimmed = line.trim();
    if (inMath) {
      if (trimmed.endsWith("\\]")) {
        mathLines.push(trimmed.slice(0, -2));
        closeMath();
      } else {
        mathLines.push(line);
      }
      continue;
    }

    if (trimmed.startsWith("|") && trimmed.endsWith("|")) {
      closeList();
      tableRows.push(trimmed);
      continue;
    }
    closeTable();

    if (trimmed.startsWith("\\[") && trimmed.endsWith("\\]") && trimmed.length > 4) {
      closeList();
      html.push(`<div class="math-block">${escapeHtml(trimmed.slice(2, -2).trim())}</div>`);
      continue;
    }

    if (trimmed === "\\[" || trimmed.startsWith("\\[")) {
      closeList();
      inMath = true;
      mathLines = [trimmed.slice(2)];
      continue;
    }

    if (!line.trim()) {
      closeList();
      continue;
    }
    if (line.startsWith("#### ")) {
      closeList();
      html.push(`<h4>${inlineMarkdown(line.slice(5))}</h4>`);
    } else if (line.startsWith("### ")) {
      closeList();
      html.push(`<h3>${inlineMarkdown(line.slice(4))}</h3>`);
    } else if (line.startsWith("## ")) {
      closeList();
      html.push(`<h2>${inlineMarkdown(line.slice(3))}</h2>`);
    } else if (line.startsWith("# ")) {
      closeList();
      html.push(`<h1>${inlineMarkdown(line.slice(2))}</h1>`);
    } else if (line.startsWith("- ")) {
      openList("ul");
      html.push(`<li>${inlineMarkdown(line.slice(2))}</li>`);
    } else if (/^\d+\.\s+/.test(line)) {
      openList("ol");
      html.push(`<li>${inlineMarkdown(line.replace(/^\d+\.\s+/, ""))}</li>`);
    } else {
      closeList();
      html.push(`<p>${inlineMarkdown(line)}</p>`);
    }
  }
  closeTable();
  closeList();
  if (inMath) closeMath();
  return html.join("");
}

function isTableSeparator(value) {
  return /^\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?$/.test(value);
}

function tableCells(row) {
  return row
    .replace(/^\|/, "")
    .replace(/\|$/, "")
    .split("|")
    .map((cell) => cell.trim());
}

export function inlineMarkdown(value) {
  return escapeHtml(value)
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/\\\((.+?)\\\)/g, '<span class="math-inline">$1</span>');
}
