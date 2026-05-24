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
                if inferred[0] in {"parallel_with", "contrasts_with"} and _has_relation(
                    relations, target.section_id, source.section_id, inferred[0]
                ):
                    continue
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
    source_title_l = source_title.lower()
    target_title_l = target_title.lower()
    if _non_conceptual_title(source_title_l) or _non_conceptual_title(target_title_l):
        return None

    source = f"{source_title} {source_text}".lower()
    target = f"{target_title} {target_text}".lower()

    if "maximum likelihood" in source_title_l and "ridge regression" in target_title_l:
        return ("foundation_for", "先理解 MLE/最小二乘，才能看懂 Ridge 在损失上加入正则项。", 0.78)
    if "bias of estimation" in source_title_l and "variance of estimation" in target_title_l:
        return ("parallel_with", "Bias 和 Variance 是评估估计量误差的两个并列维度，需要放在一起比较。", 0.79)
    if "variance of estimation" in source_title_l and "bias of estimation" in target_title_l:
        return ("parallel_with", "Bias 和 Variance 是评估估计量误差的两个并列维度，需要放在一起比较。", 0.79)
    if "bias-variance trade-off: an indicator" in source_title_l and "bias-variance trade-off: an indicator" in target_title_l:
        return ("parallel_with", "这两个小节分别从模型错设和训练过程解释 Bias-Variance trade-off，适合并列表格总结。", 0.8)
    if "ridge regression: mse" in source_title_l and "bayesian viewpoint" in target_title_l:
        return ("parallel_with", "Ridge Regression 可以从正则化损失和贝叶斯先验两个并列视角理解。", 0.8)
    if "frequentist statistic viewpoint" in source_title_l and "bayesian statistic viewpoint" in target_title_l:
        return ("parallel_with", "频率派和贝叶斯视角是机器学习统计解释的两个并列框架。", 0.82)
    if (
        "frequentist" in source_title_l
        and "bayesian" in target_title_l
        and (
            ("statistic viewpoint" in source_title_l and "statistic viewpoint" in target_title_l)
            or "v.s." in target_title_l
        )
    ):
        return ("contrasts_with", "频率派和贝叶斯视角是同一建模问题的两种解释框架。", 0.82)
    if _is_mean_variance_topic(source_title_l) and (_is_bias_topic(target_title_l) or _is_tradeoff_topic(target_title_l)):
        return ("foundation_for", "偏差与方差分析依赖均值、方差和无偏估计的概念。", 0.76)
    if _is_variance_estimation_topic(source_title_l) and _is_tradeoff_topic(target_title_l):
        return ("foundation_for", "Bias-Variance trade-off 直接使用方差和偏差定义。", 0.8)
    if "overfitting" in source_title_l and "ridge regression" in target_title_l:
        return ("regularizes", "Ridge regression 是缓解过拟合的一种 L2 正则化方法。", 0.82)
    if "random variable" in source_title_l and _is_mean_variance_topic(target_title_l):
        return ("foundation_for", "均值和方差建立在随机变量及其分布的定义之上。", 0.75)
    if "linear regression" in source_title_l and "maximum likelihood" in target_title_l:
        return ("example_of", "线性回归例子用于引出高斯噪声下的最大似然估计。", 0.74)
    return None


def _non_conceptual_title(title: str) -> bool:
    stripped = title.strip().lower()
    if not stripped:
        return True
    if stripped.startswith(("formula near", "algorithm near")):
        return True
    if stripped.startswith(("▶", "•", "-")):
        return True
    if stripped in {"in summary", "next...", "next"}:
        return True
    if "homework" in stripped or "ddl" in stripped:
        return True
    if len(stripped) <= 3:
        return True
    return False


def _is_mean_variance_topic(title: str) -> bool:
    return (
        title.startswith("mean,")
        or title.startswith("properties of mean and variance")
        or title.startswith("properties of mean")
    )


def _is_variance_estimation_topic(title: str) -> bool:
    return title.startswith("the variance of estimation")


def _is_bias_topic(title: str) -> bool:
    return title.startswith("the bias of estimation") or title.startswith("bias-variance")


def _is_tradeoff_topic(title: str) -> bool:
    return "bias-variance trade-off" in title or "trade-off between bias and variance" in title


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
