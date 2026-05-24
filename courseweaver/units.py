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
                "只输出 JSON，不要 Markdown。格式如下：\n"
                "{\n"
                '  "units": [\n'
                "    {\n"
                '      "name": "知识点名称",\n'
                '      "unit_type": "concept|definition|formula|algorithm|theorem|proof|example|figure|table|comparison|warning|exercise|summary",\n'
                '      "summary": "面向学生的简洁解释",\n'
                '      "source_blocks": ["p001_b001"],\n'
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

        pages = sorted({block_by_id[block_id].page_number for block_id in source_blocks})
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
