import unittest
from unittest.mock import Mock

from courseweaver.coverage import build_coverage
from courseweaver.models import Block, KnowledgeUnit, NoteChunk
from courseweaver.units import classify_block, extract_units, extract_units_with_llm, merge_units


def block(block_id, page, text, y=10):
    return Block(
        block_id=block_id,
        page_id=f"p{page:03d}",
        page_number=page,
        block_type="unknown",
        text=text,
        bbox=[10.0, float(y), 300.0, float(y + 10)],
        reading_order=1,
    )


class UnitPipelineTests(unittest.TestCase):
    def test_classifies_formula_algorithm_and_noise_blocks(self):
        self.assertEqual(classify_block("w = (X^T X)^-1 X^T y"), "formula")
        self.assertEqual(classify_block("Algorithm: gradient descent repeat until convergence"), "code_or_algorithm")
        self.assertEqual(classify_block("2 / 25"), "noise")
        self.assertEqual(classify_block("(1)"), "noise")
        self.assertEqual(classify_block("T"), "noise")
        self.assertEqual(classify_block("▶ Data:"), "text")

    def test_extracts_units_with_source_blocks(self):
        blocks = [
            block("p001_b001", 1, "Linear Regression"),
            block("p001_b002", 1, "We estimate parameters by maximum likelihood estimation."),
            block("p001_b003", 1, "w = (X^T X)^-1 X^T y"),
        ]

        units = extract_units(blocks)

        self.assertGreaterEqual(len(units), 2)
        self.assertTrue(any(unit.unit_type == "formula" for unit in units))
        self.assertTrue(all(unit.source_blocks for unit in units))
        self.assertTrue(all(unit.source_pages for unit in units))

    def test_title_containing_example_remains_section_summary(self):
        units = extract_units([block("p004_b001", 4, "Recall the Example of Linear Regression")])

        self.assertEqual(units[0].unit_type, "summary")

    def test_extracts_semantic_units_with_llm_source_blocks(self):
        blocks = [
            block("p006_b001", 6, "A Frequentist Viewpoint: Maximum Likelihood Estimation"),
            block("p006_b002", 6, "Assume noise epsilon follows a Gaussian distribution."),
            block("p006_b003", 6, "theta = arg max log P(y|X, theta)"),
        ]
        client = Mock()
        client.chat.return_value = """
        {
          "units": [
            {
              "name": "Maximum Likelihood Estimation",
              "unit_type": "concept",
              "summary": "MLE explains why Gaussian noise leads to the least-squares objective.",
              "source_blocks": ["p006_b001", "p006_b002", "p006_b003"],
              "importance": "core",
              "confidence": 0.93
            }
          ]
        }
        """

        units = extract_units_with_llm(blocks, client)

        self.assertEqual(len(units), 1)
        self.assertEqual(units[0].name, "Maximum Likelihood Estimation")
        self.assertEqual(units[0].source_pages, [6])
        self.assertEqual(units[0].source_blocks, ["p006_b001", "p006_b002", "p006_b003"])
        self.assertEqual(units[0].importance, "core")

    def test_llm_extraction_falls_back_to_heuristics(self):
        blocks = [
            block("p006_b001", 6, "Maximum Likelihood Estimation"),
            block("p006_b002", 6, "theta = arg max log P(y|X, theta)"),
        ]
        client = Mock()
        client.chat.side_effect = RuntimeError("api failed")

        units = extract_units_with_llm(blocks, client)

        self.assertGreaterEqual(len(units), 2)
        self.assertTrue(any(unit.unit_type == "formula" for unit in units))

    def test_merges_units_with_same_normalized_name_across_pages(self):
        units = [
            KnowledgeUnit(
                unit_id="U_001",
                name="Maximum Likelihood Estimation",
                unit_type="concept",
                summary="MLE estimates parameters by maximizing likelihood.",
                source_pages=[3],
                source_blocks=["p003_b001"],
                importance="core",
                confidence=0.8,
            ),
            KnowledgeUnit(
                unit_id="U_002",
                name="Maximum Likelihood Estimation",
                unit_type="concept",
                summary="For linear regression, MLE connects Gaussian noise to least squares.",
                source_pages=[4],
                source_blocks=["p004_b002"],
                importance="core",
                confidence=0.8,
            ),
        ]

        merged = merge_units(units)

        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0].source_pages, [3, 4])
        self.assertEqual(merged[0].source_blocks, ["p003_b001", "p004_b002"])
        self.assertIn("Gaussian noise", merged[0].summary)

    def test_builds_coverage_items_and_summary(self):
        blocks = [
            block("p001_b001", 1, "Linear Regression"),
            block("p001_b002", 1, "2 / 25"),
            block("p002_b001", 2, "An unexplained figure"),
        ]
        units = [
            KnowledgeUnit(
                unit_id="U_001",
                name="Linear Regression",
                unit_type="concept",
                summary="Linear regression models a linear relationship.",
                source_pages=[1],
                source_blocks=["p001_b001"],
                importance="core",
                confidence=0.9,
            )
        ]
        chunks = [
            NoteChunk(
                chunk_id="N_001",
                note_file="01_lecture_notes.md",
                section_title="Linear Regression",
                content="Linear regression models a linear relationship.",
                source_units=["U_001"],
                source_blocks=["p001_b001"],
            )
        ]

        items, summary = build_coverage(blocks, units, chunks)

        statuses = {item.block_id: item.status for item in items}
        self.assertEqual(statuses["p001_b001"], "covered")
        self.assertEqual(statuses["p001_b002"], "ignored")
        self.assertEqual(statuses["p002_b001"], "missing")
        self.assertEqual(summary["covered"], 1)
        self.assertEqual(summary["missing"], 1)


if __name__ == "__main__":
    unittest.main()
