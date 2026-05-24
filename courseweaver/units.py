from __future__ import annotations

import json
import re
from collections import OrderedDict

from courseweaver.models import Block, KnowledgeUnit


FORMULA_RE = re.compile(r"(\\|=|\^|_|\barg\s*max\b|\barg\s*min\b|\bsum\b|\bprod\b|∑|∏|≤|≥|θ|λ|σ|μ)")
NOISE_RE = re.compile(
    r"^\s*(\d+\s*/\s*\d+|\d+|\(\d+\)|[A-Za-z]|[.\-–—_ ]{1,8}|[⇒→←↔#\"'`]+)\s*$"
)
ALGORITHM_RE = re.compile(
    r"\b(algorithm|pseudo|input|output|initialize|repeat|until|for each|while|gradient descent|sgd|return)\b",
    re.IGNORECASE,
)
WARNING_RE = re.compile(r"\b(warning|note|remark|pitfall|underfitting|overfitting|bias|variance)\b", re.IGNORECASE)
DEFINITION_RE = re.compile(r"\b(is defined as|definition|denote|called|refers to)\b", re.IGNORECASE)
EXAMPLE_RE = re.compile(r"\b(example|for instance|e\.g\.|case study)\b", re.IGNORECASE)
ALLOWED_UNIT_TYPES = {
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
}
ALLOWED_IMPORTANCE = {"core", "supporting", "minor"}
ALLOWED_TEACHING_ROLES = {
    "core_concept",
    "definition",
    "derivation",
    "formula_detail",
    "example",
    "comparison",
    "application",
    "summary",
    "exercise",
    "supporting_detail",
}
ALLOWED_LEARNING_STAGES = {
    "orientation",
    "foundation",
    "modeling",
    "estimation",
    "analysis",
    "diagnosis",
    "regularization",
    "statistical_view",
    "review",
    "exercise",
}


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def classify_block(text: str) -> str:
    clean = normalize_text(text)
    if not clean or NOISE_RE.match(clean):
        return "noise"
    if clean.startswith(("▶", "•", "- ")):
        return "text"
    if ALGORITHM_RE.search(clean):
        return "code_or_algorithm"
    if FORMULA_RE.search(clean) and len(clean) <= 180:
        return "formula"
    if len(clean) <= 80 and _looks_like_title(clean):
        return "title"
    return "text"


def extract_units(blocks: list[Block]) -> list[KnowledgeUnit]:
    units: list[KnowledgeUnit] = []
    last_title = ""

    for block in blocks:
        text = normalize_text(block.text)
        block_type = block.block_type if block.block_type != "unknown" else classify_block(text)
        if block_type == "noise":
            continue
        if block_type == "title":
            last_title = text

        unit_type = _unit_type_for(block_type, text)
        name = _unit_name(block_type, text, last_title)
        summary = _summary_for(unit_type, text)
        importance = _importance_for(unit_type, text)

        units.append(
            KnowledgeUnit(
                unit_id=f"U_{len(units) + 1:04d}",
                name=name,
                unit_type=unit_type,
                summary=summary,
                source_pages=[block.page_number],
                source_blocks=[block.block_id],
                importance=importance,
                confidence=0.78 if unit_type in {"formula", "algorithm"} else 0.7,
                teaching_role=_teaching_role_for(unit_type, text),
                learning_stage=_learning_stage_for(text, unit_type),
                parent_topic=last_title if block_type != "title" else "",
            )
        )

    return units


def extract_units_with_llm(blocks: list[Block], client, max_blocks_per_batch: int = 80) -> list[KnowledgeUnit]:
    heuristic_units = extract_units(blocks)
    semantic_units: list[KnowledgeUnit] = []
    block_by_id = {block.block_id: block for block in blocks}

    for batch in _block_batches(blocks, max_blocks_per_batch):
        messages = _extract_messages(batch)
        try:
            content = client.chat(messages, max_tokens=4000, temperature=0.1)
            semantic_units.extend(_units_from_llm_response(content, block_by_id))
        except Exception:
            continue

    if not semantic_units:
        return heuristic_units
    return _merge_ai_and_heuristic_units(semantic_units, heuristic_units)


