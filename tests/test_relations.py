import unittest

from courseweaver.models import KnowledgeUnit, NotePlanSection
from courseweaver.relations import build_relations


def unit(unit_id, name, unit_type="summary", **kwargs):
    return KnowledgeUnit(
        unit_id=unit_id,
        name=name,
        unit_type=unit_type,
        summary=name,
        source_pages=[1],
        source_blocks=[f"{unit_id}_b001"],
        importance="core",
        **kwargs,
    )


def section(section_id, title, units):
    return NotePlanSection(
        section_id=section_id,
        section_title=title,
        units=units,
        goal="test",
    )


class RelationTests(unittest.TestCase):
    def test_builds_learning_order_between_note_sections(self):
        relations = build_relations(
            [unit("u1", "Random Variables"), unit("u2", "Mean and Variance")],
            [section("s1", "Random Variables", ["u1"]), section("s2", "Mean and Variance", ["u2"])],
        )

        self.assertTrue(any(item.relation_type == "next" and item.source_id == "s1" and item.target_id == "s2" for item in relations))

    def test_builds_domain_specific_relationships(self):
        relations = build_relations(
            [
                unit("u1", "Maximum Likelihood Estimation"),
                unit("u2", "Ridge Regression"),
                unit("u3", "Frequentist v.s. Bayesian"),
            ],
            [
                section("s1", "A Frequentist Viewpoint: Maximum Likelihood Estimation (MLE)", ["u1"]),
                section("s2", "Ridge Regression: MSE with L2 Regularization", ["u2"]),
                section("s3", "Frequentist v.s. Bayesian", ["u3"]),
            ],
        )

        typed = {(item.source_id, item.target_id, item.relation_type) for item in relations}
        self.assertIn(("s1", "s2", "foundation_for"), typed)
        self.assertIn(("s1", "s3", "contrasts_with"), typed)

    def test_builds_parallel_relationships_for_sibling_viewpoints(self):
        relations = build_relations(
            [
                unit("u1", "Bias-Variance Trade-off: An Indicator of Model Misspecification"),
                unit("u2", "Bias-Variance Trade-off: An Indicator of Training Process"),
                unit("u3", "Ridge Regression: MSE with L2 Regularization"),
                unit("u4", "Ridge Regression: A Bayesian Viewpoint"),
            ],
            [
                section("s1", "Bias-Variance Trade-off: An Indicator of Model Misspecification", ["u1"]),
                section("s2", "Bias-Variance Trade-off: An Indicator of Training Process", ["u2"]),
                section("s3", "Ridge Regression: MSE with L2 Regularization", ["u3"]),
                section("s4", "Ridge Regression: A Bayesian Viewpoint", ["u4"]),
            ],
        )

        typed = {(item.source_id, item.target_id, item.relation_type) for item in relations}
        self.assertIn(("s1", "s2", "parallel_with"), typed)
        self.assertIn(("s3", "s4", "parallel_with"), typed)

    def test_builds_relations_from_ai_unit_metadata(self):
        relations = build_relations(
            [
                unit("u1", "Gaussian Noise", learning_stage="foundation"),
                unit("u2", "Maximum Likelihood Estimation", prerequisites=["Gaussian Noise"], confusable_with=["MAP"]),
                unit("u3", "MAP"),
            ],
            [
                section("s1", "Gaussian Noise", ["u1"]),
                section("s2", "Maximum Likelihood Estimation", ["u2"]),
                section("s3", "MAP", ["u3"]),
            ],
        )

        typed = {(item.source_id, item.target_id, item.relation_type) for item in relations}
        self.assertIn(("s1", "s2", "foundation_for"), typed)
        self.assertIn(("s2", "s3", "contrasts_with"), typed)


if __name__ == "__main__":
    unittest.main()
