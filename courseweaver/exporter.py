from __future__ import annotations

import json
from pathlib import Path

from courseweaver.models import KnowledgeUnit, ProjectIR
from courseweaver.notes import add_relationship_review_chunk


def export_project(project: ProjectIR, output_dir: Path) -> None:
    ir_dir = output_dir / "ir"
    notes_dir = output_dir / "notes"
    assets_dir = output_dir / "assets"
    report_dir = output_dir / "report"
    for directory in [ir_dir, notes_dir, assets_dir / "pages", assets_dir / "crops", report_dir]:
        directory.mkdir(parents=True, exist_ok=True)

    _write_json(ir_dir / "pages.json", project.pages)
    _write_json(ir_dir / "blocks.json", project.blocks)
    _write_json(ir_dir / "knowledge_units.json", project.knowledge_units)
    _write_json(ir_dir / "note_plan.json", project.note_plan)
    _write_json(ir_dir / "relations.json", project.relations)
    _write_json(ir_dir / "note_chunks.json", project.note_chunks)
    _write_json(ir_dir / "coverage_items.json", project.coverage_items)
    _write_json(ir_dir / "project.json", project)

    (notes_dir / "00_overview.md").write_text(_overview(project), encoding="utf-8")
    (notes_dir / "01_lecture_notes.md").write_text(_lecture_notes(project), encoding="utf-8")
    (notes_dir / "03_concepts.md").write_text(_concepts(project.knowledge_units), encoding="utf-8")
    (notes_dir / "04_formulas_and_algorithms.md").write_text(
        _formulas_and_algorithms(project.knowledge_units), encoding="utf-8"
    )
    (notes_dir / "05_common_mistakes.md").write_text(_common_mistakes(project.knowledge_units), encoding="utf-8")
    (notes_dir / "06_source_index.md").write_text(_source_index(project.knowledge_units), encoding="utf-8")
    (notes_dir / "07_coverage_report.md").write_text(_coverage_report(project), encoding="utf-8")
    (report_dir / "comparison_with_prompt.md").write_text(_comparison_template(project), encoding="utf-8")


def _write_json(path: Path, value) -> None:
    if isinstance(value, list):
        data = [item.model_dump(mode="json") if hasattr(item, "model_dump") else item for item in value]
    elif hasattr(value, "model_dump"):
        data = value.model_dump(mode="json")
    else:
        data = value
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _overview(project: ProjectIR) -> str:
    title = _project_title(project)
    return "\n".join(
        [
            f"# {title} 学习包总览",
            "",
            f"- 来源文件：`{project.source_file}`",
            f"- 页数：{len(project.pages)}",
            f"- blocks：{len(project.blocks)}",
            f"- 知识单元：{len(project.knowledge_units)}",
            f"- 覆盖 blocks：{project.coverage_summary.get('covered', 0)}",
            f"- 疑似遗漏：{project.coverage_summary.get('missing', 0)}",
            "",
            "建议阅读顺序：先读 `01_lecture_notes.md` 建立主线，再用 `03_concepts.md` 和 "
            "`04_formulas_and_algorithms.md` 复习结构化内容，最后查看 `07_coverage_report.md` 检查遗漏。",
            "",
        ]
    )


def _lecture_notes(project: ProjectIR) -> str:
    title = _project_title(project)
    note_chunks = project.note_chunks
    if note_chunks and note_chunks[0].section_title != "关系导读与对比总结":
        note_chunks = add_relationship_review_chunk(
            note_chunks,
            project.knowledge_units,
            project.relations,
            project.note_plan,
        )
    chunks = "\n".join(chunk.content for chunk in note_chunks)
    return f"# {title} 讲义式笔记\n\n{chunks}\n"


def _concepts(units: list[KnowledgeUnit]) -> str:
    rows = ["# 概念表", "", "| 知识点 | 类型 | 解释 | 来源 |", "|---|---|---|---|"]
    for unit in units:
        if unit.unit_type in {"formula", "algorithm"}:
            continue
        rows.append(f"| {unit.name} | {unit.unit_type} | {_escape(unit.summary)} | {_pages(unit.source_pages)} |")
    rows.append("")
    return "\n".join(rows)