def merge_units(units: list[KnowledgeUnit]) -> list[KnowledgeUnit]:
    grouped: "OrderedDict[tuple[str, str], KnowledgeUnit]" = OrderedDict()

    for unit in units:
        key = (_normal_name(unit.name), unit.unit_type)
        if key not in grouped:
            grouped[key] = unit.model_copy(deep=True)
            continue

        current = grouped[key]
        current.summary = _merge_summary(current.summary, unit.summary)
        current.source_pages = sorted(set(current.source_pages + unit.source_pages))
        current.source_blocks = _ordered_unique(current.source_blocks + unit.source_blocks)
        current.importance = "core" if "core" in {current.importance, unit.importance} else current.importance
        current.confidence = round((current.confidence + unit.confidence) / 2, 2)
        if not current.parent_topic and unit.parent_topic:
            current.parent_topic = unit.parent_topic
        current.prerequisites = _ordered_unique(current.prerequisites + unit.prerequisites)
        current.confusable_with = _ordered_unique(current.confusable_with + unit.confusable_with)
        if not current.merge_reason and unit.merge_reason:
            current.merge_reason = unit.merge_reason
        current.teaching_role = _stronger_role(current.teaching_role, unit.teaching_role)
        current.learning_stage = _earlier_stage(current.learning_stage, unit.learning_stage)

    merged = list(grouped.values())
    for index, unit in enumerate(merged, start=1):
        unit.unit_id = f"U_{index:04d}"
    return merged


def _block_batches(blocks: list[Block], max_blocks_per_batch: int) -> list[list[Block]]:
    valid_blocks = []
    for block in blocks:
        text = normalize_text(block.text)
        block_type = block.block_type if block.block_type != "unknown" else classify_block(text)
        if block_type == "noise":
            continue
        valid_blocks.append(block)

    batches: list[list[Block]] = []
    current: list[Block] = []
    for block in valid_blocks:
        if len(current) >= max_blocks_per_batch:
            batches.append(current)
            current = []
        current.append(block)
    if current:
        batches.append(current)
    return batches


def _extract_messages(blocks: list[Block]) -> list[dict[str, str]]:
    block_lines = []
    for block in blocks:
        text = _shorten(normalize_text(block.text), 600)
        block_type = block.block_type if block.block_type != "unknown" else classify_block(text)
        block_lines.append(
            f"- block_id: {block.block_id}\n"
            f"  page: p.{block.page_number}\n"
            f"  type_hint: {block_type}\n"
            f"  text: {text}"
        )

    return [
        {
            "role": "system",
            "content": (
                "你是 CourseWeaver 的知识点抽取器。你的任务不是写笔记，而是把课件 block "
                "合并成少量有教学意义的知识单元。必须保留来源 block id，不能编造来源。"
            ),
        },
        {
            "role": "user",
            "content": (
                "请从下面的课件 blocks 中抽取结构化知识单元。\n\n"
                "判断标准：\n"
                "1. 一个知识单元应该对应学生需要理解或复习的概念、定义、公式、例子、对比、作业或总结。\n"
                "2. 动画重复页、同一推导的零散公式、同一主题的 bullet 应合并到同一个知识单元。\n"
                "3. 不要把孤立页码、装饰符、单个变量或公式碎片单独作为知识点；它们应作为来源 block 并入附近主题。\n"
                "4. source_blocks 只能使用输入中出现过的 block_id。\n"
                "5. summary 要说明该知识点在学习中的作用，不要照抄原文。\n\n"
                "还要判断教学结构：\n"
                "- teaching_role 表示这个知识点在讲义中的角色。\n"
                "- learning_stage 表示它更适合出现在学习路径的哪个阶段。\n"
                "- parent_topic 表示上级主题，用于把知识点组织成树。\n"
                "- prerequisites 是学习它之前最好先理解的知识点名称。\n"
                "- confusable_with 是适合做对比表的易混淆或并列知识点名称。\n\n"
                "只输出 JSON，不要 Markdown。格式如下：\n"
                "{\n"
                '  "units": [\n'
                "    {\n"
                '      "name": "知识点名称",\n'
                '      "unit_type": "concept|definition|formula|algorithm|theorem|proof|example|figure|table|comparison|warning|exercise|summary",\n'
                '      "teaching_role": "core_concept|definition|derivation|formula_detail|example|comparison|application|summary|exercise|supporting_detail",\n'
                '      "learning_stage": "orientation|foundation|modeling|estimation|analysis|diagnosis|regularization|statistical_view|review|exercise",\n'
                '      "parent_topic": "上级主题名称，若没有则为空字符串",\n'
                '      "summary": "面向学生的简洁解释",\n'
                '      "why_it_matters": "为什么学生需要学这个点",\n'
                '      "prerequisites": ["前置知识点名称"],\n'
                '      "confusable_with": ["易混淆或应并列比较的知识点名称"],\n'
                '      "source_blocks": ["p001_b001"],\n'
                '      "merge_reason": "为什么这些 blocks 应合并成这个知识点",\n'
                '      "importance": "core|supporting|minor",\n'
                '      "confidence": 0.0\n'
                "    }\n"
                "  ]\n"
                "}\n\n"
                "课件 blocks：\n"
                f"{chr(10).join(block_lines)}"
            ),
        },
    ]


