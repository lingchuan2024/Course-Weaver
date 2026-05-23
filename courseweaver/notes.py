from __future__ import annotations

from courseweaver.models import KnowledgeUnit, NoteChunk, NotePlanSection


def plan_notes(units: list[KnowledgeUnit]) -> list[NotePlanSection]:
    eligible = sorted(
        [unit for unit in units if unit.importance != "minor"],
        key=lambda unit: (min(unit.source_pages or [9999]), unit.unit_id),
    )
    title_units = [unit for unit in eligible if unit.unit_type == "summary" and _meaningful_title(unit)]

    if title_units:
        sections = []
        assigned: set[str] = set()
        for index, title in enumerate(title_units, start=1):
            if title.unit_id in assigned:
                continue
            title_pages = set(title.source_pages)
            section_units = [
                unit
                for unit in eligible
                if unit.unit_id not in assigned and title_pages.intersection(unit.source_pages)
            ]
            if title.unit_id not in {unit.unit_id for unit in section_units}:
                section_units.insert(0, title)
            for unit in section_units:
                assigned.add(unit.unit_id)

            sections.append(
                NotePlanSection(
                    section_id=f"S_{len(sections) + 1:04d}",
                    section_title=title.name,
                    units=[unit.unit_id for unit in section_units],
                    style=_section_style(section_units),
                    goal="按课件标题聚合相关概念、公式和算法线索，生成章节式讲义。",
                    detail_level="high" if any(unit.unit_type in {"formula", "algorithm"} for unit in section_units) else "medium",
                )
            )

        for unit in eligible:
            if unit.unit_id in assigned:
                continue
            if _front_matter_or_outline(unit):
                continue
            sections.append(_single_unit_section(unit, len(sections) + 1))
        return sections

    core_units = [unit for unit in eligible if not _front_matter_or_outline(unit)]
    sections: list[NotePlanSection] = []
    for index, unit in enumerate(core_units, start=1):
        sections.append(_single_unit_section(unit, index))
    return sections


def generate_note_chunks(units: list[KnowledgeUnit], plan: list[NotePlanSection]) -> list[NoteChunk]:
    unit_by_id = {unit.unit_id: unit for unit in units}
    chunks: list[NoteChunk] = []

    for index, section in enumerate(plan, start=1):
        section_units = [unit_by_id[unit_id] for unit_id in section.units if unit_id in unit_by_id]
        if not section_units:
            continue
        source_blocks = [block_id for unit in section_units for block_id in unit.source_blocks]
        content = _render_section(section, section_units)
        chunks.append(
            NoteChunk(
                chunk_id=f"N_{index:04d}",
                note_file="01_lecture_notes.md",
                section_title=section.section_title,
                content=content,
                source_units=[unit.unit_id for unit in section_units],
                source_blocks=list(dict.fromkeys(source_blocks)),
            )
        )
    return chunks


def refine_note_chunks_with_llm(chunks: list[NoteChunk], units: list[KnowledgeUnit], client) -> list[NoteChunk]:
    unit_by_id = {unit.unit_id: unit for unit in units}
    refined: list[NoteChunk] = []

    for chunk in chunks:
        chunk_units = [unit_by_id[unit_id] for unit_id in chunk.source_units if unit_id in unit_by_id]
        messages = _rewrite_messages(chunk, chunk_units)
        content = client.chat(messages, max_tokens=2600, temperature=0.45)
        refined.append(chunk.model_copy(update={"content": content or chunk.content}))
    return refined


def _render_section(section: NotePlanSection, units: list[KnowledgeUnit]) -> str:
    unit = units[0]
    pages = _page_range([page for item in units for page in item.source_pages])
    header = f"## {section.section_title} [{pages}]"

    if len(units) > 1:
        concepts = [item for item in units if item.unit_type not in {"summary", "formula", "algorithm"}]
        formulas = [item for item in units if item.unit_type == "formula"]
        algorithms = [item for item in units if item.unit_type == "algorithm"]
        lines = [
            f"这一部分的主线是围绕“{section.section_title}”展开。课件在 {pages} 中把相关概念、公式和过程分散呈现，"
            "这里将它们合并成一段可以连续阅读的讲义。",
            "",
        ]
        if concepts:
            lines.extend(["核心线索：", ""])
            for item in concepts[:6]:
                lines.append(f"- {item.summary}")
            lines.append("")
        if formulas:
            lines.extend(["需要重点理解的公式或数学表达：", ""])
            for item in formulas[:5]:
                lines.append(f"- `{item.summary.replace('公式内容：', '')}`")
            lines.append("")
            lines.append(
                "读这些公式时，先确认等号左边的目标量，再逐项解释右边的变量、参数、概率假设或优化目标。"
            )
            lines.append("")
        if algorithms:
            lines.extend(["涉及的算法或过程：", ""])
            for item in algorithms[:3]:
                lines.append(f"- {item.summary.replace('算法或过程内容：', '')}")
            lines.append("")
        lines.append("复习提醒：把这一节当作一个完整知识点检查，至少确认它解决什么问题、依赖什么假设、最后导向哪个公式或结论。")
        lines.append("")
        lines.append(f"来源：{pages}")
        return f"{header}\n\n" + "\n".join(lines) + "\n"

    if section.style == "formula_explanation":
        body = (
            f"这一部分的关键是理解公式背后的建模含义，而不是只记住符号。课件给出的核心内容是："
            f"`{unit.summary.replace('公式内容：', '')}`。\n\n"
            "阅读这类公式时，可以先看等号左边表示要计算的目标，再看等号右边如何由已知量、参数或约束组合而来。"
            "如果公式中出现矩阵、概率或求和符号，复习时应逐一确认每个符号对应的数据、参数和优化目标。"
        )
    elif section.style == "algorithm_walkthrough":
        body = (
            "这段内容更适合作为过程来理解：先明确输入和目标，再看每一步如何推进到结果。"
            f"课件中的算法线索是：{unit.summary.replace('算法或过程内容：', '')}\n\n"
            "复习时不要只背伪代码顺序，要问三个问题：它维护了什么状态，循环或迭代什么时候停止，"
            "以及每一步为什么会让目标更接近最终答案。"
        )
    else:
        body = (
            f"这一节要解决的问题是：为什么需要引入“{unit.name}”这个知识点。\n\n"
            f"课件中的核心信息可以概括为：{unit.summary}\n\n"
            "从学习角度看，建议先把它放回课程主线中理解：它通常承担引出概念、连接前后内容或解释模型行为的作用。"
            "如果后续出现公式、算法或实验现象，这个知识点往往就是理解它们的前提。"
        )
    return f"{header}\n\n{body}\n\n来源：{pages}\n"


