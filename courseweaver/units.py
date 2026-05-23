from __future__ import annotations

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