def _units_from_llm_response(content: str, block_by_id: dict[str, Block]) -> list[KnowledgeUnit]:
    payload = _parse_json_payload(content)
    raw_units = payload if isinstance(payload, list) else payload.get("units", [])
    if not isinstance(raw_units, list):
        return []

    units: list[KnowledgeUnit] = []
    for raw in raw_units:
        if not isinstance(raw, dict):
            continue
        name = normalize_text(str(raw.get("name", "")))
        summary = normalize_text(str(raw.get("summary", "")))
        source_blocks = _valid_source_blocks(raw.get("source_blocks", []), block_by_id)
        if not name or not summary or not source_blocks:
            continue

        unit_type = str(raw.get("unit_type", "concept")).strip()
        if unit_type not in ALLOWED_UNIT_TYPES:
            unit_type = "concept"

        importance = str(raw.get("importance", "supporting")).strip()
        if importance not in ALLOWED_IMPORTANCE:
            importance = "supporting"
        teaching_role = str(raw.get("teaching_role", "")).strip()
        if teaching_role not in ALLOWED_TEACHING_ROLES:
            teaching_role = _role_from_type(unit_type)
        learning_stage = str(raw.get("learning_stage", "")).strip()
        if learning_stage not in ALLOWED_LEARNING_STAGES:
            learning_stage = _learning_stage_for(f"{name} {summary}", unit_type)

        pages = sorted({block_by_id[block_id].page_number for block_id in source_blocks})
        why_it_matters = normalize_text(str(raw.get("why_it_matters", "")))
        if why_it_matters and why_it_matters not in summary:
            summary = f"{summary} 学习作用：{why_it_matters}"
        units.append(
            KnowledgeUnit(
                unit_id=f"AI_{len(units) + 1:04d}",
                name=_shorten(name, 120),
                unit_type=unit_type,
                summary=_shorten(summary, 700),
                source_pages=pages,
                source_blocks=source_blocks,
                importance=importance,
                confidence=_confidence(raw.get("confidence", 0.82)),
                teaching_role=teaching_role,
                learning_stage=learning_stage,
                parent_topic=_shorten(normalize_text(str(raw.get("parent_topic", ""))), 120),
                prerequisites=_string_list(raw.get("prerequisites", [])),
                confusable_with=_string_list(raw.get("confusable_with", [])),
                merge_reason=_shorten(normalize_text(str(raw.get("merge_reason", ""))), 300),
            )
        )
    return units


def _parse_json_payload(content: str):
    clean = content.strip()
    if clean.startswith("```"):
        clean = re.sub(r"^```(?:json)?\s*", "", clean)
        clean = re.sub(r"\s*```$", "", clean)
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        start = clean.find("{")
        end = clean.rfind("}")
        if start >= 0 and end > start:
            return json.loads(clean[start : end + 1])
        raise


def _valid_source_blocks(value, block_by_id: dict[str, Block]) -> list[str]:
    if not isinstance(value, list):
        return []
    result = []
    for item in value:
        block_id = str(item).strip()
        if block_id in block_by_id and block_id not in result:
            result.append(block_id)
    return result


def _confidence(value) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = 0.82
    return round(max(0.0, min(1.0, number)), 2)


def _string_list(value) -> list[str]:
    if not isinstance(value, list):
        return []
    result = []
    for item in value:
        text = _shorten(normalize_text(str(item)), 120)
        if text and text not in result:
            result.append(text)
    return result


def _merge_ai_and_heuristic_units(
    semantic_units: list[KnowledgeUnit], heuristic_units: list[KnowledgeUnit]
) -> list[KnowledgeUnit]:
    covered_blocks = {block_id for unit in semantic_units for block_id in unit.source_blocks}
    additions = []
    for unit in heuristic_units:
        if unit.importance == "minor" and unit.unit_type not in {"formula", "algorithm", "exercise"}:
            continue
        if all(block_id in covered_blocks for block_id in unit.source_blocks):
            continue
        additions.append(unit)
    return semantic_units + additions