def _rewrite_messages(chunk: NoteChunk, units: list[KnowledgeUnit]) -> list[dict[str, str]]:
    unit_lines = []
    for unit in units:
        unit_lines.append(
            "\n".join(
                [
                    f"- id: {unit.unit_id}",
                    f"  name: {unit.name}",
                    f"  type: {unit.unit_type}",
                    f"  pages: {', '.join('p.' + str(page) for page in unit.source_pages)}",
                    f"  evidence: {unit.summary}",
                ]
            )
        )
    source_pages = _page_range([page for unit in units for page in unit.source_pages])
    user_prompt = f"""请把下面的课件知识单元整理成一段真正适合复习的中文课堂笔记。

写作目标：
- 让读者能顺着老师上课的逻辑读下去，而不是看到模板化总结。
- 优先保留这页课件的推导顺序、概念之间的因果关系和容易混淆的点。
- 如果这一节主要是公式推导，就按“符号含义 -> 推导为什么成立 -> 结论怎么用”组织。
- 如果这一节主要是概念解释，就按“这个概念解决什么问题 -> 和前后知识的关系 -> 如何判断自己理解了”组织。
- 如果证据很少，不要硬凑小标题；用一两段清楚说明即可。

硬性约束：
1. 第一行必须是：## {chunk.section_title} [{source_pages}]
2. 不要编造课件没有给出的结论、例子或算法步骤。
3. 不要每一节都使用同样的小标题；只在确实有帮助时使用三级标题。
4. 公式必须解释每个关键符号的角色，尤其是目标量、参数、样本、分布假设和优化目标。
5. 用自然中文写，避免“课件这里主要给出”反复出现；只有证据不足时才保守说明。
6. 末尾必须保留：来源：{source_pages}
7. 只输出 Markdown 正文，不要输出 JSON，不要输出“以下是”。

知识单元：
{chr(10).join(unit_lines)}

当前草稿：
{chunk.content}
"""
    return [
        {
            "role": "system",
            "content": (
                "你是会讲课的课程助教，任务是把课件证据整理成可阅读、可复习、可追溯的课堂笔记。"
                "你的写作应当像认真听课后整理出来的笔记：有主线、有解释、有取舍，但不脱离证据。"
            ),
        },
        {"role": "user", "content": user_prompt},
    ]


def _single_unit_section(unit: KnowledgeUnit, index: int) -> NotePlanSection:
    style = "narrative"
    goal = "解释该知识点的作用、直觉和来源。"
    detail_level = "medium"
    if unit.unit_type == "formula":
        style = "formula_explanation"
        goal = "解释公式含义、符号直觉和使用场景。"
        detail_level = "high"
    elif unit.unit_type == "algorithm":
        style = "algorithm_walkthrough"
        goal = "说明算法目标、执行流程和关键步骤。"
        detail_level = "high"

    return NotePlanSection(
        section_id=f"S_{index:04d}",
        section_title=unit.name,
        units=[unit.unit_id],
        style=style,
        goal=goal,
        detail_level=detail_level,
    )


def _section_style(units: list[KnowledgeUnit]) -> str:
    if any(unit.unit_type == "algorithm" for unit in units):
        return "algorithm_walkthrough"
    if any(unit.unit_type == "formula" for unit in units):
        return "formula_explanation"
    return "narrative"


def _meaningful_title(unit: KnowledgeUnit) -> bool:
    name = unit.name.strip().lower()
    if unit.source_pages == [1]:
        return False
    if name in {"outline", "references", "thanks"}:
        return False
    if len(name) <= 2:
        return False
    return True


def _front_matter_or_outline(unit: KnowledgeUnit) -> bool:
    name = unit.name.strip().lower()
    if unit.unit_type == "summary" and unit.source_pages == [1]:
        return True
    if name == "outline" or name.startswith("algorithm near outline"):
        return True
    return False


def _page_range(pages: list[int]) -> str:
    unique = sorted(set(pages))
    if not unique:
        return "p.?"
    if len(unique) == 1:
        return f"p.{unique[0]}"
    if unique == list(range(unique[0], unique[-1] + 1)):
        return f"p.{unique[0]}-p.{unique[-1]}"
    return ", ".join(f"p.{page}" for page in unique)