def _formulas_and_algorithms(units: list[KnowledgeUnit]) -> str:
    rows = ["# 公式与算法", ""]
    selected = [unit for unit in units if unit.unit_type in {"formula", "algorithm"}]
    if not selected:
        rows.append("本次解析未识别出明确的公式或算法 block。")
        rows.append("")
        return "\n".join(rows)
    for unit in selected:
        rows.extend(
            [
                f"## {unit.name} [{_pages(unit.source_pages)}]",
                "",
                unit.summary,
                "",
                "复习提示：确认它的目标、输入输出、关键符号或循环条件。",
                "",
            ]
        )
    return "\n".join(rows)


def _common_mistakes(units: list[KnowledgeUnit]) -> str:
    rows = ["# 易错点", ""]
    warning_units = [unit for unit in units if unit.unit_type == "warning"]
    if not warning_units:
        warning_units = [unit for unit in units if any(word in unit.summary.lower() for word in ["bias", "variance", "overfitting", "underfitting"])]
    if not warning_units:
        rows.append("MVP 暂未从课件中识别出明确的易错点。建议人工补充学生常见误解。")
        rows.append("")
        return "\n".join(rows)
    for unit in warning_units:
        rows.append(f"- **{unit.name}** [{_pages(unit.source_pages)}]：{unit.summary}")
    rows.append("")
    return "\n".join(rows)


def _source_index(units: list[KnowledgeUnit]) -> str:
    rows = ["# 来源索引", "", "| 知识点 | 类型 | 来源页码 | 来源 block |", "|---|---|---|---|"]
    for unit in units:
        rows.append(
            f"| {unit.name} | {unit.unit_type} | {_pages(unit.source_pages)} | {', '.join(unit.source_blocks)} |"
        )
    rows.append("")
    return "\n".join(rows)


def _coverage_report(project: ProjectIR) -> str:
    rows = [
        "# 覆盖报告",
        "",
        "## 总览",
        "",
    ]
    for key in ["total_blocks", "valid_blocks", "covered", "merged", "appendix", "ignored", "uncertain", "missing"]:
        rows.append(f"- {key}: {project.coverage_summary.get(key, 0)}")
    rows.extend(
        [
            "",
            "## 逐项覆盖",
            "",
            "| 页码 | Block | 类型 | 状态 | 去向 | 说明 |",
            "|---|---|---|---|---|---|",
        ]
    )
    for item in project.coverage_items:
        rows.append(
            f"| p.{item.page_number} | {item.block_id} | {item.block_type} | {item.status} | "
            f"{item.note_location or '-'} | {_escape(item.comment)} |"
        )
    rows.append("")
    return "\n".join(rows)


def _comparison_template(project: ProjectIR) -> str:
    return "\n".join(
        [
            "# 与直接 Prompt 生成笔记的对比",
            "",
            "## Baseline",
            "",
            "将同一份课件直接交给大模型，让其一次性生成总结。这里建议粘贴 baseline 片段。",
            "",
            "## CourseWeaver 输出优势",
            "",
            "1. 先生成 CourseIR，再生成笔记，保留了知识单元和来源 block。",
            "2. 主笔记按知识点组织，而不是简单逐页摘要。",
            "3. 来源索引能追溯到页码和 block id。",
            "4. 覆盖报告能暴露 missing / uncertain 项。",
            "",
            "## 本次输出规模",
            "",
            f"- 知识单元：{len(project.knowledge_units)}",
            f"- 有效 blocks：{project.coverage_summary.get('valid_blocks', 0)}",
            f"- 疑似遗漏：{project.coverage_summary.get('missing', 0)}",
            "",
        ]
    )


def _project_title(project: ProjectIR) -> str:
    for block in project.blocks:
        if block.block_type == "title" and block.text:
            return block.text
    return Path(project.source_file).stem


def _pages(pages: list[int]) -> str:
    unique = sorted(set(pages))
    if not unique:
        return "-"
    return ", ".join(f"p.{page}" for page in unique)


def _escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")
