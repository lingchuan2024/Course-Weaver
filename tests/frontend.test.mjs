import assert from "node:assert/strict";
import test from "node:test";

import {
  buildKnowledgeGraph,
  buildKnowledgeTree,
  buildNoteMarkdown,
  filterCoverageItems,
  findFirstLearningPage,
  getReviewItems,
  getPageBlocks,
  indexProject,
  markdownToHtml,
  relationStats,
  searchNoteChunks,
  statusDistribution,
  summarizeProject,
} from "../web/app.mjs";

const project = {
  project_id: "demo",
  pages: [{ page_id: "p001", page_number: 1, width: 400, height: 300, blocks: ["b1", "b2"] }],
  blocks: [
    { block_id: "b1", page_id: "p001", page_number: 1, block_type: "title", text: "Linear Regression" },
    { block_id: "b2", page_id: "p001", page_number: 1, block_type: "formula", text: "y = Xw" },
  ],
  knowledge_units: [
    {
      unit_id: "u1",
      name: "Linear Regression",
      source_blocks: ["b1", "b2"],
      parent_topic: "Statistical Modeling",
      learning_stage: "modeling",
    },
  ],
  note_chunks: [
    { section_title: "Linear Regression", content: "## Linear Regression\n\n- Fit a line\n\n来源：p.1" },
  ],
  note_plan: [
    { section_id: "s1", section_title: "Linear Regression", units: ["u1"] },
    { section_id: "s2", section_title: "Ridge Regression", units: ["u1"] },
  ],
  relations: [
    {
      relation_id: "r1",
      source_id: "s1",
      target_id: "s2",
      relation_type: "foundation_for",
      source_label: "Linear Regression",
      target_label: "Ridge Regression",
      reason: "Ridge builds on linear regression.",
    },
  ],
  coverage_items: [
    { block_id: "b1", status: "covered", block_type: "title", comment: "ok" },
    { block_id: "b2", status: "missing", block_type: "formula", comment: "formula missing" },
  ],
  coverage_summary: { valid_blocks: 2, covered: 1, merged: 0, missing: 1 },
};

test("summarizes project metrics", () => {
  assert.equal(summarizeProject(project).title, "Linear Regression");
  assert.equal(summarizeProject(project).coverageRate, 50);
});

test("chooses first learning page instead of cover or outline", () => {
  const richerProject = {
    ...project,
    pages: [
      { page_id: "p001", page_number: 1, width: 400, height: 300, blocks: ["cover"] },
      { page_id: "p002", page_number: 2, width: 400, height: 300, blocks: ["outline"] },
      { page_id: "p003", page_number: 3, width: 400, height: 300, blocks: ["real"] },
    ],
    blocks: [
      { block_id: "cover", page_id: "p001", page_number: 1, block_type: "title", text: "Course Title" },
      { block_id: "outline", page_id: "p002", page_number: 2, block_type: "title", text: "Outline" },
      { block_id: "real", page_id: "p003", page_number: 3, block_type: "text", text: "Maximum likelihood estimation introduces a statistical view." },
    ],
  };

  assert.equal(findFirstLearningPage(richerProject), "p003");
});


test("indexes page blocks and units by block", () => {
  const indexes = indexProject(project);
  assert.equal(getPageBlocks(project, "p001", indexes).length, 2);
  assert.equal(indexes.unitsByBlock.get("b2")[0].unit_id, "u1");
});

test("filters coverage and note chunks", () => {
  assert.equal(filterCoverageItems(project, { status: "missing" }).length, 1);
  assert.equal(filterCoverageItems(project, { query: "formula" }).length, 1);
  assert.equal(searchNoteChunks(project, "fit").length, 1);
});

test("computes status distribution", () => {
  const distribution = statusDistribution(project);
  assert.equal(distribution.covered, 1);
  assert.equal(distribution.missing, 1);
});

test("summarizes relation types", () => {
  const stats = relationStats(project);
  assert.equal(stats.total, 1);
  assert.equal(stats.byType.foundation_for, 1);
});

test("builds downloadable markdown and knowledge tree", () => {
  const markdown = buildNoteMarkdown(project);
  assert.match(markdown, /^# Linear Regression 讲义式笔记/);
  assert.match(markdown, /Fit a line/);

  const tree = buildKnowledgeTree(project);
  assert.equal(tree.length, 2);
  assert.equal(tree[0].units[0].name, "Linear Regression");
  assert.equal(tree[0].parentTopics[0], "Statistical Modeling");
  assert.equal(tree[0].learningStages[0], "modeling");
  assert.equal(tree[0].relations[0].target_label, "Ridge Regression");

  const graph = buildKnowledgeGraph(project);
  assert.equal(graph.nodes.length, 2);
  assert.equal(graph.edges.length, 1);
  assert.equal(graph.edges[0].relation_type, "foundation_for");
  assert.ok(graph.width >= 420);
});

test("prioritizes review items that need attention", () => {
  const items = getReviewItems(project);
  assert.equal(items[0].status, "missing");
});

test("renders minimal markdown safely", () => {
  const html = markdownToHtml("## Title\n\n- `code` and **bold**\n\n| A | B |\n|---|---|\n| x | y |\n\n\\[\ny = X\\theta\n\\]\n\ninline \\(x\\)");
  assert.match(html, /<h2>Title<\/h2>/);
  assert.match(html, /<code>code<\/code>/);
  assert.match(html, /<strong>bold<\/strong>/);
  assert.match(html, /<table>/);
  assert.match(html, /<th>A<\/th>/);
  assert.match(html, /class="math-block"/);
  assert.match(html, /class="math-inline"/);
});
