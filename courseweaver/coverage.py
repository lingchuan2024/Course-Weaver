from __future__ import annotations

from collections import Counter

from courseweaver.models import Block, CoverageItem, KnowledgeUnit, NoteChunk
from courseweaver.units import classify_block


def build_coverage(
    blocks: list[Block], units: list[KnowledgeUnit], chunks: list[NoteChunk]
) -> tuple[list[CoverageItem], dict[str, int]]:
    unit_blocks = {block_id for unit in units for block_id in unit.source_blocks}
    chunk_blocks = {block_id for chunk in chunks for block_id in chunk.source_blocks}
    chunk_locations = {
        block_id: f"{chunk.note_file}#{_anchor(chunk.section_title)}"
        for chunk in chunks
        for block_id in chunk.source_blocks
    }

    items: list[CoverageItem] = []
    for block in blocks:
        block_type = block.block_type if block.block_type != "unknown" else classify_block(block.text)
        if block_type == "noise":
            status = "ignored"
            location = None
            comment = "识别为页码、装饰符或空内容。"
        elif block.block_id in chunk_blocks:
            status = "covered"
            location = chunk_locations.get(block.block_id)
            comment = "已进入主笔记或复习包。"
        elif block.block_id in unit_blocks:
            status = "merged"
            location = None
            comment = "已抽取为知识单元，但未直接出现在主笔记中。"
        elif block_type == "unknown":
            status = "uncertain"
            location = None
            comment = "block 类型不确定，需要人工确认。"
        else:
            status = "missing"
            location = None
            comment = "有效 block 未映射到知识单元或笔记。"

        items.append(
            CoverageItem(
                block_id=block.block_id,
                page_number=block.page_number,
                block_type=block_type,
                status=status,
                note_location=location,
                comment=comment,
            )
        )

    counter = Counter(item.status for item in items)
    summary = {
        "total_blocks": len(blocks),
        "valid_blocks": sum(1 for item in items if item.status != "ignored"),
        "covered": counter["covered"],
        "merged": counter["merged"],
        "appendix": counter["appendix"],
        "ignored": counter["ignored"],
        "uncertain": counter["uncertain"],
        "missing": counter["missing"],
    }
    return items, summary


def _anchor(title: str) -> str:
    return title.strip().lower().replace(" ", "-")
