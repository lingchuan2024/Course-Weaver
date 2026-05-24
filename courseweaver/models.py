from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


BlockType = Literal[
    "title",
    "text",
    "formula",
    "figure",
    "table",
    "code_or_algorithm",
    "noise",
    "unknown",
]

UnitType = Literal[
    "concept",
    "definition",
    "formula",
    "algorithm",
    "theorem",
    "proof",
    "example",
    "figure",
    "table",
    "comparison",
    "warning",
    "exercise",
    "summary",
]

CoverageStatus = Literal["covered", "merged", "appendix", "ignored", "uncertain", "missing"]


class PageIR(BaseModel):
    page_id: str
    page_number: int
    width: float
    height: float
    page_image: str | None = None
    blocks: list[str] = Field(default_factory=list)


class Block(BaseModel):
    block_id: str
    page_id: str
    page_number: int
    block_type: BlockType
    text: str
    bbox: list[float]
    reading_order: int
    latex: str | None = None
    image_path: str | None = None


class KnowledgeUnit(BaseModel):
    unit_id: str
    name: str
    unit_type: UnitType
    summary: str
    source_pages: list[int]
    source_blocks: list[str]
    importance: Literal["core", "supporting", "minor"] = "supporting"
    confidence: float = 0.7


class NotePlanSection(BaseModel):
    section_id: str
    section_title: str
    units: list[str]
    style: Literal["narrative", "formula_explanation", "algorithm_walkthrough", "review"] = "narrative"
    goal: str
    detail_level: Literal["low", "medium", "high"] = "medium"


class NoteChunk(BaseModel):
    chunk_id: str
    note_file: str
    section_title: str
    content: str
    source_units: list[str]
    source_blocks: list[str]


class CoverageItem(BaseModel):
    block_id: str
    page_number: int
    block_type: BlockType
    status: CoverageStatus
    note_location: str | None = None
    comment: str


class Relation(BaseModel):
    relation_id: str
    source_id: str
    target_id: str
    relation_type: Literal[
        "next",
        "parallel_with",
        "foundation_for",
        "derives",
        "regularizes",
        "contrasts_with",
        "example_of",
        "supports",
    ]
    source_label: str
    target_label: str
    reason: str
    confidence: float = 0.7
    evidence_units: list[str] = Field(default_factory=list)


class ProjectIR(BaseModel):
    project_id: str
    source_file: str
    pages: list[PageIR]
    blocks: list[Block]
    knowledge_units: list[KnowledgeUnit]
    note_plan: list[NotePlanSection]
    relations: list[Relation] = Field(default_factory=list)
    note_chunks: list[NoteChunk]
    coverage_items: list[CoverageItem]
    coverage_summary: dict[str, int]
