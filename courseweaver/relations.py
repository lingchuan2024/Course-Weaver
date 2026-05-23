from __future__ import annotations

from courseweaver.models import KnowledgeUnit, NotePlanSection, Relation


def build_relations(units: list[KnowledgeUnit], plan: list[NotePlanSection]) -> list[Relation]:
    relations: list[Relation] = []
    unit_by_id = {unit.unit_id: unit for unit in units}

    for left, right in zip(plan, plan[1:]):
        relations.append(
            _relation(
                len(relations) + 1,
                left,
                right,
                "next",
                "学习路径中的下一节。",
                _evidence_units(left, right),
                confidence=0.85,
            )
        )

    title_index = {section.section_title.lower(): section for section in plan}
    sections = list(plan)
    for source in sections:
        source_text = _section_text(source, unit_by_id)
        for target in sections:
            if source.section_id == target.section_id:
                continue
            target_text = _section_text(target, unit_by_id)
            inferred = _infer_relation(source.section_title, target.section_title, source_text, target_text)
            if inferred and not _has_relation(relations, source.section_id, target.section_id, inferred[0]):
                relations.append(
                    _relation(
                        len(relations) + 1,
                        source,
                        target,
                        inferred[0],
                        inferred[1],
                        _evidence_units(source, target),
                        confidence=inferred[2],
                    )
                )

    return relations


def _infer_relation(source_title: str, target_title: str, source_text: str, target_text: str):
    source = f"{source_title} {source_text}".lower()
    target = f"{target_title} {target_text}".lower()

    if "maximum likelihood" in source and "ridge regression" in target:
        return ("foundation_for", "先理解 MLE/最小二乘，才能看懂 Ridge 在损失上加入正则项。", 0.78)
    if "frequentist" in source and "bayesian" in target:
        return ("contrasts_with", "频率派和贝叶斯视角是同一建模问题的两种解释框架。", 0.82)
    if "mean" in source and "bias" in target:
        return ("foundation_for", "偏差与方差分析依赖均值、方差和无偏估计的概念。", 0.76)
    if "variance" in source and "trade-off" in target:
        return ("foundation_for", "Bias-Variance trade-off 直接使用方差和偏差定义。", 0.8)
    if "overfitting" in source and "ridge regression" in target:
        return ("regularizes", "Ridge regression 是缓解过拟合的一种 L2 正则化方法。", 0.82)
    if "random variable" in source and ("mean" in target or "variance" in target):
        return ("foundation_for", "均值和方差建立在随机变量及其分布的定义之上。", 0.75)
    if "linear regression" in source and "maximum likelihood" in target:
        return ("example_of", "线性回归例子用于引出高斯噪声下的最大似然估计。", 0.74)
    return None


def _relation(
    index: int,
    source: NotePlanSection,
    target: NotePlanSection,
    relation_type: str,
    reason: str,
    evidence_units: list[str],
    confidence: float,
) -> Relation:
    return Relation(
        relation_id=f"R_{index:04d}",
        source_id=source.section_id,
        target_id=target.section_id,
        relation_type=relation_type,
        source_label=source.section_title,
        target_label=target.section_title,
        reason=reason,
        confidence=confidence,
        evidence_units=evidence_units,
    )


def _evidence_units(left: NotePlanSection, right: NotePlanSection) -> list[str]:
    return list(dict.fromkeys((left.units or []) + (right.units or [])))


def _section_text(section: NotePlanSection, unit_by_id: dict[str, KnowledgeUnit]) -> str:
    chunks = [section.section_title]
    for unit_id in section.units:
        unit = unit_by_id.get(unit_id)
        if unit:
            chunks.extend([unit.name, unit.summary, unit.unit_type])
    return " ".join(chunks)


def _has_relation(relations: list[Relation], source_id: str, target_id: str, relation_type: str) -> bool:
    return any(
        item.source_id == source_id and item.target_id == target_id and item.relation_type == relation_type
        for item in relations
    )
