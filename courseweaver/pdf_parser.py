from __future__ import annotations

import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

from courseweaver.models import Block, PageIR
from courseweaver.units import classify_block, normalize_text


class PdfParserError(RuntimeError):
    pass


def parse_pdf(pdf_path: Path) -> tuple[list[PageIR], list[Block]]:
    if not pdf_path.exists():
        raise PdfParserError(f"PDF not found: {pdf_path}")
    pdftotext = shutil.which("pdftotext")
    if not pdftotext:
        raise PdfParserError("pdftotext is required for the MVP parser but was not found in PATH.")

    result = subprocess.run(
        [pdftotext, "-bbox-layout", str(pdf_path), "-"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        raise PdfParserError(result.stderr.strip() or "pdftotext failed")
    return parse_bbox_layout_xml(result.stdout)


def parse_bbox_layout_xml(xml_text: str) -> tuple[list[PageIR], list[Block]]:
    root = ET.fromstring(_strip_invalid_xml_chars(xml_text))
    page_elements = [element for element in root.iter() if _local_name(element.tag) == "page"]

    pages: list[PageIR] = []
    blocks: list[Block] = []
    for page_number, page_element in enumerate(page_elements, start=1):
        page_id = f"p{page_number:03d}"
        page = PageIR(
            page_id=page_id,
            page_number=page_number,
            width=float(page_element.attrib.get("width", 0.0)),
            height=float(page_element.attrib.get("height", 0.0)),
            blocks=[],
        )

        block_elements = [element for element in page_element.iter() if _local_name(element.tag) == "block"]
        for reading_order, block_element in enumerate(block_elements, start=1):
            text = _block_text(block_element)
            if not text:
                continue

            block_id = f"{page_id}_b{len(page.blocks) + 1:03d}"
            bbox = [
                float(block_element.attrib.get("xMin", 0.0)),
                float(block_element.attrib.get("yMin", 0.0)),
                float(block_element.attrib.get("xMax", 0.0)),
                float(block_element.attrib.get("yMax", 0.0)),
            ]
            block = Block(
                block_id=block_id,
                page_id=page_id,
                page_number=page_number,
                block_type=classify_block(text),
                text=text,
                bbox=bbox,
                reading_order=reading_order,
            )
            page.blocks.append(block_id)
            blocks.append(block)

        pages.append(page)

    return pages, blocks


def _block_text(block_element: ET.Element) -> str:
    words = []
    for element in block_element.iter():
        if _local_name(element.tag) == "word" and element.text:
            words.append(element.text)
    return normalize_text(" ".join(words))


def _local_name(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", 1)[1]
    return tag


def _strip_invalid_xml_chars(value: str) -> str:
    return "".join(
        char
        for char in value
        if char in "\t\n\r"
        or "\u0020" <= char <= "\ud7ff"
        or "\ue000" <= char <= "\ufffd"
        or "\U00010000" <= char <= "\U0010ffff"
    )
