import tempfile
import unittest
from pathlib import Path

from courseweaver.exporter import export_project
from courseweaver.models import (
    Block,
    CoverageItem,
    KnowledgeUnit,
    NoteChunk,
    NotePlanSection,
    PageIR,
    ProjectIR,
)
from courseweaver.pdf_parser import parse_bbox_layout_xml


class ParserAndExportTests(unittest.TestCase):
    def test_parses_bbox_layout_xml_into_pages_and_blocks(self):
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <html xmlns="http://www.w3.org/1999/xhtml">
          <body><doc>
            <page width="400" height="300">
              <flow>
                <block xMin="10" yMin="20" xMax="100" yMax="40">
                  <line><word>Hello</word><word>World</word></line>
                </block>
              </flow>
            </page>
          </doc></body>
        </html>
        """

        pages, blocks = parse_bbox_layout_xml(xml)

        self.assertEqual(len(pages), 1)
        self.assertEqual(pages[0].page_id, "p001")
        self.assertEqual(pages[0].blocks, ["p001_b001"])
        self.assertEqual(blocks[0].text, "Hello World")
        self.assertEqual(blocks[0].bbox, [10.0, 20.0, 100.0, 40.0])

    def test_strips_invalid_xml_control_characters_from_pdftotext_output(self):
        xml = """<html xmlns="http://www.w3.org/1999/xhtml"><body><doc>
        <page width="400" height="300">
          <flow><block xMin="1" yMin="2" xMax="3" yMax="4">
            <line><word>\x12</word><word>formula</word><word>\x13</word></line>
          </block></flow>
        </page>
        </doc></body></html>"""

        pages, blocks = parse_bbox_layout_xml(xml)

        self.assertEqual(len(pages), 1)
        self.assertEqual(blocks[0].text, "formula")

    def test_exports_project_markdown_and_ir_files(self):
        project = ProjectIR(
            project_id="demo",
            source_file="demo.pdf",
            pages=[PageIR(page_id="p001", page_number=1, width=400, height=300, blocks=["p001_b001"])],
            blocks=[
                Block(
                    block_id="p001_b001",
                    page_id="p001",
                    page_number=1,
                    block_type="title",
                    text="Linear Regression",
                    bbox=[10, 20, 100, 40],
                    reading_order=1,
                )
            ],
            knowledge_units=[
                KnowledgeUnit(
                    unit_id="U_0001",
                    name="Linear Regression",
                    unit_type="summary",
                    summary="Linear regression overview.",
                    source_pages=[1],
                    source_blocks=["p001_b001"],
                )
            ],
            note_plan=[
                NotePlanSection(
                    section_id="S_0001",
                    section_title="Linear Regression",
                    units=["U_0001"],
                    goal="Explain the topic.",
                )
            ],
            note_chunks=[
                NoteChunk(
                    chunk_id="N_0001",
                    note_file="01_lecture_notes.md",
                    section_title="Linear Regression",
                    content="## Linear Regression\n\nLinear regression overview.",
                    source_units=["U_0001"],
                    source_blocks=["p001_b001"],
                )
            ],
            coverage_items=[
                CoverageItem(
                    block_id="p001_b001",
                    page_number=1,
                    block_type="title",
                    status="covered",
                    note_location="01_lecture_notes.md#linear-regression",
                    comment="covered",
                )
            ],
            coverage_summary={"total_blocks": 1, "valid_blocks": 1, "covered": 1, "merged": 0, "appendix": 0, "ignored": 0, "uncertain": 0, "missing": 0},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            export_project(project, Path(tmpdir))
            self.assertTrue((Path(tmpdir) / "ir" / "knowledge_units.json").exists())
            note = (Path(tmpdir) / "notes" / "01_lecture_notes.md").read_text(encoding="utf-8")
            coverage = (Path(tmpdir) / "notes" / "07_coverage_report.md").read_text(encoding="utf-8")

        self.assertIn("Linear Regression", note)
        self.assertIn("covered", coverage)


if __name__ == "__main__":
    unittest.main()
