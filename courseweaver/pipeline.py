from __future__ import annotations

import re
from pathlib import Path

from courseweaver.coverage import build_coverage
from courseweaver.exporter import export_project
from courseweaver.llm import create_llm_client
from courseweaver.models import Block, PageIR, ProjectIR
from courseweaver.notes import generate_note_chunks, plan_notes, refine_note_chunks_with_llm
from courseweaver.pdf_parser import parse_pdf
from courseweaver.relations import build_relations
from courseweaver.units import extract_units, merge_units


def run_pipeline(
    pdf_path: Path,
    output_dir: Path | None = None,
    project_id: str | None = None,
    use_llm: bool = False,
    llm_provider: str = "deepseek",
    llm_model: str | None = None,
    deepseek_thinking: str = "disabled",
) -> ProjectIR:
    pdf_path = pdf_path.resolve()
    project_id = project_id or _slug(pdf_path.stem)
    output_dir = output_dir or Path("output") / project_id

    pages, blocks = parse_pdf(pdf_path)
    llm_client = None
    if use_llm:
        llm_client = create_llm_client(llm_provider, model=llm_model, thinking=deepseek_thinking)
    project = build_project_ir(project_id, str(pdf_path), pages, blocks, llm_client=llm_client)
    export_project(project, output_dir)
    return project


def build_project_ir(
    project_id: str,
    source_file: str,
    pages: list[PageIR],
    blocks: list[Block],
    llm_client=None,
) -> ProjectIR:
    page_units = extract_units(blocks)
    knowledge_units = merge_units(page_units)
    note_plan = plan_notes(knowledge_units)
    relations = build_relations(knowledge_units, note_plan)
    note_chunks = generate_note_chunks(knowledge_units, note_plan)
    if llm_client is not None:
        note_chunks = refine_note_chunks_with_llm(note_chunks, knowledge_units, llm_client)
    coverage_items, coverage_summary = build_coverage(blocks, knowledge_units, note_chunks)

    return ProjectIR(
        project_id=project_id,
        source_file=source_file,
        pages=pages,
        blocks=blocks,
        knowledge_units=knowledge_units,
        note_plan=note_plan,
        relations=relations,
        note_chunks=note_chunks,
        coverage_items=coverage_items,
        coverage_summary=coverage_summary,
    )


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", value).strip("-").lower()
    return slug or "courseweaver-project"