def _looks_like_title(text: str) -> bool:
    words = text.split()
    if len(words) > 10:
        return False
    if text.endswith("."):
        return False
    titleish_words = sum(1 for word in words if word[:1].isupper() or word.isupper())
    return titleish_words >= max(1, len(words) // 2)


def _unit_type_for(block_type: str, text: str) -> str:
    if block_type == "title":
        return "summary"
    if block_type == "formula":
        return "formula"
    if block_type == "code_or_algorithm":
        return "algorithm"
    if WARNING_RE.search(text):
        return "warning"
    if DEFINITION_RE.search(text):
        return "definition"
    if EXAMPLE_RE.search(text):
        return "example"
    return "concept"


def _unit_name(block_type: str, text: str, last_title: str) -> str:
    if block_type == "formula":
        return f"Formula near {last_title}" if last_title else _shorten(text, 48)
    if block_type == "code_or_algorithm":
        return f"Algorithm near {last_title}" if last_title else _shorten(text, 48)
    if block_type == "title":
        return _shorten(text, 80)

    sentence = re.split(r"(?<=[.!?])\s+", text)[0]
    if ":" in sentence:
        sentence = sentence.split(":", 1)[0]
    if len(sentence.split()) <= 8:
        return _shorten(sentence, 80)
    return _shorten(last_title or sentence, 80)


def _summary_for(unit_type: str, text: str) -> str:
    clean = normalize_text(text)
    if unit_type == "formula":
        return f"公式内容：{clean}"
    if unit_type == "algorithm":
        return f"算法或过程内容：{clean}"
    return _shorten(clean, 420)


def _importance_for(unit_type: str, text: str) -> str:
    lowered = text.lower()
    if unit_type in {"formula", "algorithm", "definition"}:
        return "core"
    if any(word in lowered for word in ["main", "key", "important", "objective", "likelihood", "regression"]):
        return "core"
    if len(text) < 25:
        return "minor"
    return "supporting"


def _teaching_role_for(unit_type: str, text: str) -> str:
    lowered = text.lower()
    if unit_type == "summary":
        return "summary"
    if unit_type == "definition":
        return "definition"
    if unit_type == "formula":
        if any(word in lowered for word in ["derive", "proof", "⇒", "arg", "min", "max"]):
            return "derivation"
        return "formula_detail"
    if unit_type == "example":
        return "example"
    if unit_type == "exercise":
        return "exercise"
    if any(word in lowered for word in ["v.s", " vs", "trade-off", "contrast"]):
        return "comparison"
    if any(word in lowered for word in ["ridge", "regularization", "overfitting", "underfitting"]):
        return "application"
    if _importance_for(unit_type, text) == "core":
        return "core_concept"
    return "supporting_detail"


def _role_from_type(unit_type: str) -> str:
    return {
        "definition": "definition",
        "formula": "formula_detail",
        "algorithm": "application",
        "example": "example",
        "comparison": "comparison",
        "exercise": "exercise",
        "summary": "summary",
    }.get(unit_type, "core_concept" if unit_type == "concept" else "supporting_detail")


def _learning_stage_for(text: str, unit_type: str) -> str:
    lowered = text.lower()
    if "homework" in lowered or unit_type == "exercise":
        return "exercise"
    if "summary" in lowered or "next" in lowered:
        return "review"
    if "random variable" in lowered or "mean" in lowered or "variance" in lowered and "trade" not in lowered:
        return "foundation"
    if "linear regression" in lowered or "statistical modeling" in lowered:
        return "modeling"
    if "likelihood" in lowered or "mle" in lowered or "map" in lowered or "estimation" in lowered:
        return "estimation"
    if "bias-variance" in lowered or "trade-off" in lowered:
        return "analysis"
    if "overfitting" in lowered or "underfitting" in lowered or "misspecification" in lowered:
        return "diagnosis"
    if "ridge" in lowered or "regularization" in lowered:
        return "regularization"
    if "frequentist" in lowered or "bayesian" in lowered:
        return "statistical_view"
    if unit_type == "summary":
        return "orientation"
    return "foundation"


def _stronger_role(left: str, right: str) -> str:
    rank = {
        "core_concept": 0,
        "definition": 1,
        "derivation": 2,
        "formula_detail": 3,
        "comparison": 4,
        "application": 5,
        "example": 6,
        "summary": 7,
        "exercise": 8,
        "supporting_detail": 9,
    }
    return left if rank.get(left, 99) <= rank.get(right, 99) else right


def _earlier_stage(left: str, right: str) -> str:
    order = {
        "orientation": 0,
        "foundation": 1,
        "modeling": 2,
        "estimation": 3,
        "analysis": 4,
        "diagnosis": 5,
        "regularization": 6,
        "statistical_view": 7,
        "review": 8,
        "exercise": 9,
    }
    return left if order.get(left, 99) <= order.get(right, 99) else right


def _shorten(text: str, limit: int) -> str:
    clean = normalize_text(text)
    if len(clean) <= limit:
        return clean
    return clean[: limit - 1].rstrip() + "..."


def _normal_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", name.lower()).strip()


def _merge_summary(left: str, right: str) -> str:
    if right in left:
        return left
    if left in right:
        return right
    return f"{left} {right}"


def _ordered_unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))
