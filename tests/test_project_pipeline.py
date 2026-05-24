import unittest

from courseweaver.models import Block, KnowledgeUnit, NotePlanSection, PageIR
from courseweaver.notes import reorder_note_plan_for_learning
from courseweaver.pipeline import build_project_ir


class ProjectPipelineTests(unittest.TestCase):
    def test_builds_project_ir_from_pages_and_blocks(self):
        pages = [PageIR(page_id="p002", page_number=2, width=400, height=300, blocks=["p002_b001", "p002_b002"])]
        blocks = [
            Block(
                block_id="p002_b001",
                page_id="p002",
                page_number=2,
                block_type="title",
                text="Linear Regression",
                bbox=[10, 20, 100, 40],
                reading_order=1,
            ),
            Block(
                block_id="p002_b002",
                page_id="p002",
                page_number=2,
                block_type="formula",
                text="y = Xw + e",
                bbox=[10, 60, 100, 80],
                reading_order=2,
            ),
        ]

        project = build_project_ir("demo", "demo.pdf", pages, blocks)

        self.assertEqual(project.project_id, "demo")
        self.assertGreaterEqual(len(project.knowledge_units), 2)
        self.assertGreaterEqual(len(project.note_plan), 1)
        self.assertGreaterEqual(len(project.note_chunks), 1)
        self.assertEqual(project.coverage_summary["covered"], 2)

    def test_keeps_minor_units_out_of_main_note(self):
        pages = [PageIR(page_id="p001", page_number=1, width=400, height=300, blocks=["p001_b001", "p001_b002"])]
        blocks = [
            Block(
                block_id="p001_b001",
                page_id="p001",
                page_number=1,
                block_type="text",
                text="Minor caption",
                bbox=[10, 20, 100, 40],
                reading_order=1,
            ),
            Block(
                block_id="p001_b002",
                page_id="p001",
                page_number=1,
                block_type="text",
                text="Maximum likelihood estimation is the main method in this lecture.",
                bbox=[10, 60, 100, 80],
                reading_order=2,
            ),
        ]

        project = build_project_ir("demo", "demo.pdf", pages, blocks)

        self.assertEqual(project.coverage_summary["merged"], 1)
        self.assertEqual(project.coverage_summary["covered"], 1)

    def test_groups_related_units_under_repeated_section_title(self):
        pages = [
            PageIR(page_id="p001", page_number=1, width=400, height=300, blocks=["p001_b001", "p001_b002"]),
            PageIR(page_id="p002", page_number=2, width=400, height=300, blocks=["p002_b001", "p002_b002"]),
        ]
        blocks = [
            Block(
                block_id="p001_b001",
                page_id="p001",
                page_number=1,
                block_type="title",
                text="Maximum Likelihood Estimation",
                bbox=[10, 20, 100, 40],
                reading_order=1,
            ),
            Block(
                block_id="p001_b002",
                page_id="p001",
                page_number=1,
                block_type="text",
                text="MLE maximizes likelihood under a noise model.",
                bbox=[10, 60, 100, 80],
                reading_order=2,
            ),
            Block(
                block_id="p002_b001",
                page_id="p002",
                page_number=2,
                block_type="title",
                text="Maximum Likelihood Estimation",
                bbox=[10, 20, 100, 40],
                reading_order=1,
            ),
            Block(
                block_id="p002_b002",
                page_id="p002",
                page_number=2,
                block_type="formula",
                text="theta = arg max log P(y|X, theta)",
                bbox=[10, 60, 100, 80],
                reading_order=2,
            ),
        ]

        project = build_project_ir("demo", "demo.pdf", pages, blocks)

        self.assertEqual(len(project.note_plan), 1)
        self.assertEqual(project.note_plan[0].section_title, "Maximum Likelihood Estimation")
        self.assertEqual(project.coverage_summary["covered"], 4)

    def test_keeps_cover_and_outline_out_of_main_note_plan(self):
        pages = [PageIR(page_id="p001", page_number=1, width=400, height=300, blocks=["p001_b001"])]
        blocks = [
            Block(
                block_id="p001_b001",
                page_id="p001",
                page_number=1,
                block_type="title",
                text="Introduction to Machine Learning",
                bbox=[10, 20, 100, 40],
                reading_order=1,
            )
        ]

        project = build_project_ir("demo", "demo.pdf", pages, blocks)

        self.assertEqual(project.note_plan, [])
        self.assertEqual(project.coverage_summary["merged"], 1)

    def test_reorders_note_plan_into_learning_path(self):
        pages = [
            PageIR(page_id="p002", page_number=2, width=400, height=300, blocks=["p002_b001"]),
            PageIR(page_id="p003", page_number=3, width=400, height=300, blocks=["p003_b001"]),
            PageIR(page_id="p004", page_number=4, width=400, height=300, blocks=["p004_b001"]),
        ]
        blocks = [
            Block(
                block_id="p002_b001",
                page_id="p002",
                page_number=2,
                block_type="title",
                text="Linear Regression",
                bbox=[10, 20, 100, 40],
                reading_order=1,
            ),
            Block(
                block_id="p003_b001",
                page_id="p003",
                page_number=3,
                block_type="title",
                text="Random Variables and Instances/Samples",
                bbox=[10, 20, 100, 40],
                reading_order=1,
            ),
            Block(
                block_id="p004_b001",
                page_id="p004",
                page_number=4,
                block_type="title",
                text="Homework 1",
                bbox=[10, 20, 100, 40],
                reading_order=1,
            ),
        ]

        project = build_project_ir("demo", "demo.pdf", pages, blocks)
        titles = [section.section_title for section in project.note_plan]

        self.assertEqual(titles[0], "Random Variables and Instances/Samples")
        self.assertLess(titles.index("Random Variables and Instances/Samples"), titles.index("Linear Regression"))
        self.assertNotIn("Homework 1", titles)

    def test_reorders_note_plan_by_ai_prerequisite_graph(self):
        units = [
            KnowledgeUnit(
                unit_id="u1",
                name="Ridge Regression",
                unit_type="concept",
                summary="Ridge adds L2 regularization.",
                source_pages=[2],
                source_blocks=["b1"],
                importance="core",
                learning_stage="regularization",
                prerequisites=["Maximum Likelihood Estimation"],
            ),
            KnowledgeUnit(
                unit_id="u2",
                name="Maximum Likelihood Estimation",
                unit_type="concept",
                summary="MLE maximizes likelihood.",
                source_pages=[9],
                source_blocks=["b2"],
                importance="core",
                learning_stage="estimation",
            ),
        ]
        plan = [
            NotePlanSection(section_id="s1", section_title="Ridge Regression", units=["u1"], goal="test"),
            NotePlanSection(section_id="s2", section_title="Maximum Likelihood Estimation", units=["u2"], goal="test"),
        ]

        reordered = reorder_note_plan_for_learning(plan, units)

        self.assertEqual([section.section_title for section in reordered], ["Maximum Likelihood Estimation", "Ridge Regression"])


if __name__ == "__main__":
    unittest.main()
